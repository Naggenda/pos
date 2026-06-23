# POS System with EFRIS Integration

A modern Point of Sales (POS) system with EFRIS (Uganda Revenue Authority) integration and JWT-based authentication with role-based access control, built with Flask backend and a responsive HTML/CSS frontend.

## Features

- **JWT Authentication**: Secure JSON Web Token-based authentication
- **Role-Based Access Control**: Admin, Manager, and Cashier roles with specific permissions
- **Sales Management**: Easy-to-use POS interface for processing sales
- **Product Management**: Add, edit, and manage product inventory (Manager/Admin only)
- **EFRIS Integration**: Automatic submission of sales invoices to EFRIS with receipt tracking
- **Dashboard**: Real-time statistics and business metrics
- **Transaction History**: View and manage all sales transactions
- **Tax Calculation**: Automatic calculation of VAT and tax tracking
- **Inventory Management**: Track product stock levels
- **Payment Methods**: Support for Cash, Card, and Mobile Money payments
- **User Management**: Create and manage user accounts with roles

## User Roles

- **ADMIN**: Full system access, user management, all operations
- **MANAGER**: Sales, product, and report management
- **CASHIER**: Sales transactions and viewing reports

## Project Structure

```
POS/
├── backend/
│   ├── app.py                 # Flask application entry point
│   ├── config.py              # Configuration management
│   ├── models.py              # Database models
│   ├── routes.py              # API endpoints
│   ├── efris_integration.py   # EFRIS API client
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment variables template
├── frontend/
│   ├── index.html             # Main HTML page
│   ├── style.css              # Styling
│   └── script.js              # Frontend logic
├── README.md                  # This file
└── .github/
    └── copilot-instructions.md
```

## Prerequisites

- Python 3.8 or higher
- Flask 2.3.2+
- pip (Python package manager)
- Modern web browser

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate  # On Windows
# or
source venv/bin/activate      # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment configuration:
```bash
cp .env.example .env
```

5. Edit `.env` with your EFRIS credentials:
```env
EFRIS_USERNAME=your_username
EFRIS_PASSWORD=your_password
EFRIS_TIN=your_tax_id_number
EFRIS_DEVICE_SERIAL=your_device_serial
```

6. Run the Flask application:
```bash
python app.py
```

The backend will start on `http://localhost:5000`

**Default Admin Credentials (automatically created):**
- Username: `admin`
- Password: `admin123`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Serve the frontend files using any HTTP server. Options:

**Using Python (built-in):**
```bash
python -m http.server 8000
```

**Using Node.js (if installed):**
```bash
npx http-server
```

**Using VS Code Live Server extension:**
- Right-click `index.html` → "Open with Live Server"

3. OAuthentication System

The system uses JWT (JSON Web Tokens) for authentication:

1. Users log in with username and password
2. Server returns a JWT token that's valid for 1 hour
3. Token is stored in localStorage (if "Remember me" is checked) or sessionStorage
4. All API requests include the token in the Authorization header
5. On logout, the token is removed from storage

### Creating New Users

**Via API:**
```bash
POST /api/auth/register
{
    "username": "john",
    "email": "john@example.com",
    "password": "secure_password",
    "full_name": "John Doe",
    "role": "CASHIER"
}
```

**Via Python Shell (Admin Only):**
```bash
python
>>> from app import create_app, db
>>> from models import User
>>> Authentication
- `POST /api/auth/login` - Login with username/password
- `POST /api/auth/logout` - Logout (requires token)
- `POST /api/auth/register` - Register new user
- `GET /api/auth/verify-token` - Verify JWT token validity
- `GET /api/auth/profile` - Get current user profile
- `PUT /api/auth/profile` - Update current user profile
- `POST /api/auth/change-password` - Change password

### User Management (Admin Only)
- `GET /api/auth/users` - List all users
- `PUT /api/auth/users/<id>` - Update user
- `DELETE /api/auth/users/<id>` - Delete user

### Products (Requires Authentication)
- `GET /api/products` - Get all products
- `POST /api/products` - Create new product (Manager/Admin only)
- `GET /api/products/<id>` - Get specific product
- `PUT /api/products/<id>` - Update product (Manager/Admin only)
- `DELETE /api/products/<id>` - Delete product (Manager/Admin only)

### Sales (Requires Authentication)
- `GET /api/sales` - Get all sales with filtering
- `POST /api/sales` - Create new sale (Cashier/Manager/Admin)
- `GET /api/sales/<id>` - Get specific sale
- `POST /api/sales/<id>/submit-efris` - Submit sale to EFRIS

### Dashboard (Requires Authentication)
- `GET /api/dashboard/summary` - Get dashboard statistics

### Health Checkame: `admin`
   - Password: `admin123`

## Configuration

### EFRIS Setup

To enable EFRIS integration:

1. Obtain EFRIS credentials from the Uganda Revenue Authority
2. Update the `.env` file in the backend directory:
   - `EFRIS_USERNAME`: Your EFRIS account username
   - `EFRIS_PASSWORD`: Your EFRIS account password
   - `EFRIS_TIN`: Your Tax Identification Number
   - `EFRIS_DEVICE_SERIAL`: Your device's serial number

### Database

By default, the system uses SQLite. For production, update the `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/pos_db
```

## API Endpoints

### Products
- `GET /api/products` - Get all products
- `POST /api/products` - Create new product
- `GET /api/products/<id>` - Get specific product
- `PUT /api/products/<id>` - Update product
- `DELETE /api/products/<id>` - Delete product

### Sales
- `GET /api/sales` - Get all sales with filtering
- `POST /api/sales` - Create new sale
- `GET /api/sales/<id>` - Get specific sale
- `POST /api/sales/<id>/submit-efris` - Submit sale to EFRIS

### Dashboard
- `GET /api/dashboard/summary` - Get dashboard statistics

### Health
- `GET /api/health` - Health check

## Usage

### Creating a Sale

1. Go to the "New Sale" section
2. Search and click on products to add them to the cart
3. Adjust quantities as needed
4. Enter any discount amount
5. Select payment method
6. Click "Complete Sale"
7. The system will automatically submit to EFRIS (if configured)

### Managing Products

1. Go to "Products" section
2. Click "Add Product" to create new products
3. Fill in product details (name, SKU, price, quantity, tax rate)
4. Products can be edited`.env` for production
- Use environment variables for all sensitive data (never hardcode)
- Enable HTTPS/SSL in production (especially with JWT tokens)
- Implement authentication/authorization (Done - JWT + roles)
- Validate all inputs on both frontend and backend
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Use strong passwords for user accounts
- Regularly rotate EFRIS credentials
- Monitor and log all authentication attempts
- Implement rate limiting for login attempts (recommended for production) if needed
3. Click "View" to see transaction details
4. Manually submit to EFRIS if needed

### EFRIS Status

1. Go to "EFRIS Status" section
2. Check connection status and configuration
3. View recent submissions and their status

## Troubleshooting

### Backend won't start
- Ensure Python is installed: `python --version`
- Check all dependencies: `pip install -r requirements.txt`
- Verify port 5000 is not in use

### EFRIS connection fails
- Verify EFRIS credentials in `.env`
- Check internet connection
- Ensure EFRIS API is accessible
- Review EFRIS logs in the Transactions section

### Frontend not loading products
- Ensure backend is running
- Check browser console for errors (F12)
- Verify CORS is enabled (it's enabled by default)
- Check that the API_BASE_URL in `script.js` matches your backend URL

### Database errors
- Delete `pos_system.db` to reset the database
- Re-run the application to recreate tables

## Development

### Adding new features

1. **Backend**: Add routes in `routes.py`, update models in `models.py`
2. **Frontend**: Update HTML in `index.html`, add styles in `style.css`, add logic in `script.js`

### Testing

```bash
# Backend testing (add to the project)
python -m pytest

# Frontend: Open browser console (F12) to check for errors
```

## Security Notes

- Change `SECRET_KEY` in production
- Use environment variables for all sensitive data
- Enable HTTPS in production
- Implement authentication/authorization
- Validate all inputs on both frontend and backend
- Keep dependencies updated

## EFRIS Integration Details

The system integrates with EFRIS by:

1. Formatting sales data according to EFRIS specifications
2. Authenticating using your TIN and device credentials
3. Submitting invoices through the EFRIS API
4. Tracking submission status and receipt codes
5. Logging1.0 - JWT Authentication and Role-Based Access Controlns for audit purposes

Each sale automatically attempts submission to EFRIS and records the status. Failed submissions can be retried manually.

## Support and Troubleshooting

For common issues:
- Check the EFRIS Status section for connection diagnostics
- Review browser console (F12) for frontend errors
- Check terminal/console output for backend errors
- Verify environment variables are correctly set

## License

This project is provided as-is for development and commercial use.

## Version

Version 1.0.0 - Initial Release

---

**Last Updated**: 2026-06-22
