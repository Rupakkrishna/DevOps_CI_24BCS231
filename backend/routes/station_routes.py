from flask import Blueprint, request, jsonify
from backend.services.station_service import (
    get_all_stations, get_station_by_id, create_station, update_station, delete_station
)
from backend.services.bicycle_service import get_available_bicycles
from backend.utils.auth_middleware import role_required
from backend.utils.validators import validate_required, validate_positive_number

station_bp = Blueprint('stations', __name__, url_prefix='/api/stations')

@station_bp.route('', methods=['GET'])
def list_stations():
    """List all docking stations."""
    stations = get_all_stations()
    return jsonify(stations), 200

@station_bp.route('/<int:station_id>', methods=['GET'])
def get_station(station_id):
    """Get single station by ID."""
    station = get_station_by_id(station_id)
    if not station:
        return jsonify({'error': 'Station not found.'}), 404
    return jsonify(station), 200

@station_bp.route('/<int:station_id>/bicycles', methods=['GET'])
def get_station_bicycles(station_id):
    """Get available bicycles at a specific station."""
    station = get_station_by_id(station_id)
    if not station:
        return jsonify({'error': 'Station not found.'}), 404
    bikes = get_available_bicycles(station_id=station_id)
    return jsonify(bikes), 200

@station_bp.route('', methods=['POST'])
@role_required('admin')
def add_station():
    """Create a new station (Admin only)."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['station_name', 'location', 'capacity'])
    if not ok:
        return jsonify({'error': err}), 400

    ok, capacity = validate_positive_number(data['capacity'], 'Capacity')
    if not ok:
        return jsonify({'error': capacity}), 400

    station, err = create_station(
        data['station_name'].strip(),
        data['location'].strip(),
        int(capacity)
    )
    if err:
        return jsonify({'error': err}), 400

    return jsonify(station), 201

@station_bp.route('/<int:station_id>', methods=['PUT'])
@role_required('admin')
def edit_station(station_id):
    """Update station details (Admin only)."""
    data = request.get_json() or {}
    ok, err = validate_required(data, ['station_name', 'location', 'capacity'])
    if not ok:
        return jsonify({'error': err}), 400

    ok, capacity = validate_positive_number(data['capacity'], 'Capacity')
    if not ok:
        return jsonify({'error': capacity}), 400

    station, err = update_station(
        station_id,
        data['station_name'].strip(),
        data['location'].strip(),
        int(capacity)
    )
    if err:
        return jsonify({'error': err}), 400

    return jsonify(station), 200

@station_bp.route('/<int:station_id>', methods=['DELETE'])
@role_required('admin')
def remove_station(station_id):
    """Delete a station (Admin only)."""
    ok, err = delete_station(station_id)
    if not ok:
        return jsonify({'error': err}), 400
    return jsonify({'message': 'Station deleted successfully.'}), 200

