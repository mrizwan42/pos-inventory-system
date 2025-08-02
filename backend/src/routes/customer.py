from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Customer
from src.models.sales import Sale, LoyaltyTransaction
from datetime import datetime
import uuid

customer_bp = Blueprint('customer', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

def generate_customer_code():
    """Generate unique customer code"""
    return f"CUST-{str(uuid.uuid4())[:8].upper()}"

@customer_bp.route('/', methods=['GET'])
@jwt_required()
def get_customers():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        query = Customer.query
        
        if active_only:
            query = query.filter(Customer.is_active == True)
        
        if search:
            query = query.filter(
                (Customer.first_name.contains(search)) |
                (Customer.last_name.contains(search)) |
                (Customer.email.contains(search)) |
                (Customer.phone.contains(search)) |
                (Customer.customer_code.contains(search))
            )
        
        customers = query.order_by(Customer.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers.items],
            'total': customers.total,
            'pages': customers.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['GET'])
@jwt_required()
def get_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get customer's purchase history
        sales = Sale.query.filter_by(customer_id=customer_id).order_by(Sale.sale_date.desc()).limit(10).all()
        
        # Get loyalty transactions
        loyalty_transactions = LoyaltyTransaction.query.filter_by(customer_id=customer_id).order_by(LoyaltyTransaction.created_at.desc()).limit(10).all()
        
        customer_dict = customer.to_dict()
        customer_dict['recent_sales'] = [sale.to_dict() for sale in sales]
        customer_dict['recent_loyalty_transactions'] = [transaction.to_dict() for transaction in loyalty_transactions]
        
        return jsonify({'customer': customer_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/', methods=['POST'])
@jwt_required()
def create_customer():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if email already exists (if provided)
        if data.get('email'):
            existing_customer = Customer.query.filter_by(email=data['email']).first()
            if existing_customer:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Generate customer code if not provided
        customer_code = data.get('customer_code') or generate_customer_code()
        
        # Check if customer code already exists
        existing_code = Customer.query.filter_by(customer_code=customer_code).first()
        if existing_code:
            return jsonify({'error': 'Customer code already exists'}), 400
        
        # Parse date of birth if provided
        date_of_birth = None
        if data.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create new customer
        new_customer = Customer(
            customer_code=customer_code,
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            date_of_birth=date_of_birth,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(new_customer)
        db.session.commit()
        
        return jsonify({
            'message': 'Customer created successfully',
            'customer': new_customer.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['PUT'])
@jwt_required()
def update_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        data = request.get_json()
        
        # Check if email already exists (if changed)
        if data.get('email') and data['email'] != customer.email:
            existing_customer = Customer.query.filter_by(email=data['email']).first()
            if existing_customer:
                return jsonify({'error': 'Email already exists'}), 400
        
        # Check if customer code already exists (if changed)
        if data.get('customer_code') and data['customer_code'] != customer.customer_code:
            existing_code = Customer.query.filter_by(customer_code=data['customer_code']).first()
            if existing_code:
                return jsonify({'error': 'Customer code already exists'}), 400
        
        # Parse date of birth if provided
        if data.get('date_of_birth'):
            try:
                data['date_of_birth'] = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Update customer fields
        updatable_fields = [
            'customer_code', 'first_name', 'last_name', 'email', 'phone', 
            'address', 'date_of_birth', 'is_active'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(customer, field, data[field])
        
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Customer updated successfully',
            'customer': customer.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>', methods=['DELETE'])
@jwt_required()
def delete_customer(customer_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Soft delete - just mark as inactive
        customer.is_active = False
        customer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Customer deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/search', methods=['GET'])
@jwt_required()
def search_customers():
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not query:
            return jsonify({'customers': []}), 200
        
        customers = Customer.query.filter(
            Customer.is_active == True,
            (Customer.first_name.contains(query)) |
            (Customer.last_name.contains(query)) |
            (Customer.email.contains(query)) |
            (Customer.phone.contains(query)) |
            (Customer.customer_code.contains(query))
        ).limit(limit).all()
        
        return jsonify({
            'customers': [customer.to_dict() for customer in customers]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>/loyalty', methods=['GET'])
@jwt_required()
def get_customer_loyalty(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Get loyalty transactions
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        transactions = LoyaltyTransaction.query.filter_by(customer_id=customer_id).order_by(
            LoyaltyTransaction.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'customer_id': customer_id,
            'current_points': customer.loyalty_points,
            'total_purchases': float(customer.total_purchases),
            'transactions': [transaction.to_dict() for transaction in transactions.items],
            'total': transactions.total,
            'pages': transactions.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@customer_bp.route('/<int:customer_id>/loyalty/adjust', methods=['POST'])
@jwt_required()
def adjust_loyalty_points(customer_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        data = request.get_json()
        
        if 'points' not in data:
            return jsonify({'error': 'Points value is required'}), 400
        
        points = data['points']
        reason = data.get('reason', 'Manual adjustment')
        
        # Update customer points
        customer.loyalty_points += points
        customer.updated_at = datetime.utcnow()
        
        # Create loyalty transaction
        transaction = LoyaltyTransaction(
            customer_id=customer_id,
            transaction_type='ADJUSTED',
            points=points,
            description=reason
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Loyalty points adjusted successfully',
            'customer': customer.to_dict(),
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

