import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Import all models
from src.models.user import db, User, Branch, Category, Supplier, Product, Customer
from src.models.inventory import Inventory, StockMovement, PurchaseOrder, PurchaseOrderItem
from src.models.sales import Sale, SaleItem, LoyaltyTransaction, SystemSetting, AuditLog

# Import all routes
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.product import product_bp
from src.routes.inventory import inventory_bp
from src.routes.sales import sales_bp
from src.routes.customer import customer_bp
from src.routes.supplier import supplier_bp
from src.routes.purchase import purchase_bp
from src.routes.reports import reports_bp
from src.routes.settings import settings_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = 'pos-inventory-secret-key-change-in-production'
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize JWT
jwt = JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(product_bp, url_prefix='/api/products')
app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
app.register_blueprint(sales_bp, url_prefix='/api/sales')
app.register_blueprint(customer_bp, url_prefix='/api/customers')
app.register_blueprint(supplier_bp, url_prefix='/api/suppliers')
app.register_blueprint(purchase_bp, url_prefix='/api/purchases')
app.register_blueprint(reports_bp, url_prefix='/api/reports')
app.register_blueprint(settings_bp, url_prefix='/api/settings')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables and seed data
with app.app_context():
    db.create_all()
    
    # Create default admin user if not exists
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@pos.com',
            first_name='System',
            last_name='Administrator',
            role='Admin'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
    
    # Create default branch if not exists
    main_branch = Branch.query.filter_by(branch_name='Main Store').first()
    if not main_branch:
        main_branch = Branch(
            branch_name='Main Store',
            address='123 Main Street, City, State 12345',
            phone='(555) 123-4567',
            email='main@pos.com'
        )
        db.session.add(main_branch)
    
    # Create default categories if not exist
    if Category.query.count() == 0:
        categories = [
            Category(category_name='Electronics', description='Electronic devices and accessories'),
            Category(category_name='Clothing', description='Apparel and fashion items'),
            Category(category_name='Food & Beverages', description='Food and drink products'),
            Category(category_name='Home & Garden', description='Home improvement and garden supplies'),
            Category(category_name='Books & Media', description='Books, movies, and media products')
        ]
        for category in categories:
            db.session.add(category)
    
    # Create default system settings if not exist
    if SystemSetting.query.count() == 0:
        settings = [
            SystemSetting(setting_key='TAX_RATE', setting_value='10.00', description='Default tax rate percentage'),
            SystemSetting(setting_key='CURRENCY', setting_value='USD', description='System currency'),
            SystemSetting(setting_key='LOYALTY_POINTS_RATE', setting_value='1.00', description='Points earned per dollar spent'),
            SystemSetting(setting_key='LOW_STOCK_THRESHOLD', setting_value='10', description='Default low stock alert threshold'),
            SystemSetting(setting_key='RECEIPT_FOOTER', setting_value='Thank you for your business!', description='Receipt footer message'),
            SystemSetting(setting_key='COMPANY_NAME', setting_value='Your Company Name', description='Company name for receipts'),
            SystemSetting(setting_key='COMPANY_ADDRESS', setting_value='123 Main St, City, State 12345', description='Company address'),
            SystemSetting(setting_key='COMPANY_PHONE', setting_value='(555) 123-4567', description='Company phone number')
        ]
        for setting in settings:
            db.session.add(setting)
    
    db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

