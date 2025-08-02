from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Supplier
from src.models.inventory import PurchaseOrder
from datetime import datetime

supplier_bp = Blueprint('supplier', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

@supplier_bp.route('/', methods=['GET'])
@jwt_required()
def get_suppliers():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Supplier.query
        
        if active_only:
            query = query.filter(Supplier.is_active == True)
        
        if search:
            query = query.filter(
                (Supplier.supplier_name.contains(search)) |
                (Supplier.contact_person.contains(search)) |
                (Supplier.email.contains(search)) |
                (Supplier.phone.contains(search))
            )
        
        suppliers = query.order_by(Supplier.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers.items],
            'total': suppliers.total,
            'pages': suppliers.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/<int:supplier_id>', methods=['GET'])
@jwt_required()
def get_supplier(supplier_id):
    try:
        supplier = Supplier.query.get(supplier_id)
        
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        # Get recent purchase orders
        recent_orders = PurchaseOrder.query.filter_by(supplier_id=supplier_id).order_by(
            PurchaseOrder.order_date.desc()
        ).limit(10).all()
        
        supplier_dict = supplier.to_dict()
        supplier_dict['recent_orders'] = [order.to_dict() for order in recent_orders]
        
        return jsonify({'supplier': supplier_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/', methods=['POST'])
@jwt_required()
def create_supplier():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('supplier_name'):
            return jsonify({'error': 'Supplier name is required'}), 400
        
        # Check if supplier name already exists
        existing_supplier = Supplier.query.filter_by(supplier_name=data['supplier_name']).first()
        if existing_supplier:
            return jsonify({'error': 'Supplier name already exists'}), 400
        
        # Check if email already exists (if provided)
        if data.get('email'):
            existing_email = Supplier.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Create new supplier
        new_supplier = Supplier(
            supplier_name=data['supplier_name'],
            contact_person=data.get('contact_person'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            tax_number=data.get('tax_number'),
            payment_terms=data.get('payment_terms'),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_supplier)
        db.session.commit()
        
        return jsonify({
            'message': 'Supplier created successfully',
            'supplier': new_supplier.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/<int:supplier_id>', methods=['PUT'])
@jwt_required()
def update_supplier(supplier_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        data = request.get_json()
        
        # Check if supplier name already exists (if changed)
        if data.get('supplier_name') and data['supplier_name'] != supplier.supplier_name:
            existing_supplier = Supplier.query.filter_by(supplier_name=data['supplier_name']).first()
            if existing_supplier:
                return jsonify({'error': 'Supplier name already exists'}), 400
        
        # Check if email already exists (if changed)
        if data.get('email') and data['email'] != supplier.email:
            existing_email = Supplier.query.filter_by(email=data['email']).first()
            if existing_email:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Update supplier fields
        updatable_fields = [
            'supplier_name', 'contact_person', 'email', 'phone', 'address',
            'tax_number', 'payment_terms', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(supplier, field, data[field])
        
        supplier.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Supplier updated successfully',
            'supplier': supplier.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/<int:supplier_id>', methods=['DELETE'])
@jwt_required()
def delete_supplier(supplier_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        # Check if supplier has associated products or purchase orders
        if supplier.products or supplier.purchase_orders:
            # Soft delete - just mark as inactive
            supplier.is_active = False
            supplier.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'message': 'Supplier deactivated successfully (has associated records)'}), 200
        else:
            # Hard delete if no associated records
            db.session.delete(supplier)
            db.session.commit()
            return jsonify({'message': 'Supplier deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@supplier_bp.route('/search', methods=['GET'])
@jwt_required()
def search_suppliers():
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'suppliers': []}), 200
        
        suppliers = Supplier.query.filter(
            Supplier.is_active == True,
            (Supplier.supplier_name.contains(query)) |
            (Supplier.contact_person.contains(query)) |
            (Supplier.email.contains(query)) |
            (Supplier.phone.contains(query))
        ).limit(limit).all()
        
        return jsonify({
            'suppliers': [supplier.to_dict() for supplier in suppliers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

