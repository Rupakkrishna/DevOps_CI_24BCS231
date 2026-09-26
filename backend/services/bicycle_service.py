from backend.database.db import query_db, execute_db, transaction_scope
from backend.services.station_service import recalculate_station_bicycles, get_station_by_id

VALID_STATUSES = ['Available', 'Rented', 'Maintenance', 'Inactive']
VALID_TYPES = ['City', 'Mountain', 'Road', 'Electric', 'Hybrid']

def get_all_bicycles(station_id=None, status=None, owner_id=None, bicycle_type=None):
    """Retrieve bicycles with optional filtering."""
    query = """
        SELECT b.bicycle_id, b.bicycle_number, b.type, b.status, b.rental_rate,
               b.owner_id, b.station_id, b.created_at,
               s.station_name, s.location as station_location,
               ro.name as owner_name, ro.email as owner_email
        FROM bicycle b
        LEFT JOIN station s ON b.station_id = s.station_id
        LEFT JOIN rental_owner ro ON b.owner_id = ro.owner_id
        WHERE 1=1
    """
    args = []
    if station_id is not None:
        query += " AND b.station_id = %s"
        args.append(station_id)
    if status:
        query += " AND b.status = %s"
        args.append(status)
    if owner_id is not None:
        query += " AND b.owner_id = %s"
        args.append(owner_id)
    if bicycle_type:
        query += " AND b.type = %s"
        args.append(bicycle_type)

    query += " ORDER BY b.bicycle_id DESC"
    return query_db(query, tuple(args))

def get_available_bicycles(station_id=None, bicycle_type=None):
    """Retrieve ONLY available bicycles with valid station assignment."""
    query = """
        SELECT b.bicycle_id, b.bicycle_number, b.type, b.status, b.rental_rate,
               b.owner_id, b.station_id, b.created_at,
               s.station_name, s.location as station_location,
               ro.name as owner_name
        FROM bicycle b
        JOIN station s ON b.station_id = s.station_id
        JOIN rental_owner ro ON b.owner_id = ro.owner_id
        WHERE b.status = 'Available'
    """
    args = []
    if station_id is not None:
        query += " AND b.station_id = %s"
        args.append(station_id)
    if bicycle_type:
        query += " AND b.type = %s"
        args.append(bicycle_type)

    query += " ORDER BY b.rental_rate ASC"
    return query_db(query, tuple(args))

def get_bicycle_by_id(bicycle_id: int):
    """Retrieve a single bicycle by ID with station and owner details."""
    query = """
        SELECT b.bicycle_id, b.bicycle_number, b.type, b.status, b.rental_rate,
               b.owner_id, b.station_id, b.created_at,
               s.station_name, s.location as station_location,
               ro.name as owner_name, ro.email as owner_email
        FROM bicycle b
        LEFT JOIN station s ON b.station_id = s.station_id
        LEFT JOIN rental_owner ro ON b.owner_id = ro.owner_id
        WHERE b.bicycle_id = %s
    """
    return query_db(query, (bicycle_id,), one=True)

def create_bicycle(bicycle_number: str, bicycle_type: str, rental_rate: float, owner_id: int, station_id: int = None, status: str = 'Available'):
    """Create a new bicycle and dock at station if specified."""
    # Check duplicate bicycle_number
    existing = query_db("SELECT bicycle_id FROM bicycle WHERE bicycle_number = %s", (bicycle_number,), one=True)
    if existing:
        return None, f"Bicycle number '{bicycle_number}' already exists."

    if status not in VALID_STATUSES:
        return None, f"Invalid status '{status}'. Must be one of {VALID_STATUSES}."

    if station_id:
        station = get_station_by_id(station_id)
        if not station:
            return None, "Selected station does not exist."
        # If adding as Available, check capacity
        if status == 'Available' and station['available_bicycles'] >= station['capacity']:
            return None, f"Station '{station['station_name']}' is at full capacity ({station['capacity']})."

    with transaction_scope():
        res = execute_db(
            "INSERT INTO bicycle (bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (%s, %s, %s, %s, %s, %s)",
            (bicycle_number, bicycle_type, status, rental_rate, owner_id, station_id),
            commit=False
        )
        bicycle_id = res['lastrowid']
        if station_id:
            recalculate_station_bicycles(station_id)

    return get_bicycle_by_id(bicycle_id), None

def update_bicycle(bicycle_id: int, bicycle_type: str = None, rental_rate: float = None, status: str = None, station_id: int = None, user_role: str = 'admin', user_id: int = None):
    """Update bicycle information, status, or station assignment."""
    bike = get_bicycle_by_id(bicycle_id)
    if not bike:
        return None, "Bicycle not found."

    # Authorization check: rental owners can only update their own bicycles
    if user_role == 'rental_owner' and bike['owner_id'] != user_id:
        return None, "Unauthorized: You do not own this bicycle."

    if status and status not in VALID_STATUSES:
        return None, f"Invalid status '{status}'. Must be one of {VALID_STATUSES}."

    # Cannot manually set status to Rented (only the rental workflow does this)
    if status == 'Rented' and bike['status'] != 'Rented':
        return None, "Status cannot be manually changed to 'Rented'. It must be rented through the rental flow."

    old_station_id = bike['station_id']
    target_station_id = station_id if station_id is not None else old_station_id
    target_status = status if status is not None else bike['status']

    # If assigning to a station or becoming Available, check station capacity
    if target_station_id and target_status == 'Available':
        # If moving to a new station or becoming available at current station
        if target_station_id != old_station_id or bike['status'] != 'Available':
            station = get_station_by_id(target_station_id)
            if not station:
                return None, "Target station not found."
            if station['available_bicycles'] >= station['capacity']:
                return None, f"Cannot assign to station '{station['station_name']}': capacity exceeded ({station['capacity']})."

    new_type = bicycle_type if bicycle_type is not None else bike['type']
    new_rate = rental_rate if rental_rate is not None else bike['rental_rate']

    with transaction_scope():
        execute_db(
            """
            UPDATE bicycle
            SET type = %s, rental_rate = %s, status = %s, station_id = %s
            WHERE bicycle_id = %s
            """,
            (new_type, new_rate, target_status, target_station_id, bicycle_id),
            commit=False
        )
        if old_station_id:
            recalculate_station_bicycles(old_station_id)
        if target_station_id and target_station_id != old_station_id:
            recalculate_station_bicycles(target_station_id)

    return get_bicycle_by_id(bicycle_id), None

def delete_bicycle(bicycle_id: int, user_role: str = 'admin', user_id: int = None):
    """Delete a bicycle if it is not currently rented."""
    bike = get_bicycle_by_id(bicycle_id)
    if not bike:
        return False, "Bicycle not found."

    if user_role == 'rental_owner' and bike['owner_id'] != user_id:
        return False, "Unauthorized: You do not own this bicycle."

    if bike['status'] == 'Rented':
        return False, "Cannot delete a bicycle that is currently rented."

    station_id = bike['station_id']
    with transaction_scope():
        execute_db("DELETE FROM bicycle WHERE bicycle_id = %s", (bicycle_id,), commit=False)
        if station_id:
            recalculate_station_bicycles(station_id)

    return True, None

