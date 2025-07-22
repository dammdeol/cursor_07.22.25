import threading
import time
from datetime import datetime, timedelta
from models import ScrapingLog, db
from scraper_simple import run_scraper
import logging

logger = logging.getLogger(__name__)

class ScrapingScheduler:
    def __init__(self, app):
        self.app = app
        self.timer_thread = None
        self.is_running = False
        self.interval_minutes = 60  # Default: 1 hour
        self.next_run = None
        self.auto_scraping_enabled = False
        
    def start_timer(self, interval_minutes=60):
        """Start the automatic scraping timer"""
        if self.is_running:
            self.stop_timer()
            
        self.interval_minutes = interval_minutes
        self.auto_scraping_enabled = True
        self.next_run = datetime.now() + timedelta(minutes=interval_minutes)
        self.is_running = True
        
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
        logger.info(f"Scraping timer started. Will run every {interval_minutes} minutes.")
        return True
        
    def stop_timer(self):
        """Stop the automatic scraping timer"""
        self.is_running = False
        self.auto_scraping_enabled = False
        self.next_run = None
        
        if self.timer_thread:
            self.timer_thread.join(timeout=1)
            
        logger.info("Scraping timer stopped.")
        return True
        
    def _timer_loop(self):
        """Internal timer loop"""
        while self.is_running:
            time.sleep(60)  # Check every minute
            
            if not self.auto_scraping_enabled:
                break
                
            if datetime.now() >= self.next_run:
                try:
                    logger.info("Automatic scraping triggered by timer")
                    with self.app.app_context():
                        # Check if another scraping is already running
                        running_log = ScrapingLog.query.filter_by(status='running').first()
                        if running_log:
                            logger.info("Skipping automatic scraping - another scraping is already running")
                            self.next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
                            continue
                            
                        # Run the scraper
                        result = run_scraper(self.app)
                        logger.info(f"Automatic scraping completed. Processed {result} products.")
                        
                except Exception as e:
                    logger.error(f"Automatic scraping failed: {e}")
                    
                # Schedule next run
                self.next_run = datetime.now() + timedelta(minutes=self.interval_minutes)
                
    def get_status(self):
        """Get current timer status"""
        return {
            'is_running': self.is_running,
            'auto_scraping_enabled': self.auto_scraping_enabled,
            'interval_minutes': self.interval_minutes,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'time_until_next': self._get_time_until_next()
        }
        
    def _get_time_until_next(self):
        """Get time remaining until next scraping"""
        if not self.next_run:
            return None
            
        time_diff = self.next_run - datetime.now()
        if time_diff.total_seconds() <= 0:
            return "Due now"
            
        hours, remainder = divmod(int(time_diff.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"

# Global scheduler instance
scheduler = None

def get_scheduler(app):
    """Get or create scheduler instance"""
    global scheduler
    if scheduler is None:
        scheduler = ScrapingScheduler(app)
    return scheduler
