from flask import Blueprint, request, jsonify, g
from backend.services.rental_service import (
    rent_bicycle, return_bicycle, get_rental_by_id,
    get_user_active_rental, get_all_rentals
)
from backend.utils.auth_middleware import token_required, role_required
from backend.utils.validators import validate_required

rental_bp = Blueprint('rentals', __name__, url_prefix='/api/rentals')

@rental_bp.route('', methods=['POST'])
@role_required('user')
def create_rental():
    """Start a new bicycle rental for the authenticated customer."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['bicycle_id'])
    if not ok:
        return jsonify({'error': err}), 400

    try:
        bicycle_id = int(data['bicycle_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'bicycle_id must be an integer.'}), 400

    rental, err = rent_bicycle(g.current_user['user_id'], bicycle_id)
    if err:
        return jsonify({'error': err}), 400

    return jsonify(rental), 201

@rental_bp.route('/active', methods=['GET'])
@role_required('user')
def get_active_rental():
    """Get active rental for the current authenticated customer."""
    rental = get_user_active_rental(g.current_user['user_id'])
    if not rental:
        return jsonify({'rental': None, 'message': 'No active rental.'}), 200
    return jsonify({'rental': rental}), 200

@rental_bp.route('/<int:rental_id>/return', methods=['POST'])
@token_required
def return_rented_bicycle(rental_id):
    """Return a bicycle to a designated station."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['return_station_id'])
    if not ok:
        return jsonify({'error': err}), 400

    try:
        return_station_id = int(data['return_station_id'])
    except (ValueError, TypeError):
        return jsonify({'error': 'return_station_id must be an integer.'}), 400

    is_admin = g.current_user['role'] == 'admin'
    user_id = g.current_user['user_id']

    rental, err = return_bicycle(
        rental_id=rental_id,
        return_station_id=return_station_id,
        user_id=user_id,
        is_admin=is_admin
    )
    if err:
        return jsonify({'error': err}), 400

    return jsonify(rental), 200

@rental_bp.route('/<int:rental_id>', methods=['GET'])
@token_required
def get_rental(rental_id):
    """Get rental details by ID."""
    rental = get_rental_by_id(rental_id)
    if not rental:
        return jsonify({'error': 'Rental not found.'}), 404

    # Security check
    if g.current_user['role'] == 'user' and rental['user_id'] != g.current_user['user_id']:
        return jsonify({'error': 'Access forbidden.'}), 403

    return jsonify(rental), 200

@rental_bp.route('', methods=['GET'])
@token_required
def list_rentals():
    """List rentals based on role and filters."""
    role = g.current_user['role']
    status = request.args.get('status')

    if role == 'admin':
        rentals = get_all_rentals(status=status)
    elif role == 'rental_owner':
        rentals = get_all_rentals(status=status, owner_id=g.current_user['user_id'])
    else:  # 'user'
        rentals = get_all_rentals(status=status, user_id=g.current_user['user_id'])

    return jsonify(rentals), 200

