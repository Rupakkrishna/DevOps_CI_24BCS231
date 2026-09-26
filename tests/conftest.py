import os
import pytest
from backend.app import create_app
from backend.database.db import get_db, execute_db, query_db, init_db_schema
from backend.services.auth_service import hash_password
from backend.utils.auth_middleware import generate_token

@pytest.fixture(scope='session')
def app():
    """Create application configured for testing."""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['USE_SQLITE_TEST'] = 'true'
    test_db_file = os.path.join(os.path.dirname(__file__), 'test_pbrms.sqlite')
    os.environ['SQLITE_DB_PATH'] = test_db_file

    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['USE_SQLITE_TEST'] = True
    app.config['SQLITE_DB_PATH'] = test_db_file

    yield app

    # Cleanup sqlite file after test session
    if os.path.exists(test_db_file):
        try:
            os.remove(test_db_file)
        except Exception:
            pass

@pytest.fixture(autouse=True)
def init_db(app):
    """Initialize fresh schema before each test."""
    with app.app_context():
        init_db_schema()

        # Seed essential test entities
        # Admin
        admin_pass = hash_password('Admin@123')
        execute_db(
            "INSERT INTO admin (admin_id, name, email, password) VALUES (1, 'Admin User', 'admin@test.com', %s)",
            (admin_pass,)
        )

        # Users
        user_pass = hash_password('User@123')
        execute_db(
            "INSERT INTO user (user_id, name, email, phone, password) VALUES (1, 'Test User 1', 'user1@test.com', '1234567890', %s)",
            (user_pass,)
        )
        execute_db(
            "INSERT INTO user (user_id, name, email, phone, password) VALUES (2, 'Test User 2', 'user2@test.com', '1234567891', %s)",
            (user_pass,)
        )

        # Rental Owners
        owner_pass = hash_password('Owner@123')
        execute_db(
            "INSERT INTO rental_owner (owner_id, name, email, phone, password, address, approval_status) VALUES (1, 'Approved Owner', 'owner1@test.com', '1234567892', %s, '123 St', 'Approved')",
            (owner_pass,)
        )
        execute_db(
            "INSERT INTO rental_owner (owner_id, name, email, phone, password, address, approval_status) VALUES (2, 'Pending Owner', 'owner2@test.com', '1234567893', %s, '456 St', 'Pending')",
            (owner_pass,)
        )

        # Stations
        execute_db(
            "INSERT INTO station (station_id, station_name, location, capacity, available_bicycles) VALUES (1, 'Station Alpha', 'Location A', 5, 2)"
        )
        execute_db(
            "INSERT INTO station (station_id, station_name, location, capacity, available_bicycles) VALUES (2, 'Station Beta', 'Location B', 2, 0)"
        )

        # Bicycles
        execute_db(
            "INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (1, 'TEST-101', 'City', 'Available', 5.00, 1, 1)"
        )
        execute_db(
            "INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (2, 'TEST-102', 'Road', 'Available', 8.00, 1, 1)"
        )
        execute_db(
            "INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (3, 'TEST-103', 'Mountain', 'Maintenance', 6.00, 1, 2)"
        )
        execute_db(
            "INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (4, 'TEST-104', 'Electric', 'Inactive', 12.00, 1, NULL)"
        )

@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()

@pytest.fixture
def admin_token(app):
    with app.app_context():
        return generate_token(1, 'admin', 'Admin User', 'admin@test.com')

@pytest.fixture
def user1_token(app):
    with app.app_context():
        return generate_token(1, 'user', 'Test User 1', 'user1@test.com')

@pytest.fixture
def user2_token(app):
    with app.app_context():
        return generate_token(2, 'user', 'Test User 2', 'user2@test.com')

@pytest.fixture
def owner_token(app):
    with app.app_context():
        return generate_token(1, 'rental_owner', 'Approved Owner', 'owner1@test.com')

