from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    subcategory = db.Column(db.String(100))
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    local_image_path = db.Column(db.String(500))
    product_url = db.Column(db.String(500))
    design_group = db.Column(db.String(100))
    color_group = db.Column(db.String(100))
    finish = db.Column(db.String(100))
    surface_type = db.Column(db.String(100))
    price = db.Column(db.Float)
    dimensions = db.Column(db.String(100))
    material_code = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    discontinued = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<Product {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'image_url': self.image_url,
            'local_image_path': self.local_image_path,
            'product_url': self.product_url,
            'design_group': self.design_group,
            'color_group': self.color_group,
            'finish': self.finish,
            'surface_type': self.surface_type,
            'price': self.price,
            'dimensions': self.dimensions,
            'material_code': self.material_code,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'discontinued': self.discontinued,
        }

class ScrapingLog(db.Model):
    __tablename__ = 'scraping_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    status = db.Column(db.String(50))  # 'running', 'completed', 'failed'
    products_scraped = db.Column(db.Integer, default=0)
    errors = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ScrapingLog {self.id} - {self.status}>'

class ScrapingTimer(db.Model):
    __tablename__ = 'scraping_timers'
    
    id = db.Column(db.Integer, primary_key=True)
    is_enabled = db.Column(db.Boolean, default=False)
    interval_minutes = db.Column(db.Integer, default=60)
    next_run = db.Column(db.DateTime)
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScrapingTimer {self.id} - {"Enabled" if self.is_enabled else "Disabled"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'is_enabled': self.is_enabled,
            'interval_minutes': self.interval_minutes,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

# Add discontinued field to existing Product model
# This would normally require a database migration, but we'll update the model definition

# Update the Product model to include discontinued status
# Note: In production, this would require an ALTER TABLE migration
