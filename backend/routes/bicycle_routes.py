from flask import Blueprint, request, jsonify, g
from backend.services.bicycle_service import (
    get_all_bicycles, get_available_bicycles, get_bicycle_by_id,
    create_bicycle, update_bicycle, delete_bicycle
)
from backend.utils.auth_middleware import role_required
from backend.utils.validators import validate_required, validate_positive_number

bicycle_bp = Blueprint('bicycles', __name__, url_prefix='/api/bicycles')

@bicycle_bp.route('', methods=['GET'])
def list_bicycles():
    """List bicycles with optional filters."""
    station_id = request.args.get('station_id', type=int)
    status = request.args.get('status')
    owner_id = request.args.get('owner_id', type=int)
    bicycle_type = request.args.get('type')

    bikes = get_all_bicycles(
        station_id=station_id,
        status=status,
        owner_id=owner_id,
        bicycle_type=bicycle_type
    )
    return jsonify(bikes), 200

@bicycle_bp.route('/available', methods=['GET'])
def list_available_bicycles():
    """List only available bicycles."""
    station_id = request.args.get('station_id', type=int)
    bicycle_type = request.args.get('type')

    bikes = get_available_bicycles(station_id=station_id, bicycle_type=bicycle_type)
    return jsonify(bikes), 200

@bicycle_bp.route('/<int:bicycle_id>', methods=['GET'])
def get_bicycle(bicycle_id):
    """Get single bicycle details."""
    bike = get_bicycle_by_id(bicycle_id)
    if not bike:
        return jsonify({'error': 'Bicycle not found.'}), 404
    return jsonify(bike), 200

@bicycle_bp.route('', methods=['POST'])
@role_required(['admin', 'rental_owner'])
def add_bicycle():
    """Add a new bicycle (Admin or Rental Owner)."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['bicycle_number', 'type', 'rental_rate'])
    if not ok:
        return jsonify({'error': err}), 400

    ok, rate = validate_positive_number(data['rental_rate'], 'Rental rate')
    if not ok:
        return jsonify({'error': rate}), 400

    station_id = data.get('station_id')
    if station_id is not None:
        try:
            station_id = int(station_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Station ID must be a valid integer.'}), 400

    # Determine owner_id
    if g.current_user['role'] == 'rental_owner':
        owner_id = g.current_user['user_id']
    else:
        owner_id = data.get('owner_id')
        if not owner_id:
            return jsonify({'error': 'Owner ID is required when adding as admin.'}), 400

    status = data.get('status', 'Available')

    bike, err = create_bicycle(
        bicycle_number=data['bicycle_number'].strip(),
        bicycle_type=data['type'].strip(),
        rental_rate=float(rate),
        owner_id=int(owner_id),
        station_id=station_id,
        status=status
    )
    if err:
        return jsonify({'error': err}), 400

    return jsonify(bike), 201

@bicycle_bp.route('/<int:bicycle_id>', methods=['PUT'])
@role_required(['admin', 'rental_owner'])
def edit_bicycle(bicycle_id):
    """Update bicycle information or station assignment."""
    data = request.get_json() or {}

    b_type = data.get('type')
    status = data.get('status')
    station_id = data.get('station_id')

    rental_rate = None
    if 'rental_rate' in data:
        ok, rate = validate_positive_number(data['rental_rate'], 'Rental rate')
        if not ok:
            return jsonify({'error': rate}), 400
        rental_rate = float(rate)

    if station_id is not None and station_id != "":
        try:
            station_id = int(station_id)
        except (ValueError, TypeError):
            return jsonify({'error': 'Station ID must be a valid integer.'}), 400
    elif 'station_id' in data and (station_id is None or station_id == ""):
        station_id = None

    bike, err = update_bicycle(
        bicycle_id=bicycle_id,
        bicycle_type=b_type.strip() if b_type else None,
        rental_rate=rental_rate,
        status=status,
        station_id=station_id,
        user_role=g.current_user['role'],
        user_id=g.current_user['user_id']
    )
    if err:
        return jsonify({'error': err}), 400

    return jsonify(bike), 200

@bicycle_bp.route('/<int:bicycle_id>', methods=['DELETE'])
@role_required(['admin', 'rental_owner'])
def remove_bicycle(bicycle_id):
    """Delete a bicycle."""
    ok, err = delete_bicycle(
        bicycle_id=bicycle_id,
        user_role=g.current_user['role'],
        user_id=g.current_user['user_id']
    )
    if not ok:
        return jsonify({'error': err}), 400

    return jsonify({'message': 'Bicycle deleted successfully.'}), 200

