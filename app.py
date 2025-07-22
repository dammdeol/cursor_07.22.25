from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from models import db, Product, ScrapingLog, ScrapingTimer
from scraper_simple import run_scraper
from scheduler import get_scheduler
import os
import threading
from datetime import datetime, timedelta
from sqlalchemy import func, distinct

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
if not os.environ.get('DATABASE_URL'):
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    # Use absolute path for SQLite
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'products.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize scheduler
scheduler = get_scheduler(app)

@app.route('/')
def index():
    """Home page with search and navigation"""
    # Get statistics
    total_products = Product.query.count()
    categories = db.session.query(Product.category, func.count(Product.id)).group_by(Product.category).all()
    recent_products = Product.query.order_by(Product.created_at.desc()).limit(8).all()
    
    return render_template('index.html', 
                         total_products=total_products,
                         categories=categories,
                         recent_products=recent_products)

@app.route('/products')
def products():
    """Product listing page with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # Filters
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    surface_type = request.args.get('surface_type', '')
    design_group = request.args.get('design_group', '')
    color_group = request.args.get('color_group', '')
    
    # Build query
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
    
    if surface_type:
        query = query.filter(Product.surface_type.ilike(f'%{surface_type}%'))
    
    if design_group:
        query = query.filter(Product.design_group.ilike(f'%{design_group}%'))
    
    if color_group:
        query = query.filter(Product.color_group.ilike(f'%{color_group}%'))
    
    # Pagination
    products_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get filter options
    all_categories = db.session.query(distinct(Product.category)).filter(Product.category.isnot(None)).all()
    all_surface_types = db.session.query(distinct(Product.surface_type)).filter(Product.surface_type.isnot(None)).all()
    all_design_groups = db.session.query(distinct(Product.design_group)).filter(Product.design_group.isnot(None)).all()
    all_color_groups = db.session.query(distinct(Product.color_group)).filter(Product.color_group.isnot(None)).all()
    
    return render_template('products.html',
                         products=products_pagination.items,
                         pagination=products_pagination,
                         current_filters={
                             'category': category,
                             'search': search,
                             'surface_type': surface_type,
                             'design_group': design_group,
                             'color_group': color_group
                         },
                         filter_options={
                             'categories': [c[0] for c in all_categories if c[0]],
                             'surface_types': [s[0] for s in all_surface_types if s[0]],
                             'design_groups': [d[0] for d in all_design_groups if d[0]],
                             'color_groups': [c[0] for c in all_color_groups if c[0]]
                         })

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Individual product detail page"""
    product = Product.query.get_or_404(product_id)
    
    # Get related products (same category)
    related_products = Product.query.filter(
        Product.category == product.category,
        Product.id != product.id
    ).limit(4).all()
    
    return render_template('product_detail.html', 
                         product=product,
                         related_products=related_products)

@app.route('/categories')
def categories():
    """Categories overview page"""
    categories_data = db.session.query(
        Product.category,
        func.count(Product.id).label('count'),
        func.max(Product.image_url).label('sample_image')
    ).group_by(Product.category).all()
    
    return render_template('categories.html', categories=categories_data)

@app.route('/api/products')
def api_products():
    """API endpoint for products"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    products = Product.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'products': [p.to_dict() for p in products.items],
        'total': products.total,
        'pages': products.pages,
        'current_page': products.page,
        'has_next': products.has_next,
        'has_prev': products.has_prev
    })

@app.route('/api/search')
def api_search():
    """API endpoint for product search"""
    query = request.args.get('q', '')
    limit = min(request.args.get('limit', 10, type=int), 50)
    
    if not query:
        return jsonify({'products': []})
    
    products = Product.query.filter(
        db.or_(
            Product.name.ilike(f'%{query}%'),
            Product.description.ilike(f'%{query}%'),
            Product.category.ilike(f'%{query}%'),
            Product.material_code.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    return jsonify({
        'products': [p.to_dict() for p in products]
    })

@app.route('/admin')
def admin():
    """Admin dashboard"""
    stats = {
        'discontinued_products': Product.query.filter_by(discontinued=True).count(),
        'total_products': Product.query.count(),
        'categories': db.session.query(func.count(distinct(Product.category))).scalar(),
        'last_scrape': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).first(),
        'recent_logs': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(5).all(),
        'timer_status': scheduler.get_status()
    }
    
    return render_template('admin.html', stats=stats)

@app.route('/admin/scrape', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    def run_scraping():
        try:
            count = run_scraper(app)
            print(f"Scraping completed. {count} products processed.")
        except Exception as e:
            print(f"Scraping failed: {e}")
    
    # Run scraping in background thread
    thread = threading.Thread(target=run_scraping)
    thread.daemon = True
    thread.start()
    
    flash('Scraping started in background. Check admin panel for progress.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/timer/start', methods=['POST'])
def start_timer():
    """Start automatic scraping timer"""
    try:
        interval = request.form.get('interval', 60, type=int)
        if interval < 5:  # Minimum 5 minutes
            flash('Interval must be at least 5 minutes.', 'error')
            return redirect(url_for('admin'))
            
        scheduler.start_timer(interval)
        
        # Save timer settings to database
        timer_config = ScrapingTimer.query.first()
        if not timer_config:
            timer_config = ScrapingTimer()
            db.session.add(timer_config)
            
        timer_config.is_enabled = True
        timer_config.interval_minutes = interval
        timer_config.next_run = datetime.now() + timedelta(minutes=interval)
        db.session.commit()
        
        flash(f'Automatic scraping started. Will run every {interval} minutes.', 'success')
    except Exception as e:
        flash(f'Error starting timer: {e}', 'error')
        
    return redirect(url_for('admin'))

@app.route('/admin/timer/stop', methods=['POST'])
def stop_timer():
    """Stop automatic scraping timer"""
    try:
        scheduler.stop_timer()
        
        # Update database
        timer_config = ScrapingTimer.query.first()
        if timer_config:
            timer_config.is_enabled = False
            timer_config.next_run = None
            db.session.commit()
            
        flash('Automatic scraping stopped.', 'success')
    except Exception as e:
        flash(f'Error stopping timer: {e}', 'error')
        
    return redirect(url_for('admin'))

@app.route('/admin/timer/status')
def timer_status():
    """Get timer status API"""
    return jsonify(scheduler.get_status())

@app.route('/admin/clear-data', methods=['POST'])
def clear_data():
    """Clear all product data"""
    try:
        Product.query.delete()
        db.session.commit()
        flash('All product data cleared successfully.', 'success')
    except Exception as e:
        flash(f'Error clearing data: {e}', 'error')
    
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
        
        # Initialize timer from database if exists
        timer_config = ScrapingTimer.query.first()
        if timer_config and timer_config.is_enabled:
            try:
                scheduler.start_timer(timer_config.interval_minutes)
            except Exception as e:
                print(f"Failed to restore timer: {e}")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)

@app.route('/products/discontinued')
def discontinued_products():
    """Show only discontinued products"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    
    # Query only discontinued products
    products_pagination = Product.query.filter_by(discontinued=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('products.html',
                         products=products_pagination.items,
                         pagination=products_pagination,
                         current_filters={'discontinued': True},
                         filter_options={
                             'categories': [],
                             'surface_types': [],
                             'design_groups': [],
                             'color_groups': []
                         },
                         show_discontinued=True)

@app.route('/api/products/stats')
def api_product_stats():
    """API endpoint for product statistics including discontinued count"""
    total_products = Product.query.count()
    active_products = Product.query.filter_by(discontinued=False).count()
    discontinued_products = Product.query.filter_by(discontinued=True).count()
    
    categories_stats = db.session.query(
        Product.category,
        func.count(Product.id).label('total'),
        func.sum(db.case([(Product.discontinued == True, 1)], else_=0)).label('discontinued')
    ).group_by(Product.category).all()
    
    return jsonify({
        'total_products': total_products,
        'active_products': active_products,
        'discontinued_products': discontinued_products,
        'categories': [
            {
                'name': cat[0],
                'total': cat[1],
                'discontinued': cat[2] or 0,
                'active': cat[1] - (cat[2] or 0)
            }
            for cat in categories_stats
        ]
    })
