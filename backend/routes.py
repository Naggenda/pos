from flask import Blueprint, request, jsonify
from models import db, Product, Sale, SaleItem
from efris_integration import submit_to_efris
from auth import token_required, role_required
from datetime import datetime, timedelta
import uuid

api = Blueprint('api', __name__, url_prefix='/api')

# Product Routes
@api.route('/products', methods=['GET'])
@token_required
def get_products():
    """Get all products"""
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products]), 200

@api.route('/products/<product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product.to_dict()), 200

@token_required
@role_required('ADMIN', 'MANAGER')
@api.route('/products', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('sku') or data.get('price') is None:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if SKU already exists
    existing = Product.query.filter_by(sku=data['sku']).first()
    if existing:
        return jsonify({'error': 'SKU already exists'}), 400
    
    product = Product(
        id=str(uuid.uuid4()),
        name=data['name'],
        sku=data['sku'],
        description=data.get('description', ''),
        price=float(data['price']),
        quantity=int(data.get('quantity', 0)),
        category=data.get('category', ''),
        tax_rate=float(data.get('tax_rate', 0.18))
    )
    
    try:
        db.session.add(product)
        db.session.commit()
        return jsonify(product.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@token_required
@role_required('ADMIN', 'MANAGER')

@api.route('/products/<product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        product.name = data['name']
    if 'price' in data:
        product.price = float(data['price'])
    if 'quantity' in data:
        product.quantity = int(data['quantity'])
    if 'description' in data:
        product.description = data['description']
    if 'category' in data:
        product.category = data['category']
    if 'tax_rate' in data:
        product.tax_rate = float(data['tax_rate'])
    
    try:
        db.session.commit()
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@token_required
@role_required('ADMIN', 'MANAGER')

@api.route('/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@token_required
# Sales Routes
@api.route('/sales', methods=['GET'])
def get_sales():
    """Get all sales with optional filtering"""
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    query = Sale.query
    
    if status:
        query = query.filter_by(efris_status=status)
    
    if date_from:
        try:
            from_date = datetime.fromisoformat(date_from)
            query = query.filter(Sale.created_at >= from_date)
        except:
            pass
    
    if date_to:
        try:
            to_date = datetime.fromisoformat(date_to)
            query = query.filter(Sale.created_at <= to_date)
        except:
            pass
    
    sales = query.order_by(Sale.created_at.desc()).all()
    return jsonify([sale.to_dict() for sale in sales]), 200

@api.route('/sales/<sale_id>', methods=['GET'])
def get_sale(sale_id):
    """Get a specific sale"""
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    return jsonify(sale.to_dict()), 200

@token_required
@role_required('CASHIER', 'MANAGER', 'ADMIN')
@api.route('/sales', methods=['POST'])
def create_sale():
    """Create a new sale"""
    data = request.get_json()
    
    if not data or not data.get('items') or len(data['items']) == 0:
        return jsonify({'error': 'Invalid sale data'}), 400
    
    try:
        # Calculate totals
        total_amount = 0
        tax_amount = 0
        
        # Create sale
        sale = Sale(
            id=str(uuid.uuid4()),
            receipt_number=f"RC-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            total_amount=0,
            tax_amount=0,
            net_amount=0,
            payment_method=data.get('payment_method', 'CASH'),
            efris_status='PENDING'
        )
        
        db.session.add(sale)
        db.session.flush()  # Get the sale ID
        
        # Add items
        for item in data.get('items', []):
            product = Product.query.get(item['product_id'])
            if not product:
                db.session.rollback()
                return jsonify({'error': f"Product {item['product_id']} not found"}), 404
            
            quantity = int(item['quantity'])
            if quantity > product.quantity:
                db.session.rollback()
                return jsonify({'error': f"Insufficient stock for {product.name}"}), 400
            
            unit_price = product.price
            tax_rate = product.tax_rate
            subtotal = quantity * unit_price
            tax_item = subtotal * tax_rate
            
            sale_item = SaleItem(
                id=str(uuid.uuid4()),
                sale_id=sale.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                tax_rate=tax_rate,
                tax_amount=tax_item,
                subtotal=subtotal
            )
            
            db.session.add(sale_item)
            
            # Update product quantity
            product.quantity -= quantity
            
            # Add to totals
            total_amount += subtotal
            tax_amount += tax_item
        
        # Update sale totals
        discount_amount = float(data.get('discount_amount', 0))
        sale.total_amount = total_amount
        sale.tax_amount = tax_amount
        sale.discount_amount = discount_amount
        sale.net_amount = total_amount - discount_amount
        
        db.session.commit()
        
        return jsonify(sale.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
@token_required
@role_required('ADMIN', 'MANAGER', 'CASHIER')

@api.route('/sales/<sale_id>/submit-efris', methods=['POST'])
def submit_sale_to_efris(sale_id):
    """Submit a sale to EFRIS"""
    sale = Sale.query.get(sale_id)
    if not sale:
        return jsonify({'error': 'Sale not found'}), 404
    
    success, message, receipt_code = submit_to_efris(sale)
    
    return jsonify({
        'success': success,
        'message': message,
        'receipt_code': receipt_code,
        'efris_status': sale.efris_status
    }), 200 if success else 400

@token_required
# Dashboard Routes
@api.route('/dashboard/summary', methods=['GET'])
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    days = int(request.args.get('days', 30))
    date_from = datetime.now() - timedelta(days=days)
    
    sales = Sale.query.filter(Sale.created_at >= date_from).all()
    
    total_sales = len(sales)
    total_revenue = sum(sale.net_amount for sale in sales)
    total_tax = sum(sale.tax_amount for sale in sales)
    
    efris_submitted = len([s for s in sales if s.efris_status == 'SUBMITTED'])
    efris_failed = len([s for s in sales if s.efris_status == 'FAILED'])
    
    # Products by category
    products = Product.query.all()
    low_stock = [p for p in products if p.quantity <= 5]
    
    return jsonify({
        'period_days': days,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_tax': total_tax,
        'average_transaction': total_revenue / total_sales if total_sales > 0 else 0,
        'efris_submitted': efris_submitted,
        'efris_failed': efris_failed,
        'low_stock_count': len(low_stock),
        'total_products': len(products),
    }), 200

# Health Check
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200
