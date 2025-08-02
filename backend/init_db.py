#!/usr/bin/env python3
"""
Database initialization script for POS Inventory System
Creates tables and inserts initial data
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import db, User, Branch, Category, Product, Supplier, Customer
from src.models.inventory import Inventory, StockMovement, PurchaseOrder
from src.models.sales import Sale, SaleItem, SystemSetting
from src.main import app

def init_database():
    """Initialize database with tables and sample data"""
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables
        db.create_all()
        
        print("Inserting initial data...")
        
        # Create default branch
        if not Branch.query.first():
            main_branch = Branch(
                branch_name="Main Store",
                address="123 Main Street, City, State 12345",
                phone="(555) 123-4567",
                email="main@posstore.com",
                is_active=True
            )
            db.session.add(main_branch)
            db.session.commit()
            print("✓ Created main branch")
        
        # Create admin user
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@posstore.com',
                first_name='System',
                last_name='Administrator',
                role='Admin',
                is_active=True
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✓ Created admin user (admin/admin123)")
        
        # Create sample cashier user
        if not User.query.filter_by(username='cashier').first():
            cashier_user = User(
                username='cashier',
                email='cashier@posstore.com',
                first_name='John',
                last_name='Cashier',
                role='Cashier',
                is_active=True
            )
            cashier_user.set_password('cashier123')
            db.session.add(cashier_user)
            db.session.commit()
            print("✓ Created cashier user (cashier/cashier123)")
        
        # Create sample inventory manager user
        if not User.query.filter_by(username='manager').first():
            manager_user = User(
                username='manager',
                email='manager@posstore.com',
                first_name='Jane',
                last_name='Manager',
                role='InventoryManager',
                is_active=True
            )
            manager_user.set_password('manager123')
            db.session.add(manager_user)
            db.session.commit()
            print("✓ Created inventory manager user (manager/manager123)")
        
        # Create sample categories
        categories_data = [
            {"name": "Electronics", "description": "Electronic devices and accessories"},
            {"name": "Clothing", "description": "Apparel and fashion items"},
            {"name": "Food & Beverages", "description": "Food items and drinks"},
            {"name": "Books", "description": "Books and educational materials"},
            {"name": "Home & Garden", "description": "Home improvement and garden supplies"},
        ]
        
        for cat_data in categories_data:
            if not Category.query.filter_by(category_name=cat_data["name"]).first():
                category = Category(
                    category_name=cat_data["name"],
                    description=cat_data["description"],
                    is_active=True
                )
                db.session.add(category)
        
        db.session.commit()
        print("✓ Created sample categories")
        
        # Create sample products
        electronics_cat = Category.query.filter_by(category_name="Electronics").first()
        clothing_cat = Category.query.filter_by(category_name="Clothing").first()
        food_cat = Category.query.filter_by(category_name="Food & Beverages").first()
        
        products_data = [
            {
                "code": "ELE001",
                "name": "Wireless Bluetooth Headphones",
                "description": "High-quality wireless headphones with noise cancellation",
                "category_id": electronics_cat.id if electronics_cat else None,
                "unit_of_measure": "pcs",
                "cost_price": 45.00,
                "selling_price": 79.99,
                "barcode": "1234567890123",
                "tax_rate": 8.5
            },
            {
                "code": "ELE002", 
                "name": "Smartphone Case",
                "description": "Protective case for smartphones",
                "category_id": electronics_cat.id if electronics_cat else None,
                "unit_of_measure": "pcs",
                "cost_price": 8.00,
                "selling_price": 19.99,
                "barcode": "1234567890124",
                "tax_rate": 8.5
            },
            {
                "code": "CLO001",
                "name": "Cotton T-Shirt",
                "description": "100% cotton comfortable t-shirt",
                "category_id": clothing_cat.id if clothing_cat else None,
                "unit_of_measure": "pcs",
                "cost_price": 12.00,
                "selling_price": 24.99,
                "barcode": "1234567890125",
                "tax_rate": 6.0
            },
            {
                "code": "FOO001",
                "name": "Premium Coffee Beans",
                "description": "Organic premium coffee beans 1lb bag",
                "category_id": food_cat.id if food_cat else None,
                "unit_of_measure": "lbs",
                "cost_price": 8.50,
                "selling_price": 16.99,
                "barcode": "1234567890126",
                "tax_rate": 0.0
            },
            {
                "code": "FOO002",
                "name": "Energy Drink",
                "description": "Natural energy drink 16oz can",
                "category_id": food_cat.id if food_cat else None,
                "unit_of_measure": "cans",
                "cost_price": 1.25,
                "selling_price": 2.99,
                "barcode": "1234567890127",
                "tax_rate": 0.0
            }
        ]
        
        main_branch = Branch.query.first()
        
        for prod_data in products_data:
            if not Product.query.filter_by(product_code=prod_data["code"]).first():
                product = Product(
                    product_code=prod_data["code"],
                    product_name=prod_data["name"],
                    description=prod_data["description"],
                    category_id=prod_data["category_id"],
                    unit_of_measure=prod_data["unit_of_measure"],
                    cost_price=prod_data["cost_price"],
                    selling_price=prod_data["selling_price"],
                    barcode=prod_data["barcode"],
                    tax_rate=prod_data["tax_rate"],
                    is_active=True
                )
                db.session.add(product)
                db.session.flush()  # Get the product ID
                
                # Create inventory record for main branch
                inventory = Inventory(
                    product_id=product.id,
                    branch_id=main_branch.id,
                    current_stock=50,  # Initial stock
                    reserved_stock=0
                )
                db.session.add(inventory)
        
        db.session.commit()
        print("✓ Created sample products with inventory")
        
        # Create sample customer
        if not Customer.query.filter_by(email='john.doe@email.com').first():
            customer = Customer(
                first_name='John',
                last_name='Doe',
                email='john.doe@email.com',
                phone='(555) 987-6543',
                address='456 Customer St, City, State 12345',
                loyalty_points=150,
                is_active=True
            )
            db.session.add(customer)
            db.session.commit()
            print("✓ Created sample customer")
        
        # Create sample supplier
        if not Supplier.query.filter_by(supplier_name='Tech Supplies Inc').first():
            supplier = Supplier(
                supplier_name='Tech Supplies Inc',
                contact_person='Mike Johnson',
                email='mike@techsupplies.com',
                phone='(555) 111-2222',
                address='789 Supplier Ave, City, State 12345',
                payment_terms='Net 30',
                is_active=True
            )
            db.session.add(supplier)
            db.session.commit()
            print("✓ Created sample supplier")
        
        # Create system settings
        settings_data = [
            {"key": "tax_rate", "value": "8.5", "description": "Default tax rate percentage"},
            {"key": "currency", "value": "USD", "description": "System currency"},
            {"key": "receipt_footer", "value": "Thank you for your business!", "description": "Receipt footer message"},
            {"key": "low_stock_threshold", "value": "10", "description": "Default low stock threshold"},
        ]
        
        admin_user = User.query.filter_by(username='admin').first()
        
        for setting_data in settings_data:
            if not SystemSetting.query.filter_by(setting_key=setting_data["key"]).first():
                setting = SystemSetting(
                    setting_key=setting_data["key"],
                    setting_value=setting_data["value"],
                    description=setting_data["description"],
                    updated_by=admin_user.id if admin_user else None
                )
                db.session.add(setting)
        
        db.session.commit()
        print("✓ Created system settings")
        
        print("\n🎉 Database initialization completed successfully!")
        print("\nDefault login credentials:")
        print("Admin: admin / admin123")
        print("Cashier: cashier / cashier123") 
        print("Manager: manager / manager123")

if __name__ == '__main__':
    init_database()

