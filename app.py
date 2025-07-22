from flask import Flask, render_template, request, jsonify, url_for, redirect, flash
from models import db, Product, ScrapingLog
from scraper import run_scraper
import os
import threading
from datetime import datetime
from sqlalchemy import func, distinct

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///products.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

@app.before_request
def create_tables():
    """Create database tables if they don't exist"""
    db.create_all()

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
        'total_products': Product.query.count(),
        'categories': db.session.query(func.count(distinct(Product.category))).scalar(),
        'last_scrape': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).first(),
        'recent_logs': ScrapingLog.query.order_by(ScrapingLog.start_time.desc()).limit(5).all()
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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)
