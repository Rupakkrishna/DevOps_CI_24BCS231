import os
import sys
from backend.app import create_app
from backend.database.db import get_db, execute_db, query_db, init_db_schema

def seed_database():
    """Populate database with demo accounts, stations, bicycles, and sample rentals."""
    app = create_app()
    with app.app_context():
        init_db_schema()

        # Check if already seeded
        admin_exists = query_db("SELECT admin_id FROM `admin` WHERE email = %s", ('admin@pbrms.com',), one=True)
        if admin_exists:
            print("Database already contains seed data. Re-initializing...")

        # 1. Admin
        execute_db(
            "INSERT INTO `admin` (admin_id, name, email, password) VALUES (%s, %s, %s, %s)",
            (1, 'System Administrator', 'admin@pbrms.com', '$2b$12$gCg62WS5GbEO4FN/iuC8UOoDkNlF3mNn8iamfyrYZjYAOzGm6T9sa')
        )

        # 2. Customers
        users = [
            (1, 'Alice Johnson', 'alice@example.com', '+1 555-0101', '$2b$12$MeXw/1UnL3CFvBRekIpUGOhi9WhUNg45nz4MMP3swA1wU0zS1kV02'),
            (2, 'Bob Smith', 'bob@example.com', '+1 555-0102', '$2b$12$MeXw/1UnL3CFvBRekIpUGOhi9WhUNg45nz4MMP3swA1wU0zS1kV02')
        ]
        for u in users:
            execute_db("INSERT INTO `user` (user_id, name, email, phone, password) VALUES (%s, %s, %s, %s, %s)", u)

        # 3. Rental Owners
        owners = [
            (1, 'John Doe (Metro Bikes)', 'john.bikes@example.com', '+1 555-0201', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '123 Greenway Blvd, Downtown', 'Approved'),
            (2, 'Sarah Connor (Eco Cycles)', 'sarah.rentals@example.com', '+1 555-0202', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '456 Bayfront Ave, Waterfront', 'Pending'),
            (3, 'Mike Miller (Express Fleet)', 'mike.cycles@example.com', '+1 555-0203', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '789 Uptown Rd, North End', 'Rejected')
        ]
        for o in owners:
            execute_db("INSERT INTO rental_owner (owner_id, name, email, phone, password, address, approval_status) VALUES (%s, %s, %s, %s, %s, %s, %s)", o)

        # 4. Stations
        stations = [
            (1, 'Central Metro Station', '100 Downtown Plaza, Central District', 15, 2),
            (2, 'University North Gate', '250 Campus Dr, North District', 10, 2),
            (3, 'Waterfront Pier 4', '500 Harbor Boulevard, Waterfront', 12, 1),
            (4, 'Tech Park East Plaza', '800 Innovation Way, East Suburb', 8, 0)
        ]
        for s in stations:
            execute_db("INSERT INTO station (station_id, station_name, location, capacity, available_bicycles) VALUES (%s, %s, %s, %s, %s)", s)

        # 5. Bicycles
        bikes = [
            (1, 'BK-101', 'City', 'Available', 5.00, 1, 1),
            (2, 'BK-102', 'City', 'Available', 5.00, 1, 1),
            (3, 'BK-103', 'Road', 'Available', 7.50, 1, 2),
            (4, 'BK-104', 'Electric', 'Available', 10.00, 1, 2),
            (5, 'BK-105', 'Mountain', 'Available', 8.00, 1, 3),
            (6, 'BK-106', 'Electric', 'Rented', 12.00, 1, None),
            (7, 'BK-107', 'Hybrid', 'Maintenance', 6.00, 1, 3),
            (8, 'BK-108', 'Road', 'Inactive', 7.00, 1, None)
        ]
        for b in bikes:
            execute_db("INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES (%s, %s, %s, %s, %s, %s, %s)", b)

        # 6. Rentals
        execute_db(
            "INSERT INTO rental (rental_id, user_id, bicycle_id, start_station_id, return_station_id, start_time, return_time, duration, fare, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (1, 2, 1, 1, 1, '2026-09-20 10:00:00', '2026-09-20 12:00:00', 2.00, 10.00, 'Completed')
        )
        execute_db(
            "INSERT INTO rental (rental_id, user_id, bicycle_id, start_station_id, return_station_id, start_time, return_time, duration, fare, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (2, 1, 6, 2, None, '2026-09-21 19:30:00', None, None, None, 'Active')
        )

        # 7. Payments
        execute_db(
            "INSERT INTO payment (payment_id, rental_id, amount, status, payment_date) VALUES (%s, %s, %s, %s, %s)",
            (1, 1, 10.00, 'Paid', '2026-09-20 12:01:00')
        )

        print("Database seeded successfully with demo accounts, stations, and bicycles.")

if __name__ == '__main__':
    seed_database()

