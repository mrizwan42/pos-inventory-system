from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Product, Category, Supplier
from src.models.inventory import Inventory
from datetime import datetime
import uuid

product_bp = Blueprint('product', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

@product_bp.route('/', methods=['GET'])
@jwt_required()
def get_products():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        category_id = request.args.get('category_id', type=int)
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Product.query
        
        if active_only:
            query = query.filter(Product.is_active == True)
        
        if search:
            query = query.filter(
                (Product.product_name.contains(search)) |
                (Product.product_code.contains(search)) |
                (Product.barcode.contains(search))
            )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        products = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'products': [product.to_dict() for product in products.items],
            'total': products.total,
            'pages': products.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product(product_id):
    try:
        product = Product.query.get(product_id)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Get inventory information
        inventory_records = Inventory.query.filter_by(product_id=product_id).all()
        product_dict = product.to_dict()
        product_dict['inventory'] = [inv.to_dict() for inv in inventory_records]
        
        return jsonify({'product': product_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_name', 'category_id', 'unit_of_measure', 'cost_price', 'selling_price']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Generate product code if not provided
        if not data.get('product_code'):
            data['product_code'] = f"PRD-{str(uuid.uuid4())[:8].upper()}"
        
        # Check if product code already exists
        existing_product = Product.query.filter_by(product_code=data['product_code']).first()
        if existing_product:
            return jsonify({'error': 'Product code already exists'}), 400
        
        # Check if barcode already exists (if provided)
        if data.get('barcode'):
            existing_barcode = Product.query.filter_by(barcode=data['barcode']).first()
            if existing_barcode:
                return jsonify({'error': 'Barcode already exists'}), 400
        
        # Validate category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 400
        
        # Validate supplier exists (if provided)
        if data.get('supplier_id'):
            supplier = Supplier.query.get(data['supplier_id'])
            if not supplier:
                return jsonify({'error': 'Supplier not found'}), 400
        
        # Create new product
        new_product = Product(
            product_code=data['product_code'],
            barcode=data.get('barcode'),
            product_name=data['product_name'],
            description=data.get('description'),
            category_id=data['category_id'],
            supplier_id=data.get('supplier_id'),
            unit_of_measure=data['unit_of_measure'],
            cost_price=data['cost_price'],
            selling_price=data['selling_price'],
            min_stock_level=data.get('min_stock_level', 0),
            max_stock_level=data.get('max_stock_level', 0),
            reorder_level=data.get('reorder_level', 0),
            tax_rate=data.get('tax_rate', 0),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        return jsonify({
            'message': 'Product created successfully',
            'product': new_product.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        data = request.get_json()
        
        # Check if product code already exists (if changed)
        if data.get('product_code') and data['product_code'] != product.product_code:
            existing_product = Product.query.filter_by(product_code=data['product_code']).first()
            if existing_product:
                return jsonify({'error': 'Product code already exists'}), 400
        
        # Check if barcode already exists (if changed)
        if data.get('barcode') and data['barcode'] != product.barcode:
            existing_barcode = Product.query.filter_by(barcode=data['barcode']).first()
            if existing_barcode:
                return jsonify({'error': 'Barcode already exists'}), 400
        
        # Validate category exists (if changed)
        if data.get('category_id') and data['category_id'] != product.category_id:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({'error': 'Category not found'}), 400
        
        # Validate supplier exists (if changed)
        if data.get('supplier_id') and data['supplier_id'] != product.supplier_id:
            supplier = Supplier.query.get(data['supplier_id'])
            if not supplier:
                return jsonify({'error': 'Supplier not found'}), 400
        
        # Update product fields
        updatable_fields = [
            'product_code', 'barcode', 'product_name', 'description', 'category_id',
            'supplier_id', 'unit_of_measure', 'cost_price', 'selling_price',
            'min_stock_level', 'max_stock_level', 'reorder_level', 'tax_rate', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(product, field, data[field])
        
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Soft delete - just mark as inactive
        product.is_active = False
        product.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Product deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@product_bp.route('/search', methods=['GET'])
@jwt_required()
def search_products():
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'products': []}), 200
        
        products = Product.query.filter(
            Product.is_active == True,
            (Product.product_name.contains(query)) |
            (Product.product_code.contains(query)) |
            (Product.barcode.contains(query))
        ).limit(limit).all()
        
        return jsonify({
            'products': [product.to_dict() for product in products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@product_bp.route('/barcode/<barcode>', methods=['GET'])
@jwt_required()
def get_product_by_barcode(barcode):
    try:
        product = Product.query.filter_by(barcode=barcode, is_active=True).first()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify({'product': product.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

