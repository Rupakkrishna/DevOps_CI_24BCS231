import math
from datetime import datetime, timezone
from backend.database.db import query_db, execute_db, transaction_scope
from backend.services.station_service import get_station_by_id, recalculate_station_bicycles

def calculate_fare(start_time: datetime, return_time: datetime, hourly_rate: float):
    """
    Calculate duration and fare.
    Formula: Rental Fare = Duration (Hours) × Hourly Rate
    Applies a 1-hour minimum billable duration.
    """
    if isinstance(start_time, str):
        # Parse ISO / SQL timestamp format
        try:
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        except Exception:
            start_time = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')

    if isinstance(return_time, str):
        try:
            return_time = datetime.fromisoformat(return_time.replace('Z', '+00:00'))
        except Exception:
            return_time = datetime.strptime(return_time, '%Y-%m-%d %H:%M:%S')

    total_seconds = max(0, (return_time - start_time).total_seconds())
    raw_hours = total_seconds / 3600.0

    # Minimum 1 hour billing, duration displayed to 2 decimal places
    billable_hours = max(1.0, round(raw_hours, 2))
    total_fare = round(billable_hours * float(hourly_rate), 2)

    return billable_hours, total_fare

def rent_bicycle(user_id: int, bicycle_id: int):
    """
    Initiate bicycle rental using an atomic transaction to prevent double rental.
    """
    # 1. Check if user already has an active rental
    active_rental = query_db(
        "SELECT rental_id FROM rental WHERE user_id = %s AND status = 'Active'",
        (user_id,),
        one=True
    )
    if active_rental:
        return None, "You already have an active rental in progress. Please return your current bicycle before renting another."

    # 2. Check bicycle existence
    bike = query_db(
        "SELECT bicycle_id, bicycle_number, status, rental_rate, station_id FROM bicycle WHERE bicycle_id = %s",
        (bicycle_id,),
        one=True
    )
    if not bike:
        return None, "Bicycle not found."

    if bike['status'] != 'Available':
        return None, f"Bicycle {bike['bicycle_number']} is currently not available for rent (Status: {bike['status']})."

    start_station_id = bike['station_id']
    now = datetime.now()

    # 3. Atomic reservation: Update bicycle status to 'Rented' only if still 'Available'
    with transaction_scope():
        res = execute_db(
            """
            UPDATE bicycle
            SET status = 'Rented', station_id = NULL
            WHERE bicycle_id = %s AND status = 'Available'
            """,
            (bicycle_id,),
            commit=False
        )

        if res['rowcount'] == 0:
            return None, "Bicycle was just rented by another user or is unavailable."

        # Insert rental record
        rental_res = execute_db(
            """
            INSERT INTO rental (user_id, bicycle_id, start_station_id, start_time, status)
            VALUES (%s, %s, %s, %s, 'Active')
            """,
            (user_id, bicycle_id, start_station_id, now.strftime('%Y-%m-%d %H:%M:%S')),
            commit=False
        )
        rental_id = rental_res['lastrowid']

        # Update station availability
        if start_station_id:
            recalculate_station_bicycles(start_station_id)

    return get_rental_by_id(rental_id), None

def return_bicycle(rental_id: int, return_station_id: int, user_id: int = None, is_admin: bool = False):
    """
    Return a rented bicycle, calculate duration & fare, update station & status, and record payment.
    """
    rental = get_rental_by_id(rental_id)
    if not rental:
        return None, "Rental record not found."

    if rental['status'] != 'Active':
        return None, f"Rental is not active (Current status: {rental['status']})."

    # User authorization check
    if not is_admin and user_id and rental['user_id'] != user_id:
        return None, "Unauthorized: You can only return your own rental."

    # Validate return station
    station = get_station_by_id(return_station_id)
    if not station:
        return None, "Return station not found."

    # Check station capacity: cannot exceed capacity
    if station['available_bicycles'] >= station['capacity']:
        return None, f"Cannot return bicycle to '{station['station_name']}': station is at full capacity ({station['capacity']})."

    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    duration, fare = calculate_fare(rental['start_time'], now, rental['rental_rate'])

    with transaction_scope():
        # Update rental record
        execute_db(
            """
            UPDATE rental
            SET return_time = %s, return_station_id = %s, duration = %s, fare = %s, status = 'Completed'
            WHERE rental_id = %s
            """,
            (now_str, return_station_id, duration, fare, rental_id),
            commit=False
        )

        # Update bicycle status and dock at station
        execute_db(
            """
            UPDATE bicycle
            SET status = 'Available', station_id = %s
            WHERE bicycle_id = %s
            """,
            (return_station_id, rental['bicycle_id']),
            commit=False
        )

        # Create payment record
        execute_db(
            """
            INSERT INTO payment (rental_id, amount, status, payment_date)
            VALUES (%s, %s, 'Paid', %s)
            """,
            (rental_id, fare, now_str),
            commit=False
        )

        # Recalculate return station count
        recalculate_station_bicycles(return_station_id)

    return get_rental_by_id(rental_id), None

def get_rental_by_id(rental_id: int):
    """Retrieve full rental details by ID."""
    query = """
        SELECT r.rental_id, r.user_id, r.bicycle_id, r.start_station_id, r.return_station_id,
               r.start_time, r.return_time, r.duration, r.fare, r.status, r.created_at,
               b.bicycle_number, b.type as bicycle_type, b.rental_rate,
               u.name as user_name, u.email as user_email,
               s_start.station_name as start_station_name,
               s_return.station_name as return_station_name,
               p.payment_id, p.status as payment_status, p.amount as payment_amount, p.payment_date
        FROM rental r
        JOIN bicycle b ON r.bicycle_id = b.bicycle_id
        JOIN `user` u ON r.user_id = u.user_id
        LEFT JOIN station s_start ON r.start_station_id = s_start.station_id
        LEFT JOIN station s_return ON r.return_station_id = s_return.station_id
        LEFT JOIN payment p ON r.rental_id = p.rental_id
        WHERE r.rental_id = %s
    """
    return query_db(query, (rental_id,), one=True)

def get_user_active_rental(user_id: int):
    """Get currently active rental for a user, if any."""
    query = """
        SELECT r.rental_id, r.user_id, r.bicycle_id, r.start_station_id,
               r.start_time, r.status,
               b.bicycle_number, b.type as bicycle_type, b.rental_rate,
               s.station_name as start_station_name
        FROM rental r
        JOIN bicycle b ON r.bicycle_id = b.bicycle_id
        LEFT JOIN station s ON r.start_station_id = s.station_id
        WHERE r.user_id = %s AND r.status = 'Active'
    """
    return query_db(query, (user_id,), one=True)

def get_all_rentals(user_id=None, status=None, owner_id=None):
    """Retrieve rental history with optional filters."""
    query = """
        SELECT r.rental_id, r.user_id, r.bicycle_id, r.start_station_id, r.return_station_id,
               r.start_time, r.return_time, r.duration, r.fare, r.status, r.created_at,
               b.bicycle_number, b.type as bicycle_type, b.rental_rate, b.owner_id,
               u.name as user_name, u.email as user_email,
               s_start.station_name as start_station_name,
               s_return.station_name as return_station_name,
               p.payment_id, p.status as payment_status, p.amount as payment_amount, p.payment_date
        FROM rental r
        JOIN bicycle b ON r.bicycle_id = b.bicycle_id
        JOIN `user` u ON r.user_id = u.user_id
        LEFT JOIN station s_start ON r.start_station_id = s_start.station_id
        LEFT JOIN station s_return ON r.return_station_id = s_return.station_id
        LEFT JOIN payment p ON r.rental_id = p.rental_id
        WHERE 1=1
    """
    args = []
    if user_id:
        query += " AND r.user_id = %s"
        args.append(user_id)
    if status:
        query += " AND r.status = %s"
        args.append(status)
    if owner_id:
        query += " AND b.owner_id = %s"
        args.append(owner_id)

    query += " ORDER BY r.rental_id DESC"
    return query_db(query, tuple(args))

