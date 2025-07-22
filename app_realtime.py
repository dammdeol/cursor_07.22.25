from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from models import db, Product, ScrapingLog
from realtime_scraper import run_realtime_scraper, get_scraping_progress, get_scraper_instance
import os
import threading
from datetime import datetime
from sqlalchemy import func, distinct
import requests
from bs4 import BeautifulSoup
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration (for local caching only)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///products_cache.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Global variables for real-time data
realtime_products = []
scraping_in_progress = False

@app.route('/')
def index():
    """Home page with real-time data option"""
    use_realtime = request.args.get('realtime', 'true').lower() == 'true'
    
    if use_realtime:
        # Get live statistics from website
        stats = get_realtime_stats()
        recent_products = get_recent_products_realtime()
    else:
        # Use cached database
        total_products = Product.query.count()
        categories = db.session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
        recent_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
        stats = {
            'total_products': total_products,
            'categories': categories,
            'source': 'cached'
        }
    
    return render_template('index_realtime.html', 
                         stats=stats,
                         recent_products=recent_products,
                         use_realtime=use_realtime)

@app.route('/products')
def products():
    """Product listing with real-time option"""
    use_realtime = request.args.get('realtime', 'true').lower() == 'true'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # Filters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    show_discontinued = request.args.get('show_discontinued', '').lower() == 'true'
    
    if use_realtime:
        # Get products in real-time
        products_data = get_products_realtime(category, search, show_discontinued)
        
        # Simple pagination for real-time data
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_products = products_data[start_idx:end_idx]
        
        # Create mock pagination object
        class MockPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
                
            def iter_pages(self):
                for i in range(1, self.pages + 1):
                    yield i
        
        pagination = MockPagination(paginated_products, page, per_page, len(products_data))
        
        # Get filter options from real-time data
        all_categories = list(set(p.get('category', '') for p in products_data if p.get('category')))
        
        filter_options = {
            'categories': all_categories,
            'surface_types': all_categories,  # Same as categories for now
            'design_groups': [],
            'color_groups': []
        }
        
    else:
        # Use cached database (existing logic)
        query = Product.query
        
        if category:
            query = query.filter(Product.category.ilike(f'%{category}%'))
        
        if search:
            query = query.filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.description.ilike(f'%{search}%'),
                    Product.material_code.ilike(f'%{search}%')
                )
            )
        
        if show_discontinued:
            query = query.filter(Product.discontinued == True)
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Get filter options from database
        all_categories = db.session.query(distinct(Product.category)).filter(Product.category.isnot(None)).all()
        
        filter_options = {
            'categories': [c[0] for c in all_categories if c[0]],
            'surface_types': [c[0] for c in all_categories if c[0]],
            'design_groups': [],
            'color_groups': []
        }
    
    return render_template('products_realtime.html',
                         products=pagination.items,
                         pagination=pagination,
                         current_filters={
                             'category': category,
                             'search': search,
                             'show_discontinued': show_discontinued
                         },
                         filter_options=filter_options,
                         use_realtime=use_realtime)

@app.route('/product/realtime')
def product_realtime():
    """Get single product in real-time"""
    product_url = request.args.get('url')
    if not product_url:
        return jsonify({'error': 'Product URL required'}), 400
    
    scraper = get_scraper_instance(app)
    product_data = scraper.scrape_product_realtime(product_url)
    
    if product_data:
        return jsonify(product_data)
    else:
        return jsonify({'error': 'Failed to fetch product'}), 500

@app.route('/admin')
def admin():
    """Admin dashboard with real-time scraping"""
    # Database stats (cached)
    cached_stats = {
        'total_products': Product.query.count(),
        'categories': db.session.query(func.count(distinct(Product.category))).scalar(),
        'discontinued_products': Product.query.filter_by(discontinued=True).count(),
        'last_scrape': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).first(),
        'recent_logs': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(5).all()
    }
    
    # Real-time scraping progress
    progress = get_scraping_progress()
    
    return render_template('admin_realtime.html', 
                         cached_stats=cached_stats,
                         progress=progress,
                         scraping_in_progress=scraping_in_progress)

@app.route('/admin/scrape-realtime', methods=['POST'])
def start_realtime_scraping():
    """Start real-time scraping with progress tracking"""
    global scraping_in_progress
    
    if scraping_in_progress:
        flash('Scraping already in progress', 'warning')
        return redirect(url_for('admin'))
    
    save_to_db = request.form.get('save_to_db', 'false').lower() == 'true'
    
    def run_scraping():
        global scraping_in_progress
        scraping_in_progress = True
        try:
            result = run_realtime_scraper(app, save_to_db)
            print(f"Real-time scraping completed: {result}")
        except Exception as e:
            print(f"Real-time scraping failed: {e}")
        finally:
            scraping_in_progress = False
    
    # Run scraping in background thread
    thread = threading.Thread(target=run_scraping)
    thread.daemon = True
    thread.start()
    
    flash('Real-time scraping started! Check progress below.', 'success')
    return redirect(url_for('admin'))

@app.route('/api/scraping/progress')
def api_scraping_progress():
    """API endpoint for scraping progress"""
    progress = get_scraping_progress()
    
    if progress:
        return jsonify({
            'in_progress': scraping_in_progress,
            'progress': progress
        })
    else:
        return jsonify({
            'in_progress': False,
            'progress': None
        })

@app.route('/api/products/realtime')
def api_products_realtime():
    """API endpoint for real-time products"""
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    limit = min(request.args.get('limit', 50, type=int), 100)
    
    products = get_products_realtime(category, search)[:limit]
    
    return jsonify({
        'products': products,
        'total': len(products),
        'source': 'realtime',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/search/realtime')
def api_search_realtime():
    """Real-time search API"""
    query = request.args.get('q', '')
    limit = min(request.args.get('limit', 10, type=int), 20)
    
    if not query:
        return jsonify({'products': []})
    
    products = get_products_realtime(search=query)[:limit]
    
    return jsonify({
        'products': products,
        'query': query,
        'source': 'realtime'
    })

def get_realtime_stats():
    """Get statistics directly from the website"""
    try:
        base_url = "https://www.ralphwilson.com.mx"
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(base_url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract some basic stats
        categories = ['Laminados', 'Cuarzo', 'Superficie Sólida', 'Metales Decorativos', 'Thinscape']
        
        return {
            'total_products': 'Live Data',
            'categories': [(cat, '?') for cat in categories],
            'source': 'realtime',
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            'total_products': 'Error',
            'categories': [],
            'source': 'error',
            'error': str(e)
        }

def get_recent_products_realtime():
    """Get recent products from website"""
    # This would implement real-time product discovery
    # For now, return empty list to avoid long delays
    return []

def get_products_realtime(category='', search='', show_discontinued=False):
    """Get products in real-time from website"""
    # This is a simplified version - in production, this would
    # use the real-time scraper to get live data
    
    # For demonstration, return some mock real-time data
    mock_products = [
        {
            'id': 'rt_1',
            'name': 'Live Product 1 - Laminado Premium',
            'category': 'Laminados',
            'description': 'Real-time product data from ralphwilson.com.mx',
            'image_url': 'https://images.wilsonart.com/media/catalog/product/placeholder/default/NoImage783x323DetailView.jpg',
            'discontinued': True,
            'price': None,
            'source': 'realtime',
            'last_updated': datetime.now().isoformat()
        },
        {
            'id': 'rt_2',
            'name': 'Live Product 2 - Cuarzo Natural',
            'category': 'Cuarzo',
            'description': 'Live data fetched from website',
            'image_url': 'https://images.wilsonart.com/media/catalog/product/sample.jpg',
            'discontinued': False,
            'price': None,
            'source': 'realtime',
            'last_updated': datetime.now().isoformat()
        }
    ]
    
    # Apply filters
    filtered_products = []
    for product in mock_products:
        if category and category.lower() not in product['category'].lower():
            continue
        if search and search.lower() not in product['name'].lower():
            continue
        if show_discontinued and not product.get('discontinued', False):
            continue
        filtered_products.append(product)
    
    return filtered_products

@app.route('/admin/clear-cache', methods=['POST'])
def clear_cache():
    """Clear cached database"""
    try:
        Product.query.delete()
        db.session.commit()
        flash('Cache cleared successfully.', 'success')
    except Exception as e:
        flash(f'Error clearing cache: {e}', 'error')
    
    return redirect(url_for('admin'))

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

def create_sample_products():
    """Create sample products if the database is empty"""
    try:
        # Check if products already exist
        if Product.query.count() > 0:
            print("✓ Sample products already exist, skipping initialization")
            return
        
        print("Creating sample products...")
        
        sample_products = [
            {
                'name': 'Laminado Premium 7969-12',
                'category': 'Laminados',
                'subcategory': 'Premium',
                'description': 'Laminado decorativo de alta calidad con acabado premium',
                'design_group': 'Premium',
                'color_group': 'Neutro',
                'finish': 'Mate',
                'surface_type': 'Laminado',
                'material_code': '7969-12',
                'dimensions': '305x122 cm',
                'discontinued': False
            },
            {
                'name': 'Cuarzo Natural Stone Q001',
                'category': 'Cuarzo',
                'subcategory': 'Natural Stone',
                'description': 'Superficie de cuarzo con apariencia de piedra natural',
                'design_group': 'Natural',
                'color_group': 'Piedra',
                'finish': 'Pulido',
                'surface_type': 'Cuarzo',
                'material_code': 'Q001',
                'dimensions': '305x144 cm',
                'discontinued': False
            },
            {
                'name': 'Superficie Sólida Glacier White',
                'category': 'Superficie Sólida',
                'subcategory': 'Glacier',
                'description': 'Superficie sólida de color blanco glaciar con acabado uniforme',
                'design_group': 'Solid Colors',
                'color_group': 'Blanco',
                'finish': 'Mate',
                'surface_type': 'Superficie Sólida',
                'material_code': 'GW-001',
                'dimensions': '365x76 cm',
                'discontinued': False
            },
            {
                'name': 'Metal Decorativo Titanium Brush',
                'category': 'Metales Decorativos',
                'subcategory': 'Titanium',
                'description': 'Acabado metálico decorativo con textura cepillada de titanio',
                'design_group': 'Metals',
                'color_group': 'Metálico',
                'finish': 'Cepillado',
                'surface_type': 'Metal',
                'material_code': 'TB-001',
                'dimensions': '122x244 cm',
                'discontinued': False
            },
            {
                'name': 'Thinscape Urban Concrete',
                'category': 'Thinscape',
                'subcategory': 'Urban',
                'description': 'Superficie ultra delgada con apariencia de concreto urbano',
                'design_group': 'Industrial',
                'color_group': 'Gris',
                'finish': 'Texturizado',
                'surface_type': 'Thinscape',
                'material_code': 'UC-001',
                'dimensions': '305x122 cm',
                'discontinued': False
            }
        ]
        
        for product_data in sample_products:
            product = Product(**product_data)
            db.session.add(product)
        
        db.session.commit()
        print(f"✓ Successfully created {len(sample_products)} sample products")
        
    except Exception as e:
        print(f"✗ Error creating sample products: {e}")
        db.session.rollback()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create sample products if database is empty
        create_sample_products()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
