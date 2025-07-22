#!/usr/bin/env python3
"""
Script to validate product JSON files
Usage: python3 validate_products_json.py [json_file]
"""
import sys
import json

def validate_product_json(json_file='sample_products.json'):
    """Validate product JSON file structure and data"""
    try:
        # Read and parse JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ JSON file '{json_file}' is valid")
        
        # Check structure
        if 'sample_products' not in data and 'products' not in data:
            print("✗ Missing 'sample_products' or 'products' key")
            return False
        
        # Get products array
        products = data.get('sample_products', data.get('products', []))
        
        if not isinstance(products, list):
            print("✗ Products must be an array")
            return False
        
        print(f"✓ Found {len(products)} products")
        
        # Validate each product
        required_fields = ['name', 'category']
        optional_fields = [
            'subcategory', 'description', 'image_url', 'local_image_path',
            'product_url', 'design_group', 'color_group', 'finish',
            'surface_type', 'price', 'dimensions', 'material_code', 'discontinued'
        ]
        
        valid_products = 0
        categories = set()
        
        for i, product in enumerate(products):
            if not isinstance(product, dict):
                print(f"✗ Product {i+1} is not an object")
                continue
            
            # Check required fields
            missing_fields = [field for field in required_fields if field not in product]
            if missing_fields:
                print(f"✗ Product {i+1} missing required fields: {missing_fields}")
                continue
            
            # Check field types
            if not isinstance(product.get('name'), str) or not product.get('name').strip():
                print(f"✗ Product {i+1} has invalid name")
                continue
            
            if not isinstance(product.get('category'), str) or not product.get('category').strip():
                print(f"✗ Product {i+1} has invalid category")
                continue
            
            # Add to categories
            categories.add(product['category'])
            valid_products += 1
            
            print(f"  ✓ Product {i+1}: {product['name']} ({product['category']})")
        
        print(f"\n📊 Validation Summary:")
        print(f"   Valid products: {valid_products}/{len(products)}")
        print(f"   Categories found: {len(categories)}")
        print(f"   Categories: {sorted(categories)}")
        
        # Check metadata if present
        if 'metadata' in data:
            metadata = data['metadata']
            print(f"\n📋 Metadata:")
            if 'description' in metadata:
                print(f"   Description: {metadata['description']}")
            if 'total_products' in metadata:
                expected = metadata['total_products']
                actual = len(products)
                if expected == actual:
                    print(f"   ✓ Product count matches metadata: {expected}")
                else:
                    print(f"   ⚠️  Product count mismatch: metadata={expected}, actual={actual}")
        
        if valid_products == len(products):
            print(f"\n✅ All products are valid!")
            return True
        else:
            print(f"\n⚠️  {len(products) - valid_products} products have issues")
            return False
        
    except FileNotFoundError:
        print(f"✗ File not found: {json_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"✗ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return False

if __name__ == '__main__':
    print("Product JSON Validation Script")
    print("=" * 35)
    
    # Get JSON file from command line or use default
    json_file = sys.argv[1] if len(sys.argv) > 1 else 'sample_products.json'
    
    success = validate_product_json(json_file)
    
    if not success:
        sys.exit(1)
