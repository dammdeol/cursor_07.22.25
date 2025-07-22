#!/usr/bin/env python3
"""
Script to export products from database to JSON file
Usage: python3 export_products_to_json.py [output_file]
"""
import os
import sys
import json
from flask import Flask
from models import db, Product
from datetime import datetime

def export_products_to_json(output_file='exported_products.json'):
    """Export all products from database to JSON file"""
    try:
        # Get all products
        products = Product.query.all()
        
        if not products:
            print("✗ No products found in database")
            return False
        
        print(f"Found {len(products)} products to export")
        
        # Convert products to JSON format
        products_data = []
        categories = set()
        
        for product in products:
            product_dict = {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "subcategory": product.subcategory,
                "description": product.description,
                "image_url": product.image_url,
                "local_image_path": product.local_image_path,
                "product_url": product.product_url,
                "design_group": product.design_group,
                "color_group": product.color_group,
                "finish": product.finish,
                "surface_type": product.surface_type,
                "price": product.price,
                "dimensions": product.dimensions,
                "material_code": product.material_code,
                "discontinued": product.discontinued,
                "created_at": product.created_at.isoformat() if product.created_at else None,
                "updated_at": product.updated_at.isoformat() if product.updated_at else None
            }
            products_data.append(product_dict)
            if product.category:
                categories.add(product.category)
        
        # Create export data structure
        export_data = {
            "products": products_data,
            "metadata": {
                "description": "Exported products from Ralph Wilson product catalog",
                "export_date": datetime.utcnow().isoformat(),
                "total_products": len(products_data),
                "categories": sorted(list(categories)),
                "discontinued_count": sum(1 for p in products_data if p.get('discontinued', False))
            }
        }
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Successfully exported {len(products_data)} products to {output_file}")
        
        # Show summary
        print(f"\n📊 Export Summary:")
        print(f"   Total products: {len(products_data)}")
        print(f"   Categories: {len(categories)}")
        print(f"   Discontinued: {export_data['metadata']['discontinued_count']}")
        print(f"   Output file: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error exporting products: {e}")
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
    print("Products JSON Export Script")
    print("=" * 30)
    
    # Get output file from command line argument or use default
    output_file = sys.argv[1] if len(sys.argv) > 1 else 'exported_products.json'
    
    app = setup_app()
    
    with app.app_context():
        # Export products
        success = export_products_to_json(output_file)
        
        if success:
            print("\n✅ Export completed successfully!")
        else:
            print("\n❌ Export failed!")
            sys.exit(1)
