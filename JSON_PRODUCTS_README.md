# Product JSON Management

This directory contains tools for managing product data in JSON format.

## Files

### `sample_products.json`
Contains sample product data with 5 products across different categories:
- **Laminados**: Laminado Premium 7969-12
- **Cuarzo**: Cuarzo Natural Stone Q001  
- **Superficie Sólida**: Superficie Sólida Glacier White
- **Metales Decorativos**: Metal Decorativo Titanium Brush
- **Thinscape**: Thinscape Urban Concrete

### `import_products_from_json.py`
Script to import products from JSON files into the database.

### `export_products_to_json.py`
Script to export products from the database to JSON files.

### `init_sample_data.py`
Standalone script to initialize the database with sample products.

## Usage

### Import Products from JSON
```bash
# Import from default sample_products.json
python3 import_products_from_json.py

# Import from custom JSON file
python3 import_products_from_json.py my_products.json
```

### Export Products to JSON
```bash
# Export to default exported_products.json
python3 export_products_to_json.py

# Export to custom file
python3 export_products_to_json.py my_export.json
```

### Initialize Sample Data
```bash
# Create sample products in database
python3 init_sample_data.py
```

## JSON Structure

### Product Object
```json
{
  "name": "Product Name",
  "category": "Category Name",
  "subcategory": "Subcategory",
  "description": "Product description",
  "image_url": "https://example.com/image.jpg",
  "local_image_path": "/path/to/local/image.jpg",
  "product_url": "https://example.com/product",
  "design_group": "Design Group",
  "color_group": "Color Group",
  "finish": "Finish Type",
  "surface_type": "Surface Type",
  "price": 99.99,
  "dimensions": "305x122 cm",
  "material_code": "CODE-001",
  "discontinued": false
}
```

### Full File Structure
```json
{
  "sample_products": [
    // Array of product objects
  ],
  "metadata": {
    "description": "Description of the data",
    "version": "1.0",
    "created_date": "2024-07-22",
    "total_products": 5,
    "categories": ["Category1", "Category2"]
  }
}
```

## Features

### Import Script Features
- ✅ Validates JSON format
- ✅ Checks for duplicate products (by name + material_code)
- ✅ Shows progress and summary
- ✅ Rollback on errors
- ✅ Interactive confirmation for existing data

### Export Script Features
- ✅ Exports all product fields
- ✅ Includes metadata (timestamps, categories, counts)
- ✅ Proper UTF-8 encoding
- ✅ Human-readable JSON formatting

### Sample Data Features
- ✅ Skip if products already exist
- ✅ Create all required tables
- ✅ Comprehensive product data
- ✅ Multiple categories represented

## Error Handling

All scripts include proper error handling for:
- Missing files
- Invalid JSON format
- Database connection issues
- Duplicate data conflicts
- Permission errors

## Examples

### Create Fresh Database with Sample Data
```bash
# Remove existing database
rm -f instance/products.db

# Run any app to create fresh database with samples
python3 app.py
```

### Backup Current Products
```bash
# Export current products
python3 export_products_to_json.py backup_$(date +%Y%m%d).json
```

### Import Additional Products
```bash
# Create your own JSON file with new products
python3 import_products_from_json.py new_products.json
```
