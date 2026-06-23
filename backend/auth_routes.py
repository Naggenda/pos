from flask import Blueprint, request, jsonify
from models import db, User
from auth import AuthManager, token_required, role_required
from datetime import datetime

auth_api = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_api.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name', ''),
            role=data.get('role', 'CASHIER')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_api.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Missing username or password'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'User account is inactive'}), 403
    
    try:
        # Generate token
        token = AuthManager.generate_token(user.id, user.role)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_api.route('/logout', methods=['POST'])
@token_required
def logout():
    """Logout user (client should remove token)"""
    return jsonify({'message': 'Logout successful'}), 200

@auth_api.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    try:
        user = User.query.get(request.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_api.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update current user profile"""
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data:
            # Check if email is already taken
            existing = User.query.filter(
                User.email == data['email'],
                User.id != user.id
            ).first()
            if existing:
                return jsonify({'error': 'Email already in use'}), 400
            user.email = data['email']
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_api.route('/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    user = User.query.get(request.user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data.get('old_password') or not data.get('new_password'):
        return jsonify({'error': 'Missing password fields'}), 400
    
    if not user.check_password(data['old_password']):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_api.route('/users', methods=['GET'])
@token_required
@role_required('ADMIN', 'MANAGER')
def list_users():
    """List all users (admin/manager only)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_api.route('/users/<user_id>', methods=['PUT'])
@token_required
@role_required('ADMIN')
def update_user(user_id):
    """Update user (admin only)"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'role' in data:
            if data['role'] not in User.ROLES:
                return jsonify({'error': 'Invalid role'}), 400
            user.role = data['role']
        
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        if 'full_name' in data:
            user.full_name = data['full_name']
        
        db.session.commit()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_api.route('/users/<user_id>', methods=['DELETE'])
@token_required
@role_required('ADMIN')
def delete_user(user_id):
    """Delete user (admin only)"""
    if user_id == request.user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_api.route('/verify-token', methods=['GET'])
@token_required
def verify_token():
    """Verify if token is valid"""
    return jsonify({
        'valid': True,
        'user_id': request.user_id,
        'role': request.user_role
    }), 200
