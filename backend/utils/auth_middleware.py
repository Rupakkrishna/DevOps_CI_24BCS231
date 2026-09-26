import jwt
from datetime import datetime, timezone
from functools import wraps
from flask import request, jsonify, current_app, g

def generate_token(user_id, role, name, email):
    """Generate a signed JWT token."""
    payload = {
        'user_id': user_id,
        'role': role,
        'name': name,
        'email': email,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + current_app.config['JWT_EXPIRATION']
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')
    return token

def decode_token(token):
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Token has expired. Please log in again."
    except jwt.InvalidTokenError:
        return None, "Invalid authentication token."

def token_required(f):
    """Decorator to require a valid JWT token in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Authentication token is required.'}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid Authorization header format. Expected "Bearer <token>".'}), 401

        token = parts[1]
        payload, err = decode_token(token)
        if err:
            return jsonify({'error': err}), 401

        g.current_user = payload
        return f(*args, **kwargs)
    return decorated

def role_required(allowed_roles):
    """Decorator to enforce role-based access control (RBAC)."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(*args, **kwargs):
            user_role = g.current_user.get('role')
            if user_role not in allowed_roles:
                return jsonify({
                    'error': f'Access forbidden: required role in {allowed_roles}, but got {user_role}.'
                }), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

