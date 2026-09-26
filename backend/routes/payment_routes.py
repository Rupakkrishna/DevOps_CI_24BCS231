from flask import Blueprint, request, jsonify, g
from backend.services.payment_service import get_all_payments, get_payment_by_id, update_payment_status
from backend.utils.auth_middleware import token_required

payment_bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@payment_bp.route('', methods=['GET'])
@token_required
def list_payments():
    """List payment records for admin or authenticated user."""
    role = g.current_user['role']
    if role == 'admin':
        payments = get_all_payments()
    elif role == 'user':
        payments = get_all_payments(user_id=g.current_user['user_id'])
    else:
        return jsonify({'error': 'Access forbidden.'}), 403

    return jsonify(payments), 200

@payment_bp.route('/<int:payment_id>', methods=['GET'])
@token_required
def get_payment(payment_id):
    """Get single payment record."""
    payment = get_payment_by_id(payment_id)
    if not payment:
        return jsonify({'error': 'Payment not found.'}), 404

    if g.current_user['role'] == 'user' and payment['user_id'] != g.current_user['user_id']:
        return jsonify({'error': 'Access forbidden.'}), 403

    return jsonify(payment), 200

@payment_bp.route('/<int:payment_id>/pay', methods=['POST'])
@token_required
def process_payment(payment_id):
    """Simulate paying an outstanding payment."""
    payment = get_payment_by_id(payment_id)
    if not payment:
        return jsonify({'error': 'Payment record not found.'}), 404

    if g.current_user['role'] == 'user' and payment['user_id'] != g.current_user['user_id']:
        return jsonify({'error': 'Access forbidden.'}), 403

    updated, err = update_payment_status(payment_id, 'Paid')
    if err:
        return jsonify({'error': err}), 400

    return jsonify(updated), 200

