# POS & Inventory Management System

A complete browser-based Point of Sale and Inventory Management System built with modern web technologies.

## 🚀 Features

### Core Modules
1. **User Authentication** - Role-based access (Admin, Cashier, Inventory Manager)
2. **Product Management** - Add/Edit/Delete products with barcode support
3. **Inventory Control** - Track stock levels, low-stock alerts
4. **POS (Point of Sale)** - Sales screen with cart, barcode scanning, discounts
5. **Customer Management** - Customer profiles, loyalty points, purchase history
6. **Supplier Management** - Supplier information and payment tracking
7. **Purchase Orders** - Create and manage purchase orders
8. **Reports** - Sales reports, inventory valuation, profit/loss analysis
9. **Settings** - System configuration for tax, currency, branches

### Technical Features
- **Responsive Design** - Works on desktop and tablet
- **Role-based Access Control** - Different permissions for different user roles
- **RESTful API** - Clean API architecture
- **JWT Authentication** - Secure token-based authentication
- **Database Integration** - SQLite for development (easily configurable for SQL Server)

## 🛠 Tech Stack

### Frontend
- **React.js** - Modern UI framework
- **Tailwind CSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **Axios** - HTTP client for API calls

### Backend
- **Flask** - Python web framework
- **SQLAlchemy** - Database ORM
- **Flask-JWT-Extended** - JWT authentication
- **Flask-CORS** - Cross-origin resource sharing
- **SQLite** - Database (development)

### Development Tools
- **Vite** - Fast build tool for frontend
- **Python Virtual Environment** - Isolated Python environment

## 📁 Project Structure

```
pos-inventory-system/
├── backend/                    # Flask backend application
│   ├── src/
│   │   ├── models/            # Database models
│   │   │   ├── user.py        # User, Branch, Category, Product, Customer, Supplier models
│   │   │   ├── inventory.py   # Inventory, StockMovement, PurchaseOrder models
│   │   │   └── sales.py       # Sale, SaleItem, SystemSetting models
│   │   ├── routes/            # API route handlers
│   │   │   ├── auth.py        # Authentication routes
│   │   │   ├── product.py     # Product management routes
│   │   │   ├── inventory.py   # Inventory management routes
│   │   │   ├── sales.py       # Sales management routes
│   │   │   ├── customer.py    # Customer management routes
│   │   │   ├── supplier.py    # Supplier management routes
│   │   │   ├── purchase.py    # Purchase order routes
│   │   │   ├── reports.py     # Reporting routes
│   │   │   ├── settings.py    # System settings routes
│   │   │   └── user.py        # User management routes
│   │   └── main.py            # Flask application entry point
│   ├── init_db.py             # Database initialization script
│   ├── requirements.txt       # Python dependencies
│   └── venv/                  # Python virtual environment
├── frontend/                  # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   ├── Layout.jsx     # Main layout component
│   │   │   └── LoadingSpinner.jsx
│   │   ├── contexts/          # React contexts
│   │   │   └── AuthContext.jsx
│   │   ├── lib/               # Utility libraries
│   │   │   └── api.js         # API client
│   │   ├── pages/             # Page components
│   │   │   ├── LoginPage.jsx  # Login page
│   │   │   ├── Dashboard.jsx  # Main dashboard
│   │   │   ├── POSPage.jsx    # Point of sale interface
│   │   │   ├── ProductsPage.jsx
│   │   │   ├── InventoryPage.jsx
│   │   │   ├── CustomersPage.jsx
│   │   │   ├── SuppliersPage.jsx
│   │   │   ├── PurchasesPage.jsx
│   │   │   ├── ReportsPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   └── App.jsx            # Main React component
│   ├── package.json           # Node.js dependencies
│   ├── vite.config.js         # Vite configuration
│   └── tailwind.config.js     # Tailwind CSS configuration
├── database_schema.sql        # SQL Server database schema
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or pnpm

### Installation

1. **Clone the repository**
   ```bash
   cd pos-inventory-system
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Initialize Database**
   ```bash
   python init_db.py
   ```

4. **Start Backend Server**
   ```bash
   python src/main.py
   ```
   Backend will run on http://localhost:5000

5. **Setup Frontend** (in a new terminal)
   ```bash
   cd frontend
   pnpm install  # or npm install
   ```

6. **Start Frontend Development Server**
   ```bash
   pnpm run dev  # or npm run dev
   ```
   Frontend will run on http://localhost:5173

### Default Login Credentials

After running the database initialization script, you can use these credentials:

- **Admin**: `admin` / `admin123`
- **Cashier**: `cashier` / `cashier123`
- **Inventory Manager**: `manager` / `manager123`

## 🗄 Database Schema

The system uses the following main entities:

### Core Tables
- **users** - System users with role-based access
- **branches** - Store locations/branches
- **categories** - Product categories
- **products** - Product catalog
- **customers** - Customer information
- **suppliers** - Supplier information

### Inventory Tables
- **inventory** - Current stock levels per branch
- **stock_movements** - Stock movement history
- **purchase_orders** - Purchase order management
- **purchase_order_items** - Purchase order line items

### Sales Tables
- **sales** - Sales transactions
- **sale_items** - Sales line items
- **loyalty_transactions** - Customer loyalty point transactions

### System Tables
- **system_settings** - System configuration
- **audit_logs** - System audit trail

## 🔧 Configuration

### Backend Configuration
- Database connection: Configured in `src/main.py`
- JWT settings: Configured in `src/main.py`
- CORS settings: Configured in `src/main.py`

### Frontend Configuration
- API base URL: Configured in `src/lib/api.js`
- Proxy settings: Configured in `vite.config.js`

## 📊 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token
- `POST /api/auth/logout` - User logout

### Products
- `GET /api/products` - List products
- `POST /api/products` - Create product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Delete product

### Inventory
- `GET /api/inventory` - List inventory
- `POST /api/inventory/movement` - Record stock movement
- `GET /api/inventory/low-stock` - Get low stock items

### Sales
- `GET /api/sales` - List sales
- `POST /api/sales` - Create sale
- `GET /api/sales/daily-summary` - Daily sales summary

### Reports
- `GET /api/reports/sales-summary` - Sales summary report
- `GET /api/reports/top-products` - Top selling products
- `GET /api/reports/inventory-valuation` - Inventory valuation

## 🎨 UI Components

### Main Pages
- **Login Page** - User authentication
- **Dashboard** - Overview with key metrics
- **POS Page** - Point of sale interface
- **Products Page** - Product management
- **Inventory Page** - Stock management
- **Customers Page** - Customer management
- **Suppliers Page** - Supplier management
- **Purchases Page** - Purchase order management
- **Reports Page** - Business reports
- **Settings Page** - System configuration

### Key Features
- Responsive design for desktop and tablet
- Real-time stock updates
- Barcode scanning support (ready for integration)
- Receipt generation
- Role-based UI elements

## 🔒 Security Features

- JWT-based authentication
- Role-based access control
- Password hashing with bcrypt
- CORS protection
- Input validation and sanitization

## 🚀 Deployment

### Production Deployment

1. **Database Setup**
   - Configure SQL Server connection in backend
   - Run database schema creation script
   - Update connection strings

2. **Backend Deployment**
   - Use production WSGI server (e.g., Gunicorn)
   - Configure environment variables
   - Set up reverse proxy (nginx)

3. **Frontend Deployment**
   - Build production bundle: `pnpm run build`
   - Deploy to web server or CDN
   - Configure API endpoints

### Environment Variables

Create `.env` files for production:

**Backend (.env)**
```
DATABASE_URL=your_database_connection_string
JWT_SECRET_KEY=your_jwt_secret_key
FLASK_ENV=production
```

**Frontend (.env)**
```
VITE_API_BASE_URL=https://your-api-domain.com
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
pnpm test
```

## 📝 Development Notes

### Current Status
- ✅ Database schema designed and implemented
- ✅ Backend API routes created
- ✅ Frontend UI components implemented
- ✅ Authentication system setup
- ⚠️ Integration testing in progress
- ⚠️ Some API endpoints need debugging

### Known Issues
1. Dashboard data loading needs debugging
2. Some API endpoints return 422 errors
3. Authentication flow needs refinement
4. Receipt printing integration pending

### Next Steps
1. Debug API endpoint issues
2. Complete integration testing
3. Add barcode scanning functionality
4. Implement receipt printing
5. Add data export features
6. Performance optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation
- Review the API endpoints
- Check the console for error messages
- Verify database initialization completed successfully

## 🔄 Version History

- **v1.0.0** - Initial release with core POS and inventory features
- Complete backend API implementation
- React frontend with responsive design
- Role-based authentication system
- Database schema for SQL Server compatibility

