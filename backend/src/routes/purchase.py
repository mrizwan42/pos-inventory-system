from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Product, Branch, Supplier
from src.models.inventory import PurchaseOrder, PurchaseOrderItem, Inventory, StockMovement
from datetime import datetime, date
import uuid

purchase_bp = Blueprint('purchase', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

def generate_po_number():
    """Generate unique purchase order number"""
    today = datetime.now().strftime('%Y%m%d')
    return f"PO-{today}-{str(uuid.uuid4())[:8].upper()}"

@purchase_bp.route('/', methods=['GET'])
@jwt_required()
def get_purchase_orders():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        supplier_id = request.args.get('supplier_id', type=int)
        branch_id = request.args.get('branch_id', type=int)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = PurchaseOrder.query
        
        if supplier_id:
            query = query.filter(PurchaseOrder.supplier_id == supplier_id)
        
        if branch_id:
            query = query.filter(PurchaseOrder.branch_id == branch_id)
        
        if status:
            query = query.filter(PurchaseOrder.status == status)
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(PurchaseOrder.order_date >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(PurchaseOrder.order_date <= end_date_obj)
        
        purchase_orders = query.order_by(PurchaseOrder.order_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'purchase_orders': [po.to_dict() for po in purchase_orders.items],
            'total': purchase_orders.total,
            'pages': purchase_orders.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/<int:po_id>', methods=['GET'])
@jwt_required()
def get_purchase_order(po_id):
    try:
        purchase_order = PurchaseOrder.query.get(po_id)
        
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        po_dict = purchase_order.to_dict()
        po_dict['items'] = [item.to_dict() for item in purchase_order.items]
        
        return jsonify({'purchase_order': po_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/', methods=['POST'])
@jwt_required()
def create_purchase_order():
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['supplier_id', 'branch_id', 'items']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        if not data['items']:
            return jsonify({'error': 'Purchase order must have at least one item'}), 400
        
        supplier_id = data['supplier_id']
        branch_id = data['branch_id']
        items_data = data['items']
        expected_delivery_date = data.get('expected_delivery_date')
        notes = data.get('notes', '')
        
        # Validate supplier and branch exist
        supplier = Supplier.query.get(supplier_id)
        if not supplier or not supplier.is_active:
            return jsonify({'error': 'Supplier not found or inactive'}), 404
        
        branch = Branch.query.get(branch_id)
        if not branch or not branch.is_active:
            return jsonify({'error': 'Branch not found or inactive'}), 404
        
        # Parse expected delivery date if provided
        expected_delivery_date_obj = None
        if expected_delivery_date:
            try:
                expected_delivery_date_obj = datetime.strptime(expected_delivery_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate items
        validated_items = []
        sub_total = 0
        
        for item_data in items_data:
            product_id = item_data.get('product_id')
            ordered_quantity = item_data.get('ordered_quantity', 0)
            unit_cost = item_data.get('unit_cost', 0)
            
            if not product_id or ordered_quantity <= 0 or unit_cost <= 0:
                return jsonify({'error': 'Invalid item data'}), 400
            
            # Validate product exists
            product = Product.query.get(product_id)
            if not product or not product.is_active:
                return jsonify({'error': f'Product {product_id} not found or inactive'}), 404
            
            line_total = unit_cost * ordered_quantity
            
            validated_items.append({
                'product_id': product_id,
                'ordered_quantity': ordered_quantity,
                'unit_cost': unit_cost,
                'line_total': line_total
            })
            
            sub_total += line_total
        
        # Calculate totals (assuming no tax for simplicity, can be enhanced)
        tax_amount = 0
        total_amount = sub_total + tax_amount
        
        # Create purchase order
        purchase_order = PurchaseOrder(
            po_number=generate_po_number(),
            supplier_id=supplier_id,
            branch_id=branch_id,
            expected_delivery_date=expected_delivery_date_obj,
            sub_total=sub_total,
            tax_amount=tax_amount,
            total_amount=total_amount,
            notes=notes,
            created_by=get_jwt_identity()
        )
        
        db.session.add(purchase_order)
        db.session.flush()  # Get PO ID
        
        # Create purchase order items
        for item_data in validated_items:
            po_item = PurchaseOrderItem(
                purchase_order_id=purchase_order.id,
                **item_data
            )
            db.session.add(po_item)
        
        db.session.commit()
        
        # Return PO with items
        po_dict = purchase_order.to_dict()
        po_dict['items'] = [item.to_dict() for item in purchase_order.items]
        
        return jsonify({
            'message': 'Purchase order created successfully',
            'purchase_order': po_dict
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/<int:po_id>', methods=['PUT'])
@jwt_required()
def update_purchase_order(po_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        purchase_order = PurchaseOrder.query.get(po_id)
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if purchase_order.status in ['Received', 'Cancelled']:
            return jsonify({'error': 'Cannot update received or cancelled purchase order'}), 400
        
        data = request.get_json()
        
        # Parse expected delivery date if provided
        if data.get('expected_delivery_date'):
            try:
                data['expected_delivery_date'] = datetime.strptime(data['expected_delivery_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Update purchase order fields
        updatable_fields = ['expected_delivery_date', 'status', 'notes']
        
        for field in updatable_fields:
            if field in data:
                setattr(purchase_order, field, data[field])
        
        purchase_order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order updated successfully',
            'purchase_order': purchase_order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/<int:po_id>/receive', methods=['POST'])
@jwt_required()
def receive_purchase_order(po_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        purchase_order = PurchaseOrder.query.get(po_id)
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if purchase_order.status != 'Approved':
            return jsonify({'error': 'Purchase order must be approved before receiving'}), 400
        
        data = request.get_json()
        received_items = data.get('items', [])
        
        if not received_items:
            return jsonify({'error': 'No items to receive'}), 400
        
        # Process received items
        for received_item in received_items:
            item_id = received_item.get('item_id')
            received_quantity = received_item.get('received_quantity', 0)
            
            if received_quantity <= 0:
                continue
            
            # Get purchase order item
            po_item = PurchaseOrderItem.query.get(item_id)
            if not po_item or po_item.purchase_order_id != po_id:
                return jsonify({'error': f'Invalid item ID: {item_id}'}), 400
            
            # Update received quantity
            po_item.received_quantity += received_quantity
            
            # Update inventory
            inventory = Inventory.query.filter_by(
                product_id=po_item.product_id,
                branch_id=purchase_order.branch_id
            ).first()
            
            if not inventory:
                inventory = Inventory(
                    product_id=po_item.product_id,
                    branch_id=purchase_order.branch_id,
                    current_stock=0
                )
                db.session.add(inventory)
            
            inventory.current_stock += received_quantity
            inventory.last_updated = datetime.utcnow()
            
            # Create stock movement
            movement = StockMovement(
                product_id=po_item.product_id,
                branch_id=purchase_order.branch_id,
                movement_type='IN',
                quantity=received_quantity,
                unit_cost=po_item.unit_cost,
                reference=purchase_order.po_number,
                notes=f"Received from PO {purchase_order.po_number}",
                created_by=get_jwt_identity()
            )
            db.session.add(movement)
        
        # Check if all items are fully received
        all_received = all(
            item.received_quantity >= item.ordered_quantity 
            for item in purchase_order.items
        )
        
        if all_received:
            purchase_order.status = 'Received'
        
        purchase_order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Items received successfully',
            'purchase_order': purchase_order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/<int:po_id>/approve', methods=['POST'])
@jwt_required()
def approve_purchase_order(po_id):
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        purchase_order = PurchaseOrder.query.get(po_id)
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if purchase_order.status != 'Pending':
            return jsonify({'error': 'Only pending purchase orders can be approved'}), 400
        
        purchase_order.status = 'Approved'
        purchase_order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order approved successfully',
            'purchase_order': purchase_order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@purchase_bp.route('/<int:po_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_purchase_order(po_id):
    try:
        if not check_permission(['Admin', 'InventoryManager']):
            return jsonify({'error': 'Unauthorized. Admin or Inventory Manager access required.'}), 403
        
        purchase_order = PurchaseOrder.query.get(po_id)
        if not purchase_order:
            return jsonify({'error': 'Purchase order not found'}), 404
        
        if purchase_order.status in ['Received', 'Cancelled']:
            return jsonify({'error': 'Cannot cancel received or already cancelled purchase order'}), 400
        
        data = request.get_json()
        reason = data.get('reason', 'Cancelled by user')
        
        purchase_order.status = 'Cancelled'
        purchase_order.notes = f"{purchase_order.notes or ''} | CANCELLED: {reason}"
        purchase_order.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Purchase order cancelled successfully',
            'purchase_order': purchase_order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

