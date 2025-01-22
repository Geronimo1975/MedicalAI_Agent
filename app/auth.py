from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, db
from werkzeug.security import generate_password_hash

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400

    user = User(
        username=data['username'],
        email=data['email'],
        name=data.get('name', ''),
        role=data.get('role', 'patient')  # Default role is patient
    )
    user.set_password(data['password'])

    if data.get('role') == 'doctor' and 'specialty' in data:
        user.specialty = data['specialty']

    db.session.add(user)
    try:
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
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'error': 'Already logged in'}), 400

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

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@bp.route('/user')
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

@bp.route('/update-preferences', methods=['POST'])
@login_required
def update_preferences():
    data = request.get_json()

    if 'preferred_language' in data:
        current_user.preferred_language = data['preferred_language']
        db.session.commit()

    return jsonify({
        'message': 'Preferences updated successfully',
        'preferred_language': current_user.preferred_language
    })