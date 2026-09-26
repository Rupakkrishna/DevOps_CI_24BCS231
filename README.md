# Public Bicycle Rental Management System (PBRMS)

> A centralized, full-stack web application designed for urban bicycle rental management, connecting **Administrators**, **Customers/Users**, and **Rental Owners**. Built for Software Engineering / Agile Practices, CI/CD with Jenkins, and local local demonstration.

---

## Table of Contents
1. [Project Objective & Problem Statement](#project-objective--problem-statement)
2. [Technology Stack](#technology-stack)
3. [System Architecture](#system-architecture)
4. [Project Structure](#project-structure)
5. [Database Setup & Schema](#database-setup--schema)
6. [Environment Variables](#environment-variables)
7. [Installation & Setup](#installation--setup)
8. [Demo Accounts & Credentials](#demo-accounts--credentials)
9. [Running the Application](#running-the-application)
10. [REST API Overview](#rest-api-overview)
11. [Running Automated Tests](#running-automated-tests)
12. [DevOps & Jenkins CI Pipeline](#devops--jenkins-ci-pipeline)

---

## Project Objective & Problem Statement

Urban mobility requires flexible, eco-friendly, and accessible transportation options. The **Public Bicycle Rental Management System (PBRMS)** provides a centralized platform to manage bicycle inventory, docking stations, live availability, rental transactions, duration and fare calculations, and simulated payments.

### Core User Roles
1. **Admin**: Supervises platform operations, manages docking stations and bicycles, reviews and approves/rejects rental owner applications, and audits rental & payment logs.
2. **Customer / User**: Searches stations, views available bicycles, rents bikes in real time, tracks live ride duration, returns bikes to any station with capacity, and reviews fare receipts.
3. **Rental Owner**: Registers fleet bicycles, sets hourly rental rates, assigns bicycles to docking stations, toggles maintenance status, and monitors rental earnings.

### Core Rental Workflow
```
Customer Login / Register
         ↓
Customer Dashboard
         ↓
Filter / Select Station
         ↓
View Available Bicycles
         ↓
Select Bicycle & View Hourly Rate
         ↓
Confirm Rental (Status: Available → Rented)
         ↓
Active Rental (Live duration counter & estimated fare)
         ↓
Return Bicycle to Destination Station (Capacity verified)
         ↓
Calculate Elapsed Duration & Fare (Duration × Hourly Rate)
         ↓
Record Payment (Simulated Ledger: Paid)
         ↓
Bicycle Becomes Available at Destination Station
```

---

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Bootstrap Icons. Responsive design for mobile, tablet, and desktop.
- **Backend**: Python 3.10+, Flask, RESTful API architecture, JSON responses, CORS enabled.
- **Authentication**: JWT (JSON Web Tokens) with `HS256`, password hashing via `bcrypt` (12 rounds), role-based access control (RBAC).
- **Database**: MySQL 8 (relational schema with primary/foreign keys, checks, transactions, and row-locking). Includes SQLite zero-config fallback for isolated automated tests and portable demonstrations.
- **Testing**: `pytest` test suite with 100% pass rate covering all 11 required scenarios.
- **DevOps**: Declarative `Jenkinsfile`, `.gitignore`, `requirements.txt`.

---

## System Architecture

```
+-------------------------------------------------------------------------+
|                              FRONTEND                                    |
|   Landing Page  |  Login / Register  |  Customer / Owner / Admin Dashboards  |
|             (Bootstrap 5, Vanilla ES6+ Fetch Client, JWT)               |
+-------------------------------------------------------------------------+
                                    │  HTTPS / JSON
                                    ▼
+-------------------------------------------------------------------------+
|                            BACKEND (Flask)                              |
|  Routes: /api/auth, /api/stations, /api/bicycles, /api/rentals, etc.   |
|  Middleware: JWT Auth, RBAC (@role_required), Input Validators          |
|  Services: StationService, BicycleService, RentalService, PaymentService|
+-------------------------------------------------------------------------+
                                    │  Parameterized Queries / Transactions
                                    ▼
+-------------------------------------------------------------------------+
|                           DATABASE (MySQL 8)                            |
|  admin  |  user  |  rental_owner  |  station  |  bicycle  |  rental  | payment |
+-------------------------------------------------------------------------+
```

---

## Project Structure

```
PBRMS/
│
├── backend/
│   ├── app.py                      # Flask application factory & static file server
│   ├── config.py                   # Environment configuration (Dev, Test, Prod)
│   ├── requirements.txt            # Python dependencies
│   ├── database/
│   │   ├── db.py                   # Connection manager, transactions & query helpers
│   │   └── seed.py                 # Programmatic database seed script
│   ├── routes/
│   │   ├── auth_routes.py          # /api/auth endpoints (register, login, me)
│   │   ├── station_routes.py       # /api/stations CRUD endpoints
│   │   ├── bicycle_routes.py       # /api/bicycles CRUD & availability endpoints
│   │   ├── rental_routes.py        # /api/rentals lifecycle endpoints
│   │   ├── payment_routes.py       # /api/payments ledger endpoints
│   │   └── admin_routes.py         # /api/admin metrics & owner approvals
│   ├── services/
│   │   ├── auth_service.py         # Registration, bcrypt hashing, JWT tokens
│   │   ├── station_service.py      # Station CRUD & capacity enforcement
│   │   ├── bicycle_service.py      # Fleet inventory & status transitions
│   │   ├── rental_service.py       # Atomic rental booking, return, fare calculation
│   │   └── payment_service.py      # Payment ledger records
│   └── utils/
│       ├── auth_middleware.py      # JWT decorators (@token_required, @role_required)
│       └── validators.py           # Email, password, phone, and payload validators
│
├── frontend/
│   ├── index.html                  # Landing page with live station directory
│   ├── login.html                  # Unified login with quick demo buttons
│   ├── register.html               # Customer & Rental Owner registration tabs
│   ├── user/
│   │   └── dashboard.html          # Customer portal: bikes, active rental, return, history
│   ├── admin/
│   │   └── dashboard.html          # Admin console: KPIs, approvals, stations, bikes, logs
│   ├── owner/
│   │   └── dashboard.html          # Rental Owner portal: fleet management, station assignments
│   ├── css/
│   │   └── style.css               # Bootstrap custom theme, badges, cards, timers
│   └── js/
│       ├── api.js                  # Centralized Fetch API client & JWT manager
│       ├── auth.js                 # Authentication handlers & demo fill
│       ├── user.js                 # Customer rental flow & live timer
│       ├── admin.js                # Admin management handlers
│       └── owner.js                # Owner fleet handlers
│
├── database/
│   ├── schema.sql                  # MySQL 8 DDL tables, foreign keys, and indexes
│   └── seed.sql                    # Initial seed data SQL
│
├── tests/
│   ├── conftest.py                 # Pytest fixtures and test database setup
│   ├── test_auth.py                # Tests: Registration, Login, Invalid Login, RBAC
│   ├── test_bicycles.py            # Tests: Availability, Status transitions, Capacity
│   ├── test_rentals.py             # Tests: Rental, Double-booking prevention, Return
│   └── test_fare.py                # Tests: Duration rounding & fare formula
│
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── Jenkinsfile                     # Declarative CI pipeline for Jenkins
└── README.md                       # Comprehensive documentation
```

---

## Database Setup & Schema

The database uses MySQL 8 with the following schema:

- **`admin`**: `admin_id`, `name`, `email`, `password`, `created_at`
- **`user`**: `user_id`, `name`, `email`, `phone`, `password`, `created_at`
- **`rental_owner`**: `owner_id`, `name`, `email`, `phone`, `password`, `address`, `approval_status` (`Pending`, `Approved`, `Rejected`), `created_at`
- **`station`**: `station_id`, `station_name`, `location`, `capacity`, `available_bicycles`, `created_at`
- **`bicycle`**: `bicycle_id`, `bicycle_number`, `type`, `status` (`Available`, `Rented`, `Maintenance`, `Inactive`), `rental_rate`, `owner_id` (FK), `station_id` (FK)
- **`rental`**: `rental_id`, `user_id` (FK), `bicycle_id` (FK), `start_station_id` (FK), `return_station_id` (FK), `start_time`, `return_time`, `duration`, `fare`, `status` (`Active`, `Completed`, `Cancelled`)
- **`payment`**: `payment_id`, `rental_id` (FK), `amount`, `status` (`Pending`, `Paid`, `Failed`), `payment_date`

### Initializing the Database in MySQL

1. Start your local MySQL server (e.g. via Windows Services or command line):
   ```powershell
   net start MySQL80
   ```
2. Execute the schema and seed scripts using the MySQL CLI:
   ```bash
   mysql -u root -p < database/schema.sql
   mysql -u root -p < database/seed.sql
   ```
3. Or initialize programmatically using Python:
   ```bash
   python -m backend.database.seed
   ```

---

## Environment Variables

Copy `.env.example` to `.env` and configure your local database credentials:

```bash
cp .env.example .env
```

Example `.env` content:
```ini
FLASK_ENV=development
SECRET_KEY=pbrms-super-secret-key-change-in-production-2026
JWT_EXPIRY_HOURS=24
PORT=5000

# MySQL 8 Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=pbrms_db

# SQLite Fallback (set to false to force MySQL only)
USE_SQLITE_FALLBACK=true
```

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd PBRMS
   ```

2. **Create and activate a virtual environment**:
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Initialize seed data**:
   ```bash
   python -m backend.database.seed
   ```

---

## Demo Accounts & Credentials

The database comes preloaded with demonstration accounts for each role:

| Role | Name | Email | Password | Status / Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Admin** | System Administrator | `admin@pbrms.com` | `Admin@123` | Full system access |
| **Customer** | Alice Johnson | `alice@example.com` | `User@123` | Has 1 active rental |
| **Customer** | Bob Smith | `bob@example.com` | `User@123` | Has 1 completed rental |
| **Rental Owner** | John Doe (Metro Bikes) | `john.bikes@example.com` | `Owner@123` | **Approved** (8 bicycles) |
| **Rental Owner** | Sarah Connor (Eco Cycles) | `sarah.rentals@example.com` | `Owner@123` | **Pending** approval |
| **Rental Owner** | Mike Miller (Express Fleet)| `mike.cycles@example.com` | `Owner@123` | **Rejected** |

> **Tip**: On the login page (`login.html`), click the quick-fill buttons (**Admin**, **Customer**, **Rental Owner**) to instantly populate credentials.

---

## Running the Application

Start the Flask application server:

```bash
python backend/app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

- **Landing Page**: `http://127.0.0.1:5000/index.html`
- **Login Page**: `http://127.0.0.1:5000/login.html`
- **Register Page**: `http://127.0.0.1:5000/register.html`
- **Customer Portal**: `http://127.0.0.1:5000/user/dashboard.html`
- **Admin Console**: `http://127.0.0.1:5000/admin/dashboard.html`
- **Rental Owner Portal**: `http://127.0.0.1:5000/owner/dashboard.html`

---

## REST API Overview

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Register customer or rental owner |
| `POST` | `/api/auth/login` | Public | Authenticate user & return JWT token |
| `POST` | `/api/auth/logout` | Public | Clear session/token |
| `GET` | `/api/auth/me` | Authenticated | Get current user profile |
| `GET` | `/api/stations` | Public | List all docking stations |
| `POST` | `/api/stations` | Admin | Create docking station |
| `PUT` | `/api/stations/<id>` | Admin | Update station details & capacity |
| `DELETE` | `/api/stations/<id>` | Admin | Delete station (if empty) |
| `GET` | `/api/bicycles` | Public | List bicycles (with filters) |
| `GET` | `/api/bicycles/available` | Public | List available bicycles only |
| `POST` | `/api/bicycles` | Admin, Owner | Add a new bicycle to fleet |
| `PUT` | `/api/bicycles/<id>` | Admin, Owner | Update bicycle or station assignment |
| `DELETE` | `/api/bicycles/<id>` | Admin, Owner | Remove bicycle |
| `POST` | `/api/rentals` | Customer | Rent a bicycle (atomic transaction) |
| `GET` | `/api/rentals/active` | Customer | Get ongoing active rental |
| `POST` | `/api/rentals/<id>/return` | Customer, Admin | Return bicycle & calculate fare |
| `GET` | `/api/rentals` | Authenticated | List rental history |
| `GET` | `/api/payments` | Authenticated | View simulated payment ledger |
| `GET` | `/api/admin/dashboard` | Admin | Aggregate KPI metrics |
| `POST` | `/api/admin/owners/<id>/status`| Admin | Approve or Reject rental owner |

---

## Running Automated Tests

The test suite covers all 11 required test cases using `pytest`:

```bash
python -m pytest tests/ -v
```

### Verified Test Cases:
1. `test_user_registration`: Customer and rental owner account creation with validations.
2. `test_login_success`: Valid credential verification for all three roles.
3. `test_invalid_login`: Rejection of wrong password, nonexistent email, and unapproved owners.
4. `test_bicycle_availability`: Confirms available list excludes `Rented`, `Maintenance`, and `Inactive` bikes.
5. `test_bicycle_rental_lifecycle`: Status change to `Rented` and station availability decrement.
6. `test_prevent_double_rental`: Concurrency safeguard preventing duplicate rental of the same bike.
7. `test_return_bicycle`: Status change to `Available`, fare calculation, and station count increment.
8. `test_fare_calculation`: Accurate fare calculation with a 1-hour minimum billable duration.
9. `test_bicycle_status_transition`: Complete state transitions (`Available` ↔ `Maintenance`).
10. `test_station_availability_update_and_capacity`: Enforces station capacity limits upon docking.
11. `test_unauthorized_endpoint_access`: Access control rejection (HTTP 401 and 403).

---

## DevOps & Jenkins CI Pipeline

A declarative `Jenkinsfile` is provided in the repository root. The pipeline executes:

1. **Checkout**: Checks out source code from the Git repository.
2. **Build**: Configures the Python virtual environment and installs `requirements.txt`.
3. **Test**: Executes `pytest tests/ -v --junitxml=junit.xml`.
4. **Result**: Archives JUnit test results and reports pipeline build status.

### Setting up Jenkins:
1. In your Jenkins dashboard, create a new **Pipeline** job.
2. Under **Pipeline Definition**, select **Pipeline script from SCM**.
3. Choose **Git**, provide the repository URL and branch (`main`).
4. Script Path: `Jenkinsfile`.
5. Run **Build Now** to verify continuous integration.

