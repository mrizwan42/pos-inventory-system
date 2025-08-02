from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Product, Branch, Customer
from src.models.sales import Sale, SaleItem, LoyaltyTransaction, SystemSetting
from src.models.inventory import Inventory, StockMovement
from datetime import datetime, date
from sqlalchemy import func
import uuid

sales_bp = Blueprint('sales', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

def generate_sale_number():
    """Generate unique sale number"""
    today = datetime.now().strftime('%Y%m%d')
    return f"SALE-{today}-{str(uuid.uuid4())[:8].upper()}"

def update_inventory_after_sale(sale_items, branch_id, cashier_id):
    """Update inventory after a sale"""
    for item in sale_items:
        # Get inventory record
        inventory = Inventory.query.filter_by(
            product_id=item['product_id'],
            branch_id=branch_id
        ).first()
        
        if inventory:
            # Update stock
            inventory.current_stock -= item['quantity']
            inventory.last_updated = datetime.utcnow()
            
            # Create stock movement
            movement = StockMovement(
                product_id=item['product_id'],
                branch_id=branch_id,
                movement_type='OUT',
                quantity=-item['quantity'],
                reference=f"SALE-{item.get('sale_id', '')}",
                notes=f"Sale transaction",
                created_by=cashier_id
            )
            db.session.add(movement)

@sales_bp.route('/', methods=['GET'])
@jwt_required()
def get_sales():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        branch_id = request.args.get('branch_id', type=int)
        cashier_id = request.args.get('cashier_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        payment_method = request.args.get('payment_method')
        
        query = Sale.query
        
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
        
        if cashier_id:
            query = query.filter(Sale.cashier_id == cashier_id)
        
        if start_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(func.date(Sale.sale_date) >= start_date_obj)
        
        if end_date:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(func.date(Sale.sale_date) <= end_date_obj)
        
        if payment_method:
            query = query.filter(Sale.payment_method == payment_method)
        
        sales = query.order_by(Sale.sale_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'sales': [sale.to_dict() for sale in sales.items],
            'total': sales.total,
            'pages': sales.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/<int:sale_id>', methods=['GET'])
@jwt_required()
def get_sale(sale_id):
    try:
        sale = Sale.query.get(sale_id)
        
        if not sale:
            return jsonify({'error': 'Sale not found'}), 404
        
        sale_dict = sale.to_dict()
        sale_dict['items'] = [item.to_dict() for item in sale.items]
        
        return jsonify({'sale': sale_dict}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/', methods=['POST'])
@jwt_required()
def create_sale():
    try:
        if not check_permission(['Admin', 'Cashier']):
            return jsonify({'error': 'Unauthorized. Admin or Cashier access required.'}), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['branch_id', 'items', 'payment_method', 'total_amount']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        if not data['items']:
            return jsonify({'error': 'Sale must have at least one item'}), 400
        
        branch_id = data['branch_id']
        customer_id = data.get('customer_id')
        items_data = data['items']
        payment_method = data['payment_method']
        discount_amount = data.get('discount_amount', 0)
        notes = data.get('notes', '')
        
        # Validate branch exists
        branch = Branch.query.get(branch_id)
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
        
        # Validate customer exists (if provided)
        customer = None
        if customer_id:
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
        
        # Validate items and check stock availability
        validated_items = []
        sub_total = 0
        total_tax = 0
        
        for item_data in items_data:
            product_id = item_data.get('product_id')
            quantity = item_data.get('quantity', 0)
            unit_price = item_data.get('unit_price')
            item_discount = item_data.get('discount_amount', 0)
            
            if not product_id or quantity <= 0:
                return jsonify({'error': 'Invalid item data'}), 400
            
            # Get product
            product = Product.query.get(product_id)
            if not product or not product.is_active:
                return jsonify({'error': f'Product {product_id} not found or inactive'}), 404
            
            # Use product selling price if unit_price not provided
            if unit_price is None:
                unit_price = float(product.selling_price)
            
            # Check stock availability
            inventory = Inventory.query.filter_by(
                product_id=product_id,
                branch_id=branch_id
            ).first()
            
            if not inventory or inventory.available_stock < quantity:
                return jsonify({'error': f'Insufficient stock for product {product.product_name}'}), 400
            
            # Calculate line totals
            line_subtotal = unit_price * quantity - item_discount
            tax_amount = line_subtotal * (float(product.tax_rate) / 100)
            line_total = line_subtotal + tax_amount
            
            validated_items.append({
                'product_id': product_id,
                'quantity': quantity,
                'unit_price': unit_price,
                'discount_amount': item_discount,
                'tax_amount': tax_amount,
                'line_total': line_total
            })
            
            sub_total += line_subtotal
            total_tax += tax_amount
        
        # Calculate totals
        total_amount = sub_total + total_tax - discount_amount
        
        # Create sale
        sale = Sale(
            sale_number=generate_sale_number(),
            customer_id=customer_id,
            branch_id=branch_id,
            cashier_id=get_jwt_identity(),
            sub_total=sub_total,
            tax_amount=total_tax,
            discount_amount=discount_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            notes=notes
        )
        
        db.session.add(sale)
        db.session.flush()  # Get sale ID
        
        # Create sale items
        for item_data in validated_items:
            sale_item = SaleItem(
                sale_id=sale.id,
                **item_data
            )
            db.session.add(sale_item)
        
        # Update inventory
        update_inventory_after_sale(validated_items, branch_id, get_jwt_identity())
        
        # Handle loyalty points (if customer provided)
        if customer:
            loyalty_rate_setting = SystemSetting.query.filter_by(setting_key='LOYALTY_POINTS_RATE').first()
            loyalty_rate = float(loyalty_rate_setting.setting_value) if loyalty_rate_setting else 1.0
            
            points_earned = int(total_amount * loyalty_rate)
            if points_earned > 0:
                customer.loyalty_points += points_earned
                customer.total_purchases += total_amount
                
                # Create loyalty transaction
                loyalty_transaction = LoyaltyTransaction(
                    customer_id=customer_id,
                    sale_id=sale.id,
                    transaction_type='EARNED',
                    points=points_earned,
                    description=f'Points earned from sale {sale.sale_number}'
                )
                db.session.add(loyalty_transaction)
        
        db.session.commit()
        
        # Return sale with items
        sale_dict = sale.to_dict()
        sale_dict['items'] = [item.to_dict() for item in sale.items]
        
        return jsonify({
            'message': 'Sale created successfully',
            'sale': sale_dict
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/<int:sale_id>/refund', methods=['POST'])
@jwt_required()
def refund_sale(sale_id):
    try:
        if not check_permission(['Admin', 'Cashier']):
            return jsonify({'error': 'Unauthorized. Admin or Cashier access required.'}), 403
        
        sale = Sale.query.get(sale_id)
        if not sale:
            return jsonify({'error': 'Sale not found'}), 404
        
        if sale.payment_status == 'Refunded':
            return jsonify({'error': 'Sale already refunded'}), 400
        
        data = request.get_json()
        refund_reason = data.get('reason', 'Customer request')
        
        # Update sale status
        sale.payment_status = 'Refunded'
        sale.notes = f"{sale.notes or ''} | REFUNDED: {refund_reason}"
        
        # Restore inventory
        for item in sale.items:
            inventory = Inventory.query.filter_by(
                product_id=item.product_id,
                branch_id=sale.branch_id
            ).first()
            
            if inventory:
                inventory.current_stock += item.quantity
                inventory.last_updated = datetime.utcnow()
                
                # Create stock movement
                movement = StockMovement(
                    product_id=item.product_id,
                    branch_id=sale.branch_id,
                    movement_type='IN',
                    quantity=item.quantity,
                    reference=f"REFUND-{sale.sale_number}",
                    notes=f"Refund for sale {sale.sale_number}",
                    created_by=get_jwt_identity()
                )
                db.session.add(movement)
        
        # Handle loyalty points refund
        if sale.customer_id:
            customer = Customer.query.get(sale.customer_id)
            if customer:
                # Find loyalty points earned from this sale
                loyalty_transaction = LoyaltyTransaction.query.filter_by(
                    customer_id=sale.customer_id,
                    sale_id=sale.id,
                    transaction_type='EARNED'
                ).first()
                
                if loyalty_transaction:
                    # Deduct points
                    customer.loyalty_points -= loyalty_transaction.points
                    customer.total_purchases -= sale.total_amount
                    
                    # Create refund loyalty transaction
                    refund_loyalty = LoyaltyTransaction(
                        customer_id=sale.customer_id,
                        sale_id=sale.id,
                        transaction_type='ADJUSTED',
                        points=-loyalty_transaction.points,
                        description=f'Points deducted for refunded sale {sale.sale_number}'
                    )
                    db.session.add(refund_loyalty)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Sale refunded successfully',
            'sale': sale.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/daily-summary', methods=['GET'])
@jwt_required()
def get_daily_summary():
    try:
        target_date = request.args.get('date', date.today().isoformat())
        branch_id = request.args.get('branch_id', type=int)
        
        target_date_obj = datetime.strptime(target_date, '%Y-%m-%d').date()
        
        query = Sale.query.filter(
            func.date(Sale.sale_date) == target_date_obj,
            Sale.payment_status != 'Refunded'
        )
        
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
        
        sales = query.all()
        
        # Calculate summary
        total_sales = len(sales)
        total_revenue = sum(sale.total_amount for sale in sales)
        total_tax = sum(sale.tax_amount for sale in sales)
        total_discount = sum(sale.discount_amount for sale in sales)
        
        # Payment method breakdown
        payment_methods = {}
        for sale in sales:
            method = sale.payment_method
            if method not in payment_methods:
                payment_methods[method] = {'count': 0, 'amount': 0}
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += sale.total_amount
        
        return jsonify({
            'date': target_date,
            'total_sales': total_sales,
            'total_revenue': float(total_revenue),
            'total_tax': float(total_tax),
            'total_discount': float(total_discount),
            'payment_methods': {
                method: {
                    'count': data['count'],
                    'amount': float(data['amount'])
                }
                for method, data in payment_methods.items()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@sales_bp.route('/receipt/<int:sale_id>', methods=['GET'])
@jwt_required()
def get_receipt(sale_id):
    try:
        sale = Sale.query.get(sale_id)
        
        if not sale:
            return jsonify({'error': 'Sale not found'}), 404
        
        # Get company settings
        company_name = SystemSetting.query.filter_by(setting_key='COMPANY_NAME').first()
        company_address = SystemSetting.query.filter_by(setting_key='COMPANY_ADDRESS').first()
        company_phone = SystemSetting.query.filter_by(setting_key='COMPANY_PHONE').first()
        receipt_footer = SystemSetting.query.filter_by(setting_key='RECEIPT_FOOTER').first()
        
        receipt_data = {
            'sale': sale.to_dict(),
            'items': [item.to_dict() for item in sale.items],
            'company': {
                'name': company_name.setting_value if company_name else 'POS System',
                'address': company_address.setting_value if company_address else '',
                'phone': company_phone.setting_value if company_phone else '',
                'footer': receipt_footer.setting_value if receipt_footer else 'Thank you!'
            }
        }
        
        return jsonify({'receipt': receipt_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

