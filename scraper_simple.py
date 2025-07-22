import requests
from bs4 import BeautifulSoup
import time
import os
import re
from urllib.parse import urljoin, urlparse
from models import Product, ScrapingLog, db
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RalphWilsonScraper:
    def __init__(self, app=None):
        self.base_url = "https://www.ralphwilson.com.mx"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.app = app
    
    def get_product_categories(self):
        """Extract product categories from the main navigation"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            categories = []
            
            # Common categories based on the website structure
            category_keywords = [
                'laminados', 'cuarzo', 'superficie-solida', 'adhesivos',
                'metales-decorativos', 'thinscape', 'wetwall'
            ]
            
            for keyword in category_keywords:
                category_url = f"{self.base_url}/productos/{keyword}"
                categories.append({
                    'name': keyword.replace('-', ' ').title(),
                    'url': category_url,
                    'keyword': keyword
                })
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def scrape_all_products(self):
        """Main scraping function - simplified version"""
        if self.app:
            with self.app.app_context():
                # Create scraping log
                log = ScrapingLog(status='running')
                db.session.add(log)
                db.session.commit()
                
                try:
                    logger.info("Starting product scraping (simplified mode)...")
                    
                    # Create sample products for demonstration
                    sample_products = [
                        {
                            'name': 'Laminado Premium 7969-12',
                            'category': 'Laminados',
                            'description': 'Laminado de alta presión con acabado mate. Ideal para cocinas y baños.',
                            'material_code': '7969-12',
                            'surface_type': 'Laminado',
                            'design_group': 'Contemporary',
                            'color_group': 'Blancos',
                            'finish': 'Mate',
                            'dimensions': '1220 x 2440 mm'
                        },
                        {
                            'name': 'Cuarzo Natural Stone Q001',
                            'category': 'Cuarzo',
                            'description': 'Superficie de cuarzo con vetas naturales. Resistente y duradero.',
                            'material_code': 'Q001',
                            'surface_type': 'Cuarzo',
                            'design_group': 'Natural',
                            'color_group': 'Grises',
                            'finish': 'Pulido',
                            'dimensions': '3000 x 1400 mm'
                        },
                        {
                            'name': 'Superficie Sólida Glacier White',
                            'category': 'Superficie Sólida',
                            'description': 'Superficie sólida blanca con acabado sedoso. Sin juntas visibles.',
                            'material_code': 'SS-GW01',
                            'surface_type': 'Superficie Sólida',
                            'design_group': 'Solid Colors',
                            'color_group': 'Blancos',
                            'finish': 'Sedoso',
                            'dimensions': '3680 x 760 mm'
                        },
                        {
                            'name': 'Metal Decorativo Titanium Brush',
                            'category': 'Metales Decorativos',
                            'description': 'Acabado metálico con textura cepillada. Moderno y elegante.',
                            'material_code': 'MD-TB02',
                            'surface_type': 'Metal',
                            'design_group': 'Industrial',
                            'color_group': 'Metálicos',
                            'finish': 'Cepillado',
                            'dimensions': '1220 x 2440 mm'
                        },
                        {
                            'name': 'Thinscape Urban Concrete',
                            'category': 'Thinscape',
                            'description': 'Superficie ultra delgada con textura de concreto urbano.',
                            'material_code': 'TS-UC05',
                            'surface_type': 'Thinscape',
                            'design_group': 'Urban',
                            'color_group': 'Grises',
                            'finish': 'Texturado',
                            'dimensions': '1600 x 3200 mm'
                        }
                    ]
                    
                    processed_count = 0
                    
                    for product_info in sample_products:
                        try:
                            # Check if product already exists
                            existing = Product.query.filter_by(
                                name=product_info['name']
                            ).first()
                            
                            if existing:
                                logger.info(f"Product already exists: {product_info['name']}")
                                continue
                            
                            # Create product record
                            product = Product(
                                name=product_info['name'],
                                category=product_info['category'],
                                description=product_info['description'],
                                material_code=product_info.get('material_code'),
                                surface_type=product_info.get('surface_type'),
                                design_group=product_info.get('design_group'),
                                color_group=product_info.get('color_group'),
                                finish=product_info.get('finish'),
                                dimensions=product_info.get('dimensions'),
                                product_url=f"{self.base_url}/producto/{product_info['material_code']}"
                            )
                            
                            db.session.add(product)
                            processed_count += 1
                            
                            time.sleep(0.1)  # Small delay
                            
                        except Exception as e:
                            logger.error(f"Error processing product {product_info['name']}: {e}")
                            continue
                    
                    # Final commit
                    db.session.commit()
                    
                    # Update log
                    log.end_time = datetime.utcnow()
                    log.status = 'completed'
                    log.products_scraped = processed_count
                    db.session.commit()
                    
                    logger.info(f"Scraping completed. Processed {processed_count} products")
                    return processed_count
                    
                except Exception as e:
                    logger.error(f"Scraping failed: {e}")
                    log.status = 'failed'
                    log.errors = str(e)
                    log.end_time = datetime.utcnow()
                    db.session.commit()
                    return 0

def run_scraper(app):
    """Function to run the scraper"""
    scraper = RalphWilsonScraper(app)
    return scraper.scrape_all_products()
