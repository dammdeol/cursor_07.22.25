import requests
from bs4 import BeautifulSoup
import time
import os
import re
from urllib.parse import urljoin, urlparse
from models import Product, ScrapingLog, db
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

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
        self.driver = None
        
    def setup_driver(self):
        """Setup Selenium WebDriver for JavaScript-heavy pages"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        return self.driver
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
    
    def get_product_categories(self):
        """Extract product categories from the main navigation"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            categories = []
            
            # Look for main product navigation
            nav_items = soup.find_all(['li', 'a'], class_=re.compile(r'nav|menu|product', re.I))
            
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
    
    def scrape_product_page(self, url):
        """Scrape individual product page for detailed information"""
        try:
            if not self.driver:
                self.setup_driver()
                
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_data = {
                'name': '',
                'description': '',
                'image_url': '',
                'design_group': '',
                'color_group': '',
                'finish': '',
                'dimensions': '',
                'material_code': ''
            }
            
            # Extract product name
            name_selectors = [
                'h1.product-title',
                'h1.page-title',
                '.product-name h1',
                'h1',
                '.product-details h1'
            ]
            
            for selector in name_selectors:
                name_elem = soup.select_one(selector)
                if name_elem:
                    product_data['name'] = name_elem.get_text(strip=True)
                    break
            
            # Extract description
            desc_selectors = [
                '.product-description',
                '.product-details .description',
                '.product-info p',
                'meta[name="description"]'
            ]
            
            for selector in desc_selectors:
                if selector.startswith('meta'):
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        product_data['description'] = desc_elem.get('content', '')
                        break
                else:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        product_data['description'] = desc_elem.get_text(strip=True)
                        break
            
            # Extract main product image
            img_selectors = [
                '.product-image img',
                '.product-gallery img',
                '.hero-image img',
                'img[data-role="product-image"]',
                '.main-image img'
            ]
            
            for selector in img_selectors:
                img_elem = soup.select_one(selector)
                if img_elem:
                    img_src = img_elem.get('src') or img_elem.get('data-src')
                    if img_src:
                        product_data['image_url'] = urljoin(url, img_src)
                        break
            
            # Extract product specifications
            spec_containers = soup.find_all(['div', 'section'], class_=re.compile(r'spec|detail|info', re.I))
            
            for container in spec_containers:
                text = container.get_text().lower()
                
                if 'grupo de diseño' in text or 'design group' in text:
                    product_data['design_group'] = self.extract_spec_value(container)
                elif 'grupo de color' in text or 'color group' in text:
                    product_data['color_group'] = self.extract_spec_value(container)
                elif 'acabado' in text or 'finish' in text:
                    product_data['finish'] = self.extract_spec_value(container)
                elif 'dimensión' in text or 'dimension' in text:
                    product_data['dimensions'] = self.extract_spec_value(container)
                elif 'código' in text or 'code' in text:
                    product_data['material_code'] = self.extract_spec_value(container)
            
            return product_data
            
        except Exception as e:
            logger.error(f"Error scraping product page {url}: {e}")
            return None
    
    def extract_spec_value(self, container):
        """Extract specification value from container"""
        try:
            # Look for common patterns
            text = container.get_text()
            
            # Pattern: "Label: Value"
            if ':' in text:
                parts = text.split(':')
                if len(parts) >= 2:
                    return parts[1].strip()
            
            # Pattern: "Label Value" (look for next sibling or child)
            strong_elem = container.find('strong')
            if strong_elem:
                next_text = strong_elem.next_sibling
                if next_text and hasattr(next_text, 'strip'):
                    return next_text.strip()
            
            return text.strip()
            
        except:
            return ""
    
    def search_products(self, category_keyword=""):
        """Search for products using the site's search functionality"""
        try:
            if not self.driver:
                self.setup_driver()
            
            # Try different search URLs
            search_urls = [
                f"{self.base_url}/productos",
                f"{self.base_url}/buscar",
                f"{self.base_url}/catalog",
                f"{self.base_url}/advancedsearch/advanced/filterproductattributes/"
            ]
            
            products = []
            
            for search_url in search_urls:
                try:
                    self.driver.get(search_url)
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                    
                    # Look for product links
                    product_links = soup.find_all('a', href=re.compile(r'/producto|/product|/laminado|/cuarzo', re.I))
                    
                    for link in product_links:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            
                            # Extract basic info from link
                            name = link.get_text(strip=True)
                            if not name:
                                img = link.find('img')
                                if img:
                                    name = img.get('alt', '')
                            
                            if name and len(name) > 3:  # Filter out very short names
                                products.append({
                                    'name': name,
                                    'url': full_url,
                                    'category': category_keyword or 'General'
                                })
                    
                    if products:  # If we found products, break
                        break
                        
                except Exception as e:
                    logger.warning(f"Failed to search at {search_url}: {e}")
                    continue
            
            return products
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def scrape_all_products(self):
        """Main scraping function"""
        if self.app:
            with self.app.app_context():
                # Create scraping log
                log = ScrapingLog(status='running')
                db.session.add(log)
                db.session.commit()
                
                try:
                    logger.info("Starting product scraping...")
                    
                    # Get categories
                    categories = self.get_product_categories()
                    logger.info(f"Found {len(categories)} categories")
                    
                    all_products = []
                    
                    # Search for products in each category
                    for category in categories:
                        logger.info(f"Scraping category: {category['name']}")
                        products = self.search_products(category['keyword'])
                        
                        for product in products:
                            product['category'] = category['name']
                            all_products.append(product)
                        
                        time.sleep(2)  # Be respectful to the server
                    
                    # If no categories found, do a general search
                    if not all_products:
                        logger.info("No categories found, doing general search...")
                        general_products = self.search_products()
                        all_products.extend(general_products)
                    
                    logger.info(f"Found {len(all_products)} products to process")
                    
                    # Process each product
                    processed_count = 0
                    
                    for product_info in all_products:
                        try:
                            # Check if product already exists
                            existing = Product.query.filter_by(
                                name=product_info['name']
                            ).first()
                            
                            if existing:
                                logger.info(f"Product already exists: {product_info['name']}")
                                continue
                            
                            # Scrape detailed product information
                            detailed_data = self.scrape_product_page(product_info['url'])
                            
                            if detailed_data:
                                # Download and save image
                                local_image_path = None
                                if detailed_data.get('image_url'):
                                    local_image_path = self.download_image(
                                        detailed_data['image_url'],
                                        product_info['name']
                                    )
                                
                                # Create product record
                                product = Product(
                                    name=detailed_data['name'] or product_info['name'],
                                    category=product_info['category'],
                                    description=detailed_data['description'],
                                    image_url=detailed_data['image_url'],
                                    local_image_path=local_image_path,
                                    product_url=product_info['url'],
                                    design_group=detailed_data['design_group'],
                                    color_group=detailed_data['color_group'],
                                    finish=detailed_data['finish'],
                                    dimensions=detailed_data['dimensions'],
                                    material_code=detailed_data['material_code'],
                                    surface_type=product_info['category']
                                )
                                
                                db.session.add(product)
                                processed_count += 1
                                
                                if processed_count % 10 == 0:
                                    db.session.commit()
                                    logger.info(f"Processed {processed_count} products")
                            
                            time.sleep(1)  # Rate limiting
                            
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
                    
                finally:
                    self.close_driver()
    
    def download_image(self, image_url, product_name):
        """Download and save product image"""
        try:
            if not image_url:
                return None
            
            # Create images directory if it doesn't exist
            images_dir = os.path.join('static', 'images', 'products')
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate filename
            safe_name = re.sub(r'[^\w\-_\.]', '_', product_name.lower())
            extension = os.path.splitext(urlparse(image_url).path)[1] or '.jpg'
            filename = f"{safe_name}{extension}"
            filepath = os.path.join(images_dir, filename)
            
            # Download image
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"images/products/{filename}"
            
        except Exception as e:
            logger.error(f"Error downloading image {image_url}: {e}")
            return None


def run_scraper(app):
    """Function to run the scraper"""
    scraper = RalphWilsonScraper(app)
    return scraper.scrape_all_products()
