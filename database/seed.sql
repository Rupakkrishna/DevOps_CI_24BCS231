-- =======================================================
-- PUBLIC BICYCLE RENTAL MANAGEMENT SYSTEM (PBRMS)
-- Database Seed Data: MySQL 8
-- =======================================================

USE pbrms_db;

-- 1. SEED ADMIN
-- Password: Admin@123
INSERT INTO `admin` (admin_id, name, email, password) VALUES
(1, 'System Administrator', 'admin@pbrms.com', '$2b$12$gCg62WS5GbEO4FN/iuC8UOoDkNlF3mNn8iamfyrYZjYAOzGm6T9sa')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 2. SEED CUSTOMERS / USERS
-- Password: User@123
INSERT INTO `user` (user_id, name, email, phone, password) VALUES
(1, 'Alice Johnson', 'alice@example.com', '+1 555-0101', '$2b$12$MeXw/1UnL3CFvBRekIpUGOhi9WhUNg45nz4MMP3swA1wU0zS1kV02'),
(2, 'Bob Smith', 'bob@example.com', '+1 555-0102', '$2b$12$MeXw/1UnL3CFvBRekIpUGOhi9WhUNg45nz4MMP3swA1wU0zS1kV02')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. SEED RENTAL OWNERS
-- Password: Owner@123
INSERT INTO rental_owner (owner_id, name, email, phone, password, address, approval_status) VALUES
(1, 'John Doe (Metro Bikes)', 'john.bikes@example.com', '+1 555-0201', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '123 Greenway Blvd, Downtown', 'Approved'),
(2, 'Sarah Connor (Eco Cycles)', 'sarah.rentals@example.com', '+1 555-0202', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '456 Bayfront Ave, Waterfront', 'Pending'),
(3, 'Mike Miller (Express Fleet)', 'mike.cycles@example.com', '+1 555-0203', '$2b$12$nPRmBeRE/r8CXgRMqEXbRu7hbkQv4IGOjBgWKsWeN4leYS0H6pHYS', '789 Uptown Rd, North End', 'Rejected')
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 4. SEED STATIONS
INSERT INTO station (station_id, station_name, location, capacity, available_bicycles) VALUES
(1, 'Central Metro Station', '100 Downtown Plaza, Central District', 15, 2),
(2, 'University North Gate', '250 Campus Dr, North District', 10, 2),
(3, 'Waterfront Pier 4', '500 Harbor Boulevard, Waterfront', 12, 1),
(4, 'Tech Park East Plaza', '800 Innovation Way, East Suburb', 8, 0)
ON DUPLICATE KEY UPDATE station_name=VALUES(station_name);

-- 5. SEED BICYCLES
INSERT INTO bicycle (bicycle_id, bicycle_number, type, status, rental_rate, owner_id, station_id) VALUES
(1, 'BK-101', 'City', 'Available', 5.00, 1, 1),
(2, 'BK-102', 'City', 'Available', 5.00, 1, 1),
(3, 'BK-103', 'Road', 'Available', 7.50, 1, 2),
(4, 'BK-104', 'Electric', 'Available', 10.00, 1, 2),
(5, 'BK-105', 'Mountain', 'Available', 8.00, 1, 3),
(6, 'BK-106', 'Electric', 'Rented', 12.00, 1, NULL),
(7, 'BK-107', 'Hybrid', 'Maintenance', 6.00, 1, 3),
(8, 'BK-108', 'Road', 'Inactive', 7.00, 1, NULL)
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- 6. SEED RENTALS
-- Completed rental for Bob
INSERT INTO rental (rental_id, user_id, bicycle_id, start_station_id, return_station_id, start_time, return_time, duration, fare, status) VALUES
(1, 2, 1, 1, 1, '2026-09-20 10:00:00', '2026-09-20 12:00:00', 2.00, 10.00, 'Completed')
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- Active rental for Alice
INSERT INTO rental (rental_id, user_id, bicycle_id, start_station_id, return_station_id, start_time, return_time, duration, fare, status) VALUES
(2, 1, 6, 2, NULL, '2026-09-21 19:30:00', NULL, NULL, NULL, 'Active')
ON DUPLICATE KEY UPDATE status=VALUES(status);

-- 7. SEED PAYMENTS
INSERT INTO payment (payment_id, rental_id, amount, status, payment_date) VALUES
(1, 1, 10.00, 'Paid', '2026-09-20 12:01:00')
ON DUPLICATE KEY UPDATE status=VALUES(status);

