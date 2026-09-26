from flask import Blueprint, request, jsonify
from backend.database.db import query_db, execute_db
from backend.utils.auth_middleware import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

@admin_bp.route('/dashboard', methods=['GET'])
@role_required('admin')
def get_dashboard_stats():
    """Retrieve aggregate platform metrics for the admin dashboard."""
    # User counts
    users_count = query_db("SELECT COUNT(*) as count FROM `user`", one=True)['count']
    owners_count = query_db("SELECT COUNT(*) as count FROM rental_owner", one=True)['count']
    pending_owners = query_db("SELECT COUNT(*) as count FROM rental_owner WHERE approval_status = 'Pending'", one=True)['count']

    # Bicycle counts
    total_bikes = query_db("SELECT COUNT(*) as count FROM bicycle", one=True)['count']
    available_bikes = query_db("SELECT COUNT(*) as count FROM bicycle WHERE status = 'Available'", one=True)['count']
    rented_bikes = query_db("SELECT COUNT(*) as count FROM bicycle WHERE status = 'Rented'", one=True)['count']
    maintenance_bikes = query_db("SELECT COUNT(*) as count FROM bicycle WHERE status = 'Maintenance'", one=True)['count']
    inactive_bikes = query_db("SELECT COUNT(*) as count FROM bicycle WHERE status = 'Inactive'", one=True)['count']

    # Station counts
    total_stations = query_db("SELECT COUNT(*) as count FROM station", one=True)['count']

    # Rental counts
    active_rentals = query_db("SELECT COUNT(*) as count FROM rental WHERE status = 'Active'", one=True)['count']
    completed_rentals = query_db("SELECT COUNT(*) as count FROM rental WHERE status = 'Completed'", one=True)['count']

    # Payment summary
    revenue_row = query_db("SELECT SUM(amount) as total FROM payment WHERE status = 'Paid'", one=True)
    total_revenue = float(revenue_row['total'] or 0.0)

    pending_payment_row = query_db("SELECT SUM(amount) as total FROM payment WHERE status = 'Pending'", one=True)
    total_pending_payment = float(pending_payment_row['total'] or 0.0)

    return jsonify({
        'users': {
            'total_customers': users_count,
            'total_owners': owners_count,
            'pending_owner_approvals': pending_owners
        },
        'bicycles': {
            'total': total_bikes,
            'available': available_bikes,
            'rented': rented_bikes,
            'maintenance': maintenance_bikes,
            'inactive': inactive_bikes
        },
        'stations': {
            'total': total_stations
        },
        'rentals': {
            'active': active_rentals,
            'completed': completed_rentals
        },
        'payments': {
            'total_revenue': total_revenue,
            'total_pending': total_pending_payment
        }
    }), 200

@admin_bp.route('/users', methods=['GET'])
@role_required('admin')
def list_users():
    """List all registered customers."""
    users = query_db("SELECT user_id, name, email, phone, created_at FROM `user` ORDER BY user_id DESC")
    return jsonify(users), 200

@admin_bp.route('/owners', methods=['GET'])
@role_required('admin')
def list_owners():
    """List all rental owners with their approval statuses."""
    status = request.args.get('status')
    query = "SELECT owner_id, name, email, phone, address, approval_status, created_at FROM rental_owner"
    args = []
    if status:
        query += " WHERE approval_status = %s"
        args.append(status)
    query += " ORDER BY owner_id DESC"
    owners = query_db(query, tuple(args))
    return jsonify(owners), 200

@admin_bp.route('/owners/<int:owner_id>/status', methods=['POST'])
@role_required('admin')
def set_owner_status(owner_id):
    """Approve or reject a rental owner account."""
    data = request.get_json() or {}
    new_status = data.get('status')
    if new_status not in ['Approved', 'Rejected']:
        return jsonify({'error': "Status must be 'Approved' or 'Rejected'."}), 400

    owner = query_db("SELECT owner_id, name, email FROM rental_owner WHERE owner_id = %s", (owner_id,), one=True)
    if not owner:
        return jsonify({'error': 'Rental owner not found.'}), 404

    execute_db("UPDATE rental_owner SET approval_status = %s WHERE owner_id = %s", (new_status, owner_id))
    return jsonify({
        'owner_id': owner_id,
        'approval_status': new_status,
        'message': f"Rental owner account has been {new_status.lower()}."
    }), 200

