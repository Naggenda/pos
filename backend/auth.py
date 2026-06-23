import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import db, User

class AuthManager:
    """JWT Authentication Manager"""
    
    @staticmethod
    def generate_token(user_id, user_role, expires_in=3600):
        """Generate JWT token"""
        payload = {
            'user_id': user_id,
            'role': user_role,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return token
    
    @staticmethod
    def verify_token(token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def get_token_from_request(request):
        """Extract token from Authorization header"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            # Bearer <token>
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                return parts[1]
        except Exception:
            pass
        
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = AuthManager.get_token_from_request(request)
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        payload = AuthManager.verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.user_id = payload.get('user_id')
        request.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    
    return decorated

def role_required(*allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'user_role'):
                return jsonify({'error': 'Authentication required'}), 401
            
            if request.user_role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated
    return decorator
