# Troubleshooting Guide

This guide helps resolve common issues you might encounter while setting up or running the POS & Inventory Management System.

## 🚨 Common Issues

### 1. Backend Server Won't Start

**Problem**: `ModuleNotFoundError` when starting the backend server

**Solution**:
```bash
cd backend
source venv/bin/activate  # Make sure virtual environment is activated
pip install -r requirements.txt
```

### 2. Database Initialization Fails

**Problem**: Errors during `python init_db.py`

**Solutions**:
- Make sure you're in the backend directory
- Ensure virtual environment is activated
- Check if SQLite is available (usually comes with Python)

```bash
cd backend
source venv/bin/activate
python init_db.py
```

### 3. Frontend Won't Start

**Problem**: `npm` or `pnpm` command not found

**Solutions**:
- Install Node.js from https://nodejs.org/
- If using pnpm, install it: `npm install -g pnpm`
- Alternative: Use npm instead of pnpm

```bash
cd frontend
npm install  # if pnpm is not available
npm run dev
```

### 4. API Connection Issues

**Problem**: Frontend can't connect to backend (CORS errors, 404s)

**Solutions**:
1. Ensure backend server is running on port 5000
2. Check if proxy is configured in `vite.config.js`
3. Verify API base URL in `src/lib/api.js`

**Check backend is running**:
```bash
curl http://localhost:5000/api/auth/login
```

### 5. Login Issues

**Problem**: Login form clears but doesn't redirect to dashboard

**Current Status**: This is a known issue being debugged

**Workarounds**:
1. Check browser console for error messages
2. Verify database was initialized properly
3. Check backend logs for API errors

**Debug steps**:
```bash
# Check if admin user exists in database
cd backend
source venv/bin/activate
python -c "
from src.main import app
from src.models.user import User
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    print('Admin user found:', admin is not None)
    if admin:
        print('Admin details:', admin.username, admin.email)
"
```

### 6. Database Schema Issues

**Problem**: Table doesn't exist errors

**Solution**: Re-run database initialization
```bash
cd backend
source venv/bin/activate
rm -f instance/database.db  # Remove existing database
python init_db.py  # Recreate with fresh data
```

### 7. Port Already in Use

**Problem**: `Address already in use` error

**Solutions**:
```bash
# Find process using port 5000 (backend)
lsof -i :5000
kill -9 <PID>

# Find process using port 5173 (frontend)
lsof -i :5173
kill -9 <PID>
```

### 8. Permission Denied Errors

**Problem**: Permission errors when running scripts

**Solution**:
```bash
chmod +x setup.sh
# Or run with explicit interpreter
bash setup.sh
```

## 🔧 Development Issues

### API Endpoints Returning 422 Errors

**Current Status**: Some endpoints need debugging

**Debug approach**:
1. Check backend logs for detailed error messages
2. Verify request payload format
3. Check database constraints

**Example debugging**:
```bash
# Check backend logs
cd backend
source venv/bin/activate
python src/main.py  # Watch console output
```

### Frontend Build Issues

**Problem**: Build fails with dependency errors

**Solutions**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install  # Fresh install
```

### Database Connection Issues

**Problem**: SQLAlchemy connection errors

**Solutions**:
1. Check if database file exists: `backend/instance/database.db`
2. Verify file permissions
3. Re-run initialization script

## 🛠 Advanced Debugging

### Enable Debug Mode

**Backend**:
```python
# In src/main.py, ensure debug=True
app.run(host='0.0.0.0', port=5000, debug=True)
```

**Frontend**:
```bash
# Development mode is enabled by default with Vite
pnpm run dev
```

### Check API Responses

**Test login endpoint**:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Test protected endpoint**:
```bash
# First get token from login response, then:
curl -X GET http://localhost:5000/api/products \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Database Inspection

**View database contents**:
```bash
cd backend
source venv/bin/activate
python -c "
from src.main import app
from src.models.user import User, Product
with app.app_context():
    print('Users:', User.query.count())
    print('Products:', Product.query.count())
    for user in User.query.all():
        print(f'User: {user.username} ({user.role})')
"
```

## 🔍 Log Analysis

### Backend Logs
- Check console output when running `python src/main.py`
- Look for HTTP status codes (200, 401, 422, 500)
- Check for SQLAlchemy errors

### Frontend Logs
- Open browser Developer Tools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for failed API requests

### Common Error Patterns

**422 Unprocessable Entity**:
- Usually indicates validation errors
- Check request payload format
- Verify required fields are present

**401 Unauthorized**:
- JWT token issues
- Check if token is being sent correctly
- Verify token hasn't expired

**500 Internal Server Error**:
- Backend application error
- Check backend console for stack trace
- Usually indicates code bugs

## 📞 Getting Help

If you're still experiencing issues:

1. **Check the logs** - Both frontend (browser console) and backend (terminal)
2. **Verify setup** - Ensure all installation steps were completed
3. **Test components individually** - Test backend API directly with curl
4. **Check dependencies** - Ensure all required packages are installed

### Useful Commands for Diagnosis

```bash
# Check Python version
python3 --version

# Check Node.js version
node --version

# Check if ports are available
netstat -tulpn | grep :5000
netstat -tulpn | grep :5173

# Check virtual environment
which python  # Should point to venv/bin/python when activated

# Check installed packages
pip list  # In backend venv
npm list  # In frontend directory
```

## 🔄 Reset Everything

If all else fails, start fresh:

```bash
# Remove everything and start over
rm -rf pos-inventory-system
# Re-extract the project and run setup.sh
```

Remember: This is a development version, and some integration issues are expected. The core functionality is implemented and can be debugged with the information provided above.

