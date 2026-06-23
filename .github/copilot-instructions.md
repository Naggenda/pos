<!-- Use this file to provide workspace-specific custom instructions to Copilot. -->

# POS System Development Guidelines

## Project Overview

This is a complete Point of Sales (POS) system with EFRIS integration and JWT-based authentication. It consists of:
- **Backend**: Flask Python REST API with role-based access control
- **Frontend**: Responsive HTML/CSS/JavaScript SPA with login system

## Setup Instructions

### Quick Start - Backend

1. Navigate to backend folder: `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate environment: 
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy environment config: `cp .env.example .env`
6. Update EFRIS credentials in `.env`
7. Run: `python app.py`

**Default Admin Credentials:**
- Username: `admin`
- Password: `admin123`

### Quick Start - Frontend

1. Navigate to frontend folder: `cd frontend`
2. Start a simple HTTP server:
   - Python: `python -m http.server 8000`
   - Or use VS Code Live Server
3. Open: `http://localhost:8000/login.html`

## Technology Stack

- **Backend**: Flask 2.3.2, SQLAlchemy, Flask-CORS, PyJWT
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Database**: SQLite (development), PostgreSQL (production)
- **APIs**: EFRIS REST API
- **Authentication**: JWT (JSON Web Tokens)

## Authentication System

### User Roles

1. **ADMIN**: Full access to all features, user management
2. **MANAGER**: Sales and product management, view reports
3. **CASHIER**: Sales transactions only

### JWT Flow

1. User logs in with username/password
2. Backend validates credentials and returns JWT token
3. Frontend stores token in localStorage (remember) or sessionStorage (session)
4. All API requests include token in Authorization header
5. Backend validates token on each request
6. Token expires after 1 hour (configurable)

### Authentication Routes

- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/logout` - Logout (clears session on backend)
- `GET /api/auth/verify-token` - Verify if token is valid
- `GET /api/auth/profile` - Get current user profile
- `PUT /api/auth/profile` - Update profile
- `POST /api/auth/change-password` - Change password
- `GET /api/auth/users` - List users (admin/manager only)
- `PUT /api/auth/users/<id>` - Update user (admin only)
- `DELETE /api/auth/users/<id>` - Delete user (admin only)
- `POST /api/auth/register` - Register new user

## Key Components

### Backend Structure
- `app.py` - Application factory with default admin creation
- `config.py` - Configuration management
- `models.py` - Database models (User, Product, Sale, SaleItem, EfrisLog)
- `routes.py` - API endpoints with role-based decorators
- `auth.py` - JWT authentication manager and decorators
- `auth_routes.py` - Authentication endpoints
- `efris_integration.py` - EFRIS API client

### Frontend Structure
- `login.html` - Login page with remember-me option
- `index.html` - Main dashboard SPA
- `style.css` - Responsive styling
- `script.js` - Frontend logic with authentication

### Database Models
- **User**: User accounts with roles and passwords
- **Product**: Product inventory
- **Sale**: Sales transactions
- **SaleItem**: Line items in sales
- **EfrisLog**: EFRIS API interaction logs

### Role-Based Access Control

```
Products CRUD:
- Create/Update/Delete: ADMIN, MANAGER
- Read: All authenticated users

Sales:
- Create: CASHIER, MANAGER, ADMIN
- Read: All authenticated users
- Submit to EFRIS: CASHIER, MANAGER, ADMIN

User Management:
- List: ADMIN, MANAGER
- Update: ADMIN only
- Delete: ADMIN only
```

## Development Workflow

### Adding a New Feature

1. **Backend**:
   - Add database model changes to `models.py`
   - Add API routes to `routes.py` with appropriate decorators
   - Add authentication routes to `auth_routes.py` if needed
   - Use `@token_required` and `@role_required()` decorators

2. **Frontend**:
   - Update HTML in `index.html`
   - Add styles in `style.css`
   - Add JavaScript functions in `script.js`
   - Use `getAuthHeaders()` for API calls
   - Check `currentUser.role` for permission-based UI

### Protecting Routes

```python
# Token required
@api.route('/protected', methods=['GET'])
@token_required
def protected_route():
    user_id = request.user_id
    user_role = request.user_role
    return jsonify({'message': 'Protected'}), 200

# Role required
@api.route('/admin-only', methods=['GET'])
@token_required
@role_required('ADMIN')
def admin_only():
    return jsonify({'message': 'Admin only'}), 200

# Multiple roles
@api.route('/staff', methods=['GET'])
@token_required
@role_required('ADMIN', 'MANAGER')
def staff_only():
    return jsonify({'message': 'Staff only'}), 200
```

### Testing Changes

- **Backend**: Use curl or Postman with JWT token
- **Frontend**: Test in browser with Developer Tools (F12)
- **Authentication**: Login with different user roles to test access

## Common Tasks

### Create New User (Admin Only)
```python
POST /api/auth/register
{
    "username": "john",
    "email": "john@example.com",
    "password": "secure_password",
    "full_name": "John Doe",
    "role": "CASHIER"
}
```

### Login
```python
POST /api/auth/login
{
    "username": "admin",
    "password": "admin123"
}
```

### Update Product (Manager/Admin Only)
Frontend checks role before allowing product management.

### Submit to EFRIS (Any Staff)
Sales can be submitted by CASHIER, MANAGER, or ADMIN roles.

## Environment Variables

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite:///pos_system.db
EFRIS_BASE_URL=https://restapi.efris.go.ug/api
EFRIS_USERNAME=your_username
EFRIS_PASSWORD=your_password
EFRIS_TIN=your_tax_id
EFRIS_DEVICE_SERIAL=your_device_serial
PORT=5000
```

## API Response Format

All endpoints return JSON:

```json
{
  "data": { /* response data */ },
  "error": null,
  "status": "success"
}
```

Authentication responses include token:

```json
{
  "message": "Login successful",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": "user-id",
    "username": "admin",
    "email": "admin@pos.local",
    "role": "ADMIN",
    "full_name": "Administrator"
  }
}
```

## Code Style

- **Python**: Follow PEP 8
- **JavaScript**: Use camelCase for functions/variables
- **CSS**: Use kebab-case for class names
- **Comments**: Keep comments clear and concise

## Security Reminders

- Never commit `.env` file
- Change `SECRET_KEY` in production
- Use HTTPS in production (JWT tokens in Authorization header)
- Implement rate limiting for login attempts
- Hash passwords with Werkzeug (automatically done)
- Validate all inputs server-side
- Use parameterized queries (SQLAlchemy handles this)
- Clear tokens on logout (frontend removes token)
- Set token expiration (default 1 hour)

## Debugging Tips

1. **Authentication issues**: Check token in browser DevTools → Storage
2. **Permission denied**: Verify user role matches required role
3. **Token expired**: User must login again
4. **Backend errors**: Check terminal/console output
5. **Frontend errors**: Open browser DevTools (F12)
6. **API issues**: Use Network tab to inspect requests/responses

## Useful Commands

```bash
# Backend
python app.py                     # Run Flask
pip install -r requirements.txt   # Install dependencies
python -c "from app import *"    # Test imports

# Frontend
python -m http.server 8000       # Serve files

# Create new admin user in Python shell
python
>>> from app import create_app, db
>>> from models import User
>>> app = create_app()
>>> with app.app_context():
>>>     u = User(username='newadmin', email='new@admin.com', role='ADMIN', full_name='New Admin')
>>>     u.set_password('password123')
>>>     db.session.add(u)
>>>     db.session.commit()
```

## Version Control

- Commit frequently with clear messages
- Keep `.env.example` updated (without secrets)
- Don't commit `*.db`, `venv/`, or `.env` files
- Use meaningful branch names

## Future Enhancements

- Two-factor authentication (2FA)
- Social login (OAuth)
- Advanced reporting and analytics
- Receipt printing with QR codes
- Multi-location support
- Barcode scanning
- Payment gateway integration
- Mobile app version
- Audit logging
- Session management/concurrent login limits

---

**Project Version**: 1.1.0
**Last Updated**: 2026-06-22

