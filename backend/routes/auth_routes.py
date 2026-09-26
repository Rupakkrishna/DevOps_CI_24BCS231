from flask import Blueprint, request, jsonify, g
from backend.services.auth_service import register_user, register_owner, login_user, get_current_user_profile
from backend.utils.auth_middleware import token_required
from backend.utils.validators import validate_email, validate_password, validate_phone, validate_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register customer or rental owner."""
    data = request.get_json() or {}
    role = data.get('role', 'user').lower()

    if role not in ['user', 'rental_owner']:
        return jsonify({'error': "Invalid role. Role must be 'user' or 'rental_owner'."}), 400

    required = ['name', 'email', 'phone', 'password']
    if role == 'rental_owner':
        required.append('address')

    ok, err = validate_required(data, required)
    if not ok:
        return jsonify({'error': err}), 400

    ok, email = validate_email(data['email'])
    if not ok:
        return jsonify({'error': email}), 400

    ok, password = validate_password(data['password'])
    if not ok:
        return jsonify({'error': password}), 400

    ok, phone = validate_phone(data['phone'])
    if not ok:
        return jsonify({'error': phone}), 400

    name = data['name'].strip()

    if role == 'rental_owner':
        address = data['address'].strip()
        result, err = register_owner(name, email, phone, password, address)
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result), 201
    else:
        result, err = register_user(name, email, phone, password)
        if err:
            return jsonify({'error': err}), 400
        return jsonify(result), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate any user (admin, user, rental_owner)."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['email', 'password'])
    if not ok:
        return jsonify({'error': err}), 400

    email = data['email'].strip()
    password = data['password']

    result, err = login_user(email, password)
    if err:
        return jsonify({'error': err}), 401

    return jsonify(result), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Client-side token disposal confirmation."""
    return jsonify({'message': 'Logged out successfully.'}), 200

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me():
    """Get profile of current authenticated user."""
    user = get_current_user_profile(g.current_user['user_id'], g.current_user['role'])
    if not user:
        return jsonify({'error': 'User not found.'}), 404
    return jsonify(user), 200

