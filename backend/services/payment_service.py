from backend.database.db import query_db, execute_db

VALID_PAYMENT_STATUSES = ['Pending', 'Paid', 'Failed']

def get_all_payments(user_id=None):
    """Retrieve payments with optional user filter."""
    query = """
        SELECT p.payment_id, p.rental_id, p.amount, p.status, p.payment_date, p.created_at,
               r.user_id, r.bicycle_id, r.duration, r.fare,
               u.name as user_name, u.email as user_email,
               b.bicycle_number, b.type as bicycle_type
        FROM payment p
        JOIN rental r ON p.rental_id = r.rental_id
        JOIN `user` u ON r.user_id = u.user_id
        JOIN bicycle b ON r.bicycle_id = b.bicycle_id
        WHERE 1=1
    """
    args = []
    if user_id:
        query += " AND r.user_id = %s"
        args.append(user_id)

    query += " ORDER BY p.payment_id DESC"
    return query_db(query, tuple(args))

def get_payment_by_id(payment_id: int):
    """Retrieve a single payment record by ID."""
    query = """
        SELECT p.payment_id, p.rental_id, p.amount, p.status, p.payment_date, p.created_at,
               r.user_id, r.bicycle_id, r.duration, r.fare,
               u.name as user_name, u.email as user_email,
               b.bicycle_number, b.type as bicycle_type
        FROM payment p
        JOIN rental r ON p.rental_id = r.rental_id
        JOIN `user` u ON r.user_id = u.user_id
        JOIN bicycle b ON r.bicycle_id = b.bicycle_id
        WHERE p.payment_id = %s
    """
    return query_db(query, (payment_id,), one=True)

def update_payment_status(payment_id: int, status: str):
    """Update simulated payment status."""
    if status not in VALID_PAYMENT_STATUSES:
        return None, f"Invalid payment status '{status}'. Must be one of {VALID_PAYMENT_STATUSES}."

    payment = get_payment_by_id(payment_id)
    if not payment:
        return None, "Payment record not found."

    execute_db(
        "UPDATE payment SET status = %s WHERE payment_id = %s",
        (status, payment_id)
    )
    return get_payment_by_id(payment_id), None

