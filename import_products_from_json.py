#!/usr/bin/env python3
"""
Script to import products from JSON file into the database
Usage: python3 import_products_from_json.py [json_file]
"""
import os
import sys
import json
from flask import Flask
from models import db, Product
from datetime import datetime

def import_products_from_json(json_file='sample_products.json'):
    """Import products from JSON file"""
    try:
        # Read JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        products_data = data.get('sample_products', [])
        if not products_data:
            print(f"✗ No products found in {json_file}")
            return False
        
        print(f"Found {len(products_data)} products in {json_file}")
        
        # Check existing products
        existing_count = Product.query.count()
        print(f"Current database has {existing_count} products")
        
        # Ask for confirmation if products exist
        if existing_count > 0:
            response = input("Database already contains products. Continue? (y/N): ")
            if response.lower() != 'y':
                print("Import cancelled")
                return False
        
        # Import products
        imported_count = 0
        skipped_count = 0
        
        for product_data in products_data:
            # Check if product already exists (by name and material code)
            existing_product = Product.query.filter_by(
                name=product_data['name'],
                material_code=product_data['material_code']
            ).first()
            
            if existing_product:
                print(f"  ⚠️  Skipped: {product_data['name']} (already exists)")
                skipped_count += 1
                continue
            
            # Create new product
            product = Product(
                name=product_data['name'],
                category=product_data['category'],
                subcategory=product_data.get('subcategory'),
                description=product_data.get('description'),
                image_url=product_data.get('image_url'),
                local_image_path=product_data.get('local_image_path'),
                product_url=product_data.get('product_url'),
                design_group=product_data.get('design_group'),
                color_group=product_data.get('color_group'),
                finish=product_data.get('finish'),
                surface_type=product_data.get('surface_type'),
                price=product_data.get('price'),
                dimensions=product_data.get('dimensions'),
                material_code=product_data.get('material_code'),
                discontinued=product_data.get('discontinued', False),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(product)
            imported_count += 1
            print(f"  ✓ Imported: {product_data['name']} ({product_data['category']})")
        
        # Commit changes
        db.session.commit()
        
        print(f"\n�� Import Summary:")
        print(f"   Imported: {imported_count} products")
        print(f"   Skipped: {skipped_count} products")
        print(f"   Total in DB: {Product.query.count()} products")
        
        return True
        
    except FileNotFoundError:
        print(f"✗ JSON file not found: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"✗ Error importing products: {e}")
        db.session.rollback()
        return False

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
    print("Products JSON Import Script")
    print("=" * 30)
    
    # Get JSON file from command line argument or use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'sample_products.json'
    
    app = setup_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        print("✓ Database tables ready")
        
        # Import products
        success = import_products_from_json(json_file)
        
        if success:
            print("\n✅ Import completed successfully!")
        else:
            print("\n❌ Import failed!")
            sys.exit(1)
