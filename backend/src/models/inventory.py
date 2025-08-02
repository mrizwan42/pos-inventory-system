from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Inventory(db.Model):
    __tablename__ = 'inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    current_stock = db.Column(db.Integer, nullable=False, default=0)
    reserved_stock = db.Column(db.Integer, default=0)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='inventory_records')
    branch = db.relationship('Branch', backref='inventory_records')

    # Unique constraint
    __table_args__ = (db.UniqueConstraint('product_id', 'branch_id', name='unique_product_branch'),)

    @property
    def available_stock(self):
        return self.current_stock - self.reserved_stock

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'branch_id': self.branch_id,
            'current_stock': self.current_stock,
            'reserved_stock': self.reserved_stock,
            'available_stock': self.available_stock,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'product': self.product.to_dict() if self.product else None,
            'branch': self.branch.to_dict() if self.branch else None
        }

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    movement_type = db.Column(db.String(20), nullable=False)  # IN, OUT, TRANSFER, ADJUSTMENT
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Numeric(10, 2))
    reference = db.Column(db.String(100))
    notes = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    product = db.relationship('Product', backref='stock_movements')
    branch = db.relationship('Branch', backref='stock_movements')
    user = db.relationship('User', backref='stock_movements')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'branch_id': self.branch_id,
            'movement_type': self.movement_type,
            'quantity': self.quantity,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'reference': self.reference,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'product': self.product.to_dict() if self.product else None,
            'branch': self.branch.to_dict() if self.branch else None,
            'user': self.user.to_dict() if self.user else None
        }

class PurchaseOrder(db.Model):
    __tablename__ = 'purchase_orders'
    
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_delivery_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Pending')  # Pending, Approved, Received, Cancelled
    sub_total = db.Column(db.Numeric(12, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(12, 2), default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    notes = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier = db.relationship('Supplier', backref='purchase_orders')
    branch = db.relationship('Branch', backref='purchase_orders')
    user = db.relationship('User', backref='purchase_orders')

    def to_dict(self):
        return {
            'id': self.id,
            'po_number': self.po_number,
            'supplier_id': self.supplier_id,
            'branch_id': self.branch_id,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'expected_delivery_date': self.expected_delivery_date.isoformat() if self.expected_delivery_date else None,
            'status': self.status,
            'sub_total': float(self.sub_total) if self.sub_total else 0,
            'tax_amount': float(self.tax_amount) if self.tax_amount else 0,
            'total_amount': float(self.total_amount) if self.total_amount else 0,
            'notes': self.notes,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'supplier': self.supplier.to_dict() if self.supplier else None,
            'branch': self.branch.to_dict() if self.branch else None,
            'user': self.user.to_dict() if self.user else None
        }

class PurchaseOrderItem(db.Model):
    __tablename__ = 'purchase_order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    ordered_quantity = db.Column(db.Integer, nullable=False)
    received_quantity = db.Column(db.Integer, default=0)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=False)
    line_total = db.Column(db.Numeric(12, 2), nullable=False)

    # Relationships
    purchase_order = db.relationship('PurchaseOrder', backref='items')
    product = db.relationship('Product', backref='purchase_order_items')

    def to_dict(self):
        return {
            'id': self.id,
            'purchase_order_id': self.purchase_order_id,
            'product_id': self.product_id,
            'ordered_quantity': self.ordered_quantity,
            'received_quantity': self.received_quantity,
            'unit_cost': float(self.unit_cost) if self.unit_cost else 0,
            'line_total': float(self.line_total) if self.line_total else 0,
            'product': self.product.to_dict() if self.product else None
        }

