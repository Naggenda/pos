from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    ROLES = ['ADMIN', 'MANAGER', 'CASHIER']
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='CASHIER')
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
        }

class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, unique=True)
    sku = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100))
    tax_rate = db.Column(db.Float, default=0.18)  # Standard VAT rate for Uganda
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'sku': self.sku,
            'description': self.description,
            'price': self.price,
            'quantity': self.quantity,
            'category': self.category,
            'tax_rate': self.tax_rate,
        }

class Sale(db.Model):
    """Sales transaction model"""
    __tablename__ = 'sales'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    receipt_number = db.Column(db.String(50), nullable=False, unique=True)
    total_amount = db.Column(db.Float, nullable=False)
    tax_amount = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    net_amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), default='CASH')  # CASH, CARD, MOBILE_MONEY
    efris_status = db.Column(db.String(50), default='PENDING')  # PENDING, SUBMITTED, APPROVED, FAILED
    efris_receipt_code = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'receipt_number': self.receipt_number,
            'total_amount': self.total_amount,
            'tax_amount': self.tax_amount,
            'discount_amount': self.discount_amount,
            'net_amount': self.net_amount,
            'payment_method': self.payment_method,
            'efris_status': self.efris_status,
            'efris_receipt_code': self.efris_receipt_code,
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items],
        }

class SaleItem(db.Model):
    """Individual item in a sale"""
    __tablename__ = 'sale_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.String(36), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    tax_rate = db.Column(db.Float, default=0.18)
    tax_amount = db.Column(db.Float, default=0)
    subtotal = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'tax_rate': self.tax_rate,
            'tax_amount': self.tax_amount,
            'subtotal': self.subtotal,
        }

class EfrisLog(db.Model):
    """Log for EFRIS API interactions"""
    __tablename__ = 'efris_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sale_id = db.Column(db.String(36), db.ForeignKey('sales.id'))
    endpoint = db.Column(db.String(200))
    method = db.Column(db.String(10))
    request_data = db.Column(db.JSON)
    response_status = db.Column(db.Integer)
    response_data = db.Column(db.JSON)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'response_status': self.response_status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
        }
