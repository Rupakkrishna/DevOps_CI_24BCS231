from backend.database.db import query_db, execute_db

def get_all_stations():
    """Retrieve all stations with their current bicycle counts."""
    query = """
        SELECT s.station_id, s.station_name, s.location, s.capacity,
               s.available_bicycles, s.created_at,
               (SELECT COUNT(*) FROM bicycle b WHERE b.station_id = s.station_id) as total_bicycles
        FROM station s
        ORDER BY s.station_name ASC
    """
    return query_db(query)

def get_station_by_id(station_id: int):
    """Retrieve a single station by ID."""
    query = """
        SELECT s.station_id, s.station_name, s.location, s.capacity,
               s.available_bicycles, s.created_at,
               (SELECT COUNT(*) FROM bicycle b WHERE b.station_id = s.station_id) as total_bicycles
        FROM station s
        WHERE s.station_id = %s
    """
    return query_db(query, (station_id,), one=True)

def create_station(station_name: str, location: str, capacity: int):
    """Create a new docking station."""
    if capacity <= 0:
        return None, "Station capacity must be greater than 0."

    res = execute_db(
        "INSERT INTO station (station_name, location, capacity, available_bicycles) VALUES (%s, %s, %s, 0)",
        (station_name, location, capacity)
    )
    return get_station_by_id(res['lastrowid']), None

def update_station(station_id: int, station_name: str, location: str, capacity: int):
    """Update an existing station's details and capacity."""
    station = get_station_by_id(station_id)
    if not station:
        return None, "Station not found."

    if capacity < station['available_bicycles']:
        return None, f"Capacity cannot be reduced below currently docked bicycles ({station['available_bicycles']})."

    execute_db(
        "UPDATE station SET station_name = %s, location = %s, capacity = %s WHERE station_id = %s",
        (station_name, location, capacity, station_id)
    )
    return get_station_by_id(station_id), None

def delete_station(station_id: int):
    """Delete a station if no bicycles are docked at it."""
    station = get_station_by_id(station_id)
    if not station:
        return False, "Station not found."

    docked_bikes = query_db(
        "SELECT COUNT(*) as count FROM bicycle WHERE station_id = %s",
        (station_id,),
        one=True
    )
    if docked_bikes and docked_bikes['count'] > 0:
        return False, f"Cannot delete station: {docked_bikes['count']} bicycle(s) are currently assigned to it."

    execute_db("DELETE FROM station WHERE station_id = %s", (station_id,))
    return True, None

def recalculate_station_bicycles(station_id: int):
    """Recalculate and update the available_bicycles count for a station."""
    count_row = query_db(
        "SELECT COUNT(*) as count FROM bicycle WHERE station_id = %s AND status = 'Available'",
        (station_id,),
        one=True
    )
    count = count_row['count'] if count_row else 0
    execute_db("UPDATE station SET available_bicycles = %s WHERE station_id = %s", (count, station_id))
    return count

