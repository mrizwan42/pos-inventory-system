#!/bin/bash

# POS & Inventory Management System Setup Script
# This script sets up the complete development environment

echo "🚀 Setting up POS & Inventory Management System..."
echo "=================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Setup Backend
echo ""
echo "📦 Setting up Backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database with sample data..."
python init_db.py

echo "✅ Backend setup complete"

# Setup Frontend
echo ""
echo "🎨 Setting up Frontend..."
cd ../frontend

# Check if pnpm is available, otherwise use npm
if command -v pnpm &> /dev/null; then
    echo "Installing frontend dependencies with pnpm..."
    pnpm install
else
    echo "Installing frontend dependencies with npm..."
    npm install
fi

echo "✅ Frontend setup complete"

# Return to root directory
cd ..

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "To start the application:"
echo ""
echo "1. Start the backend server:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python src/main.py"
echo ""
echo "2. In a new terminal, start the frontend:"
echo "   cd frontend"
echo "   pnpm run dev  # or npm run dev"
echo ""
echo "3. Open your browser and go to: http://localhost:5173"
echo ""
echo "Default login credentials:"
echo "- Admin: admin / admin123"
echo "- Cashier: cashier / cashier123"
echo "- Manager: manager / manager123"
echo ""
echo "📖 For more information, see README.md"

