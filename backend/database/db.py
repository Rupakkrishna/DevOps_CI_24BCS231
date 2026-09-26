import os
import pymysql
import pymysql.cursors
import sqlite3
from flask import current_app, g
from contextlib import contextmanager

def get_db():
    """Get or create database connection for the current application context."""
    if 'db' not in g:
        is_testing = current_app.config.get('TESTING', False)
        use_sqlite_test = current_app.config.get('USE_SQLITE_TEST', False) and is_testing

        if use_sqlite_test:
            sqlite_path = current_app.config.get('SQLITE_DB_PATH', ':memory:')
            conn = sqlite3.connect(sqlite_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            g.db = conn
            g.is_sqlite = True
            return g.db

        # Try connecting to MySQL
        try:
            g.db = pymysql.connect(
                host=current_app.config.get('DB_HOST', '127.0.0.1'),
                port=current_app.config.get('DB_PORT', 3306),
                user=current_app.config.get('DB_USER', 'root'),
                password=current_app.config.get('DB_PASSWORD', ''),
                database=current_app.config.get('DB_NAME', 'pbrms_db'),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=False,
                connect_timeout=3
            )
            g.is_sqlite = False
        except Exception as mysql_err:
            if current_app.config.get('USE_SQLITE_FALLBACK', False):
                # Fallback to local SQLite database
                sqlite_path = current_app.config.get('SQLITE_DB_PATH')
                conn = sqlite3.connect(sqlite_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA foreign_keys = ON;")
                g.db = conn
                g.is_sqlite = True
            else:
                raise mysql_err
    return g.db

def close_db(e=None):
    """Close database connection at the end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def _adapt_query(query, is_sqlite):
    """Adapt MySQL query syntax to SQLite if running under SQLite test mode."""
    if is_sqlite:
        # Replace %s with ? for parameterized queries in sqlite3
        query = query.replace('%s', '?')
        # Replace NOW() with CURRENT_TIMESTAMP
        query = query.replace('NOW()', 'CURRENT_TIMESTAMP')
        # Replace CURDATE() with DATE('now')
        query = query.replace('CURDATE()', "DATE('now')")
    return query

def query_db(query, args=(), one=False):
    """Execute a read query and return dictionary rows."""
    conn = get_db()
    is_sqlite = getattr(g, 'is_sqlite', False)
    adapted_query = _adapt_query(query, is_sqlite)

    if is_sqlite:
        cur = conn.cursor()
        cur.execute(adapted_query, args)
        rows = cur.fetchall()
        cur.close()
        results = [dict(row) for row in rows]
        return (results[0] if results else None) if one else results
    else:
        with conn.cursor() as cur:
            cur.execute(adapted_query, args)
            results = cur.fetchall()
            return (results[0] if results else None) if one else results

def execute_db(query, args=(), commit=True):
    """Execute an insert, update, or delete query and return affected rows and lastrowid."""
    conn = get_db()
    is_sqlite = getattr(g, 'is_sqlite', False)
    adapted_query = _adapt_query(query, is_sqlite)

    if is_sqlite:
        cur = conn.cursor()
        cur.execute(adapted_query, args)
        last_id = cur.lastrowid
        rowcount = cur.rowcount
        cur.close()
        if commit:
            conn.commit()
        return {'lastrowid': last_id, 'rowcount': rowcount}
    else:
        with conn.cursor() as cur:
            cur.execute(adapted_query, args)
            last_id = cur.lastrowid
            rowcount = cur.rowcount
        if commit:
            conn.commit()
        return {'lastrowid': last_id, 'rowcount': rowcount}

@contextmanager
def transaction_scope():
    """Transactional context manager for atomic multi-statement operations."""
    conn = get_db()
    is_sqlite = getattr(g, 'is_sqlite', False)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise

def init_db_schema(schema_sql_path=None):
    """Initialize database tables using schema SQL."""
    conn = get_db()
    is_sqlite = getattr(g, 'is_sqlite', False)
    
    if schema_sql_path is None:
        schema_sql_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'schema.sql'
        )
        if not os.path.exists(schema_sql_path):
            schema_sql_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', '..', 'database', 'schema.sql'
            )

    with open(schema_sql_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    if is_sqlite:
        # Convert MySQL-specific DDL to SQLite compatible DDL
        sqlite_ddl = """
        DROP TABLE IF EXISTS payment;
        DROP TABLE IF EXISTS rental;
        DROP TABLE IF EXISTS bicycle;
        DROP TABLE IF EXISTS station;
        DROP TABLE IF EXISTS rental_owner;
        DROP TABLE IF EXISTS user;
        DROP TABLE IF EXISTS admin;

        CREATE TABLE admin (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE user (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE rental_owner (
            owner_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            password TEXT NOT NULL,
            address TEXT,
            approval_status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE station (
            station_id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT NOT NULL,
            location TEXT NOT NULL,
            capacity INTEGER NOT NULL,
            available_bicycles INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE bicycle (
            bicycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bicycle_number TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available',
            rental_rate REAL NOT NULL,
            owner_id INTEGER NOT NULL,
            station_id INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES rental_owner (owner_id) ON DELETE CASCADE,
            FOREIGN KEY (station_id) REFERENCES station (station_id) ON DELETE SET NULL
        );

        CREATE TABLE rental (
            rental_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            bicycle_id INTEGER NOT NULL,
            start_station_id INTEGER NULL,
            return_station_id INTEGER NULL,
            start_time TIMESTAMP NOT NULL,
            return_time TIMESTAMP NULL,
            duration REAL NULL,
            fare REAL NULL,
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (user_id) ON DELETE CASCADE,
            FOREIGN KEY (bicycle_id) REFERENCES bicycle (bicycle_id) ON DELETE CASCADE,
            FOREIGN KEY (start_station_id) REFERENCES station (station_id) ON DELETE SET NULL,
            FOREIGN KEY (return_station_id) REFERENCES station (station_id) ON DELETE SET NULL
        );

        CREATE TABLE payment (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            rental_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            payment_date TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rental_id) REFERENCES rental (rental_id) ON DELETE CASCADE
        );
        """
        cur = conn.cursor()
        cur.executescript(sqlite_ddl)
        conn.commit()
        cur.close()
    else:
        # MySQL execution
        with conn.cursor() as cur:
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]
            for stmt in statements:
                # Skip CREATE DATABASE or USE statements if already connected
                if stmt.upper().startswith('CREATE DATABASE') or stmt.upper().startswith('USE '):
                    continue
                cur.execute(stmt)
        conn.commit()
