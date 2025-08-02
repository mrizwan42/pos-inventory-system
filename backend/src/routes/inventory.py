from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Product, Branch
from src.models.inventory import Inventory, StockMovement
from datetime import datetime
from sqlalchemy import func

inventory_bp = Blueprint('inventory', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

@inventory_bp.route('/', methods=['GET'])
@jwt_required()
def get_inventory():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        branch_id = request.args.get('branch_id', type=int)
        low_stock_only = request.args.get('low_stock_only', 'false').lower() == 'true'
        search = request.args.get('search', '')
        
        query = db.session.query(Inventory).join(Product)
        
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
        
        if search:
            query = query.filter(
                (Product.product_name.contains(search)) |
                (Product.product_code.contains(search)) |
                (Product.barcode.contains(search))
            )
        
        if low_stock_only:
            query = query.filter(Inventory.current_stock <= Product.reorder_level)
        
        inventory_records = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'inventory': [record.to_dict() for record in inventory_records.items],
            'total': inventory_records.total,
            'pages': inventory_records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/product/<int:product_id>', methods=['GET'])
@jwt_required()
def get_product_inventory(product_id):
    try:
        inventory_records = Inventory.query.filter_by(product_id=product_id).all()
        
        return jsonify({
            'inventory': [record.to_dict() for record in inventory_records]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/adjust', methods=['POST'])
@jwt_required()
def adjust_stock():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'branch_id', 'quantity', 'movement_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        product_id = data['product_id']
        branch_id = data['branch_id']
        quantity = data['quantity']
        movement_type = data['movement_type']  # IN, OUT, ADJUSTMENT
        unit_cost = data.get('unit_cost')
        reference = data.get('reference', '')
        notes = data.get('notes', '')
        
        # Validate product and branch exist
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        branch = Branch.query.get(branch_id)
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
        
        # Get or create inventory record
        inventory = Inventory.query.filter_by(
            product_id=product_id, 
            branch_id=branch_id
        ).first()
        
        if not inventory:
            inventory = Inventory(
                product_id=product_id,
                branch_id=branch_id,
                current_stock=0
            )
            db.session.add(inventory)
        
        # Calculate new stock level
        if movement_type == 'IN':
            new_stock = inventory.current_stock + quantity
        elif movement_type == 'OUT':
            if inventory.current_stock < quantity:
                return jsonify({'error': 'Insufficient stock'}), 400
            new_stock = inventory.current_stock - quantity
        elif movement_type == 'ADJUSTMENT':
            new_stock = quantity  # Direct adjustment to specific quantity
        else:
            return jsonify({'error': 'Invalid movement type'}), 400
        
        # Update inventory
        inventory.current_stock = new_stock
        inventory.last_updated = datetime.utcnow()
        
        # Create stock movement record
        stock_movement = StockMovement(
            product_id=product_id,
            branch_id=branch_id,
            movement_type=movement_type,
            quantity=quantity if movement_type != 'OUT' else -quantity,
            unit_cost=unit_cost,
            reference=reference,
            notes=notes,
            created_by=get_jwt_identity()
        )
        
        db.session.add(stock_movement)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock adjusted successfully',
            'inventory': inventory.to_dict(),
            'movement': stock_movement.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/transfer', methods=['POST'])
@jwt_required()
def transfer_stock():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'from_branch_id', 'to_branch_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        product_id = data['product_id']
        from_branch_id = data['from_branch_id']
        to_branch_id = data['to_branch_id']
        quantity = data['quantity']
        notes = data.get('notes', '')
        
        if from_branch_id == to_branch_id:
            return jsonify({'error': 'Source and destination branches cannot be the same'}), 400
        
        # Validate product and branches exist
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        from_branch = Branch.query.get(from_branch_id)
        to_branch = Branch.query.get(to_branch_id)
        if not from_branch or not to_branch:
            return jsonify({'error': 'Branch not found'}), 404
        
        # Get source inventory
        from_inventory = Inventory.query.filter_by(
            product_id=product_id, 
            branch_id=from_branch_id
        ).first()
        
        if not from_inventory or from_inventory.available_stock < quantity:
            return jsonify({'error': 'Insufficient stock in source branch'}), 400
        
        # Get or create destination inventory
        to_inventory = Inventory.query.filter_by(
            product_id=product_id, 
            branch_id=to_branch_id
        ).first()
        
        if not to_inventory:
            to_inventory = Inventory(
                product_id=product_id,
                branch_id=to_branch_id,
                current_stock=0
            )
            db.session.add(to_inventory)
        
        # Update inventories
        from_inventory.current_stock -= quantity
        from_inventory.last_updated = datetime.utcnow()
        
        to_inventory.current_stock += quantity
        to_inventory.last_updated = datetime.utcnow()
        
        # Create stock movement records
        transfer_ref = f"TRANSFER-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        out_movement = StockMovement(
            product_id=product_id,
            branch_id=from_branch_id,
            movement_type='TRANSFER',
            quantity=-quantity,
            reference=transfer_ref,
            notes=f"Transfer to {to_branch.branch_name}. {notes}",
            created_by=get_jwt_identity()
        )
        
        in_movement = StockMovement(
            product_id=product_id,
            branch_id=to_branch_id,
            movement_type='TRANSFER',
            quantity=quantity,
            reference=transfer_ref,
            notes=f"Transfer from {from_branch.branch_name}. {notes}",
            created_by=get_jwt_identity()
        )
        
        db.session.add(out_movement)
        db.session.add(in_movement)
        db.session.commit()
        
        return jsonify({
            'message': 'Stock transferred successfully',
            'from_inventory': from_inventory.to_dict(),
            'to_inventory': to_inventory.to_dict(),
            'transfer_reference': transfer_ref
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/movements', methods=['GET'])
@jwt_required()
def get_stock_movements():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        product_id = request.args.get('product_id', type=int)
        branch_id = request.args.get('branch_id', type=int)
        movement_type = request.args.get('movement_type')
        
        query = StockMovement.query
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if branch_id:
            query = query.filter(StockMovement.branch_id == branch_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        movements = query.order_by(StockMovement.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'movements': [movement.to_dict() for movement in movements.items],
            'total': movements.total,
            'pages': movements.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/low-stock', methods=['GET'])
@jwt_required()
def get_low_stock_items():
    try:
        branch_id = request.args.get('branch_id', type=int)
        
        query = db.session.query(Inventory).join(Product).filter(
            Inventory.current_stock <= Product.reorder_level,
            Product.is_active == True
        )
        
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
        
        low_stock_items = query.all()
        
        return jsonify({
            'low_stock_items': [item.to_dict() for item in low_stock_items],
            'count': len(low_stock_items)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/valuation', methods=['GET'])
@jwt_required()
def get_inventory_valuation():
    try:
        branch_id = request.args.get('branch_id', type=int)
        
        query = db.session.query(
            Inventory.product_id,
            Inventory.branch_id,
            Inventory.current_stock,
            Product.product_name,
            Product.cost_price,
            (Inventory.current_stock * Product.cost_price).label('total_value')
        ).join(Product).filter(Product.is_active == True)
        
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
        
        valuation_data = query.all()
        
        total_value = sum(item.total_value for item in valuation_data if item.total_value)
        
        return jsonify({
            'valuation': [
                {
                    'product_id': item.product_id,
                    'branch_id': item.branch_id,
                    'product_name': item.product_name,
                    'current_stock': item.current_stock,
                    'cost_price': float(item.cost_price) if item.cost_price else 0,
                    'total_value': float(item.total_value) if item.total_value else 0
                }
                for item in valuation_data
            ],
            'total_inventory_value': float(total_value)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

