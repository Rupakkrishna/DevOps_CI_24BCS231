-- =======================================================
-- PUBLIC BICYCLE RENTAL MANAGEMENT SYSTEM (PBRMS)
-- Database Schema: MySQL 8
-- =======================================================

CREATE DATABASE IF NOT EXISTS pbrms_db;
USE pbrms_db;

-- Drop tables in reverse order of foreign key dependencies
DROP TABLE IF EXISTS payment;
DROP TABLE IF EXISTS rental;
DROP TABLE IF EXISTS bicycle;
DROP TABLE IF EXISTS station;
DROP TABLE IF EXISTS rental_owner;
DROP TABLE IF EXISTS `user`;
DROP TABLE IF EXISTS `admin`;

-- 1. ADMIN TABLE
CREATE TABLE `admin` (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. USER (CUSTOMER) TABLE
CREATE TABLE `user` (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. RENTAL OWNER TABLE
CREATE TABLE rental_owner (
    owner_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    password VARCHAR(255) NOT NULL,
    address TEXT,
    approval_status ENUM('Pending', 'Approved', 'Rejected') NOT NULL DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. STATION TABLE
CREATE TABLE station (
    station_id INT AUTO_INCREMENT PRIMARY KEY,
    station_name VARCHAR(100) NOT NULL,
    location VARCHAR(255) NOT NULL,
    capacity INT NOT NULL,
    available_bicycles INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_station_capacity CHECK (capacity > 0),
    CONSTRAINT chk_station_available CHECK (available_bicycles >= 0 AND available_bicycles <= capacity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. BICYCLE TABLE
CREATE TABLE bicycle (
    bicycle_id INT AUTO_INCREMENT PRIMARY KEY,
    bicycle_number VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(50) NOT NULL,
    status ENUM('Available', 'Rented', 'Maintenance', 'Inactive') NOT NULL DEFAULT 'Available',
    rental_rate DECIMAL(10, 2) NOT NULL,
    owner_id INT NOT NULL,
    station_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_bicycle_rate CHECK (rental_rate >= 0),
    CONSTRAINT fk_bicycle_owner FOREIGN KEY (owner_id) REFERENCES rental_owner (owner_id) ON DELETE CASCADE,
    CONSTRAINT fk_bicycle_station FOREIGN KEY (station_id) REFERENCES station (station_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. RENTAL TABLE
CREATE TABLE rental (
    rental_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    bicycle_id INT NOT NULL,
    start_station_id INT NULL,
    return_station_id INT NULL,
    start_time DATETIME NOT NULL,
    return_time DATETIME NULL,
    duration DECIMAL(10, 2) NULL,
    fare DECIMAL(10, 2) NULL,
    status ENUM('Active', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_rental_user FOREIGN KEY (user_id) REFERENCES `user` (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_rental_bicycle FOREIGN KEY (bicycle_id) REFERENCES bicycle (bicycle_id) ON DELETE CASCADE,
    CONSTRAINT fk_rental_start_station FOREIGN KEY (start_station_id) REFERENCES station (station_id) ON DELETE SET NULL,
    CONSTRAINT fk_rental_return_station FOREIGN KEY (return_station_id) REFERENCES station (station_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. PAYMENT TABLE
CREATE TABLE payment (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    rental_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status ENUM('Pending', 'Paid', 'Failed') NOT NULL DEFAULT 'Pending',
    payment_date DATETIME NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_payment_amount CHECK (amount >= 0),
    CONSTRAINT fk_payment_rental FOREIGN KEY (rental_id) REFERENCES rental (rental_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- INDEXES FOR PERFORMANCE & LOOKUPS
CREATE INDEX idx_bicycle_status ON bicycle (status);
CREATE INDEX idx_bicycle_station ON bicycle (station_id);
CREATE INDEX idx_rental_user ON rental (user_id);
CREATE INDEX idx_rental_status ON rental (status);
CREATE INDEX idx_payment_rental ON payment (rental_id);
CREATE INDEX idx_owner_approval ON rental_owner (approval_status);

