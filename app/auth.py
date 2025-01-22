from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email'],
        name=data['name'],
        role=data['role']
    )
    user.set_password(data['password'])
    
    if data['role'] == 'doctor' and 'specialty' in data:
        user.specialty = data['specialty']
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    
    return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'name': user.name,
        'role': user.role,
        'specialty': user.specialty
    })

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'role': user.role,
            'specialty': user.specialty
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/user')
def get_user():
    if current_user.is_authenticated:
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'name': current_user.name,
            'role': current_user.role,
            'specialty': current_user.specialty
        })
    return jsonify({'error': 'Not authenticated'}), 401
