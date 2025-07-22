#!/usr/bin/env python3
"""
Standalone script to initialize sample products in the database
Usage: python3 init_sample_data.py
"""
import os
from flask import Flask
from models import db, Product

def create_sample_products():
    """Create sample products if the database is empty"""
    try:
        # Check if products already exist
        existing_count = Product.query.count()
        if existing_count > 0:
            print(f"✓ Database already contains {existing_count} products, skipping initialization")
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
        
        # Display created products
        print("\nCreated products:")
        for product in sample_products:
            print(f"  • {product['name']} ({product['category']})")
        
    except Exception as e:
        print(f"✗ Error creating sample products: {e}")
        db.session.rollback()
        raise

def setup_app():
    """Setup Flask app and database connection"""
    app = Flask(__name__)
    
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
    
    return app

if __name__ == '__main__':
    print("Sample Products Initialization Script")
    print("=" * 40)
    
    app = setup_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("✓ Database tables ready")
        
        # Create sample products
        create_sample_products()
        
        # Show final statistics
        total_products = Product.query.count()
        categories = db.session.query(Product.category).distinct().count()
        
        print(f"\n📊 Database Summary:")
        print(f"   Total products: {total_products}")
        print(f"   Categories: {categories}")
        print(f"   Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
    print("\n✅ Sample data initialization completed!")
