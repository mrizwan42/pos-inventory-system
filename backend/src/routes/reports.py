from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Product, Branch
from src.models.sales import Sale, SaleItem
from src.models.inventory import Inventory, StockMovement
from datetime import datetime, date, timedelta
from sqlalchemy import func, desc

reports_bp = Blueprint('reports', __name__)

def check_permission(required_roles):
    """Check if current user has required role"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return user and user.role in required_roles

@reports_bp.route('/sales-summary', methods=['GET'])
@jwt_required()
def sales_summary():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id', type=int)
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        query = Sale.query.filter(
            func.date(Sale.sale_date) >= start_date_obj,
            func.date(Sale.sale_date) <= end_date_obj,
            Sale.payment_status != 'Refunded'
        )
        
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
        
        sales = query.all()
        
        # Calculate summary statistics
        total_sales = len(sales)
        total_revenue = sum(sale.total_amount for sale in sales)
        total_tax = sum(sale.tax_amount for sale in sales)
        total_discount = sum(sale.discount_amount for sale in sales)
        average_sale = total_revenue / total_sales if total_sales > 0 else 0
        
        # Daily breakdown
        daily_sales = {}
        for sale in sales:
            sale_date = sale.sale_date.date().isoformat()
            if sale_date not in daily_sales:
                daily_sales[sale_date] = {'count': 0, 'revenue': 0}
            daily_sales[sale_date]['count'] += 1
            daily_sales[sale_date]['revenue'] += sale.total_amount
        
        # Payment method breakdown
        payment_methods = {}
        for sale in sales:
            method = sale.payment_method
            if method not in payment_methods:
                payment_methods[method] = {'count': 0, 'amount': 0}
            payment_methods[method]['count'] += 1
            payment_methods[method]['amount'] += sale.total_amount
        
        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': {
                'total_sales': total_sales,
                'total_revenue': float(total_revenue),
                'total_tax': float(total_tax),
                'total_discount': float(total_discount),
                'average_sale': float(average_sale)
            },
            'daily_breakdown': {
                date: {
                    'count': data['count'],
                    'revenue': float(data['revenue'])
                }
                for date, data in daily_sales.items()
            },
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

@reports_bp.route('/top-products', methods=['GET'])
@jwt_required()
def top_products():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id', type=int)
        limit = request.args.get('limit', 10, type=int)
        
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Query for top selling products by quantity
        query = db.session.query(
            Product.id,
            Product.product_name,
            Product.product_code,
            func.sum(SaleItem.quantity).label('total_quantity'),
            func.sum(SaleItem.line_total).label('total_revenue'),
            func.count(SaleItem.id).label('transaction_count')
        ).join(SaleItem).join(Sale).filter(
            func.date(Sale.sale_date) >= start_date_obj,
            func.date(Sale.sale_date) <= end_date_obj,
            Sale.payment_status != 'Refunded'
        )
        
        if branch_id:
            query = query.filter(Sale.branch_id == branch_id)
        
        top_products = query.group_by(
            Product.id, Product.product_name, Product.product_code
        ).order_by(desc('total_quantity')).limit(limit).all()
        
        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'top_products': [
                {
                    'product_id': product.id,
                    'product_name': product.product_name,
                    'product_code': product.product_code,
                    'total_quantity': product.total_quantity,
                    'total_revenue': float(product.total_revenue),
                    'transaction_count': product.transaction_count
                }
                for product in top_products
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/inventory-valuation', methods=['GET'])
@jwt_required()
def inventory_valuation():
    try:
        branch_id = request.args.get('branch_id', type=int)
        
        query = db.session.query(
            Product.id,
            Product.product_name,
            Product.product_code,
            Product.cost_price,
            Product.selling_price,
            Inventory.current_stock,
            Inventory.branch_id,
            Branch.branch_name,
            (Inventory.current_stock * Product.cost_price).label('cost_value'),
            (Inventory.current_stock * Product.selling_price).label('retail_value')
        ).join(Inventory).join(Branch).filter(
            Product.is_active == True,
            Inventory.current_stock > 0
        )
        
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
        
        inventory_data = query.all()
        
        total_cost_value = sum(item.cost_value for item in inventory_data if item.cost_value)
        total_retail_value = sum(item.retail_value for item in inventory_data if item.retail_value)
        total_items = len(inventory_data)
        
        return jsonify({
            'summary': {
                'total_items': total_items,
                'total_cost_value': float(total_cost_value),
                'total_retail_value': float(total_retail_value),
                'potential_profit': float(total_retail_value - total_cost_value)
            },
            'inventory': [
                {
                    'product_id': item.id,
                    'product_name': item.product_name,
                    'product_code': item.product_code,
                    'branch_id': item.branch_id,
                    'branch_name': item.branch_name,
                    'current_stock': item.current_stock,
                    'cost_price': float(item.cost_price) if item.cost_price else 0,
                    'selling_price': float(item.selling_price) if item.selling_price else 0,
                    'cost_value': float(item.cost_value) if item.cost_value else 0,
                    'retail_value': float(item.retail_value) if item.retail_value else 0
                }
                for item in inventory_data
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/profit-loss', methods=['GET'])
@jwt_required()
def profit_loss():
    try:
        if not check_permission(['Admin']):
            return jsonify({'error': 'Unauthorized. Admin access required.'}), 403
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id', type=int)
        
        # Default to current month if no dates provided
        if not start_date:
            start_date = date.today().replace(day=1).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Calculate revenue from sales
        sales_query = Sale.query.filter(
            func.date(Sale.sale_date) >= start_date_obj,
            func.date(Sale.sale_date) <= end_date_obj,
            Sale.payment_status != 'Refunded'
        )
        
        if branch_id:
            sales_query = sales_query.filter(Sale.branch_id == branch_id)
        
        sales = sales_query.all()
        total_revenue = sum(sale.total_amount for sale in sales)
        
        # Calculate cost of goods sold (COGS)
        cogs_query = db.session.query(
            func.sum(SaleItem.quantity * Product.cost_price).label('total_cogs')
        ).join(Product).join(Sale).filter(
            func.date(Sale.sale_date) >= start_date_obj,
            func.date(Sale.sale_date) <= end_date_obj,
            Sale.payment_status != 'Refunded'
        )
        
        if branch_id:
            cogs_query = cogs_query.filter(Sale.branch_id == branch_id)
        
        cogs_result = cogs_query.first()
        total_cogs = cogs_result.total_cogs if cogs_result.total_cogs else 0
        
        # Calculate gross profit
        gross_profit = total_revenue - total_cogs
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total_revenue': float(total_revenue),
                'total_sales': len(sales)
            },
            'costs': {
                'cost_of_goods_sold': float(total_cogs)
            },
            'profit': {
                'gross_profit': float(gross_profit),
                'gross_margin_percent': float(gross_margin)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/low-stock', methods=['GET'])
@jwt_required()
def low_stock_report():
    try:
        branch_id = request.args.get('branch_id', type=int)
        
        query = db.session.query(
            Product.id,
            Product.product_name,
            Product.product_code,
            Product.reorder_level,
            Product.min_stock_level,
            Inventory.current_stock,
            Inventory.branch_id,
            Branch.branch_name
        ).join(Inventory).join(Branch).filter(
            Product.is_active == True,
            Inventory.current_stock <= Product.reorder_level
        )
        
        if branch_id:
            query = query.filter(Inventory.branch_id == branch_id)
        
        low_stock_items = query.order_by(Inventory.current_stock).all()
        
        return jsonify({
            'low_stock_items': [
                {
                    'product_id': item.id,
                    'product_name': item.product_name,
                    'product_code': item.product_code,
                    'branch_id': item.branch_id,
                    'branch_name': item.branch_name,
                    'current_stock': item.current_stock,
                    'reorder_level': item.reorder_level,
                    'min_stock_level': item.min_stock_level,
                    'shortage': item.reorder_level - item.current_stock
                }
                for item in low_stock_items
            ],
            'total_items': len(low_stock_items)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/stock-movements', methods=['GET'])
@jwt_required()
def stock_movements_report():
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        branch_id = request.args.get('branch_id', type=int)
        product_id = request.args.get('product_id', type=int)
        movement_type = request.args.get('movement_type')
        
        # Default to last 7 days if no dates provided
        if not start_date:
            start_date = (date.today() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = date.today().isoformat()
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        query = db.session.query(
            StockMovement.id,
            StockMovement.movement_type,
            StockMovement.quantity,
            StockMovement.unit_cost,
            StockMovement.reference,
            StockMovement.notes,
            StockMovement.created_at,
            Product.product_name,
            Product.product_code,
            Branch.branch_name,
            User.username
        ).join(Product).join(Branch).join(User).filter(
            func.date(StockMovement.created_at) >= start_date_obj,
            func.date(StockMovement.created_at) <= end_date_obj
        )
        
        if branch_id:
            query = query.filter(StockMovement.branch_id == branch_id)
        
        if product_id:
            query = query.filter(StockMovement.product_id == product_id)
        
        if movement_type:
            query = query.filter(StockMovement.movement_type == movement_type)
        
        movements = query.order_by(desc(StockMovement.created_at)).all()
        
        # Calculate summary by movement type
        movement_summary = {}
        for movement in movements:
            mov_type = movement.movement_type
            if mov_type not in movement_summary:
                movement_summary[mov_type] = {'count': 0, 'total_quantity': 0}
            movement_summary[mov_type]['count'] += 1
            movement_summary[mov_type]['total_quantity'] += abs(movement.quantity)
        
        return jsonify({
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'summary': movement_summary,
            'movements': [
                {
                    'id': movement.id,
                    'movement_type': movement.movement_type,
                    'quantity': movement.quantity,
                    'unit_cost': float(movement.unit_cost) if movement.unit_cost else None,
                    'reference': movement.reference,
                    'notes': movement.notes,
                    'created_at': movement.created_at.isoformat(),
                    'product_name': movement.product_name,
                    'product_code': movement.product_code,
                    'branch_name': movement.branch_name,
                    'created_by': movement.username
                }
                for movement in movements
            ],
            'total_movements': len(movements)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

