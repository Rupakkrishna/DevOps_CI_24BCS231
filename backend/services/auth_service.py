import bcrypt
from backend.database.db import query_db, execute_db
from backend.utils.auth_middleware import generate_token

def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed_password: str) -> bool:
    """Check a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def check_email_exists(email: str) -> bool:
    """Check if an email already exists in any user table."""
    in_user = query_db("SELECT user_id FROM `user` WHERE email = %s", (email,), one=True)
    if in_user:
        return True
    in_owner = query_db("SELECT owner_id FROM rental_owner WHERE email = %s", (email,), one=True)
    if in_owner:
        return True
    in_admin = query_db("SELECT admin_id FROM `admin` WHERE email = %s", (email,), one=True)
    if in_admin:
        return True
    return False

def register_user(name: str, email: str, phone: str, password: str):
    """Register a new customer/user."""
    if check_email_exists(email):
        return None, "Email address is already registered."

    hashed = hash_password(password)
    res = execute_db(
        "INSERT INTO `user` (name, email, phone, password) VALUES (%s, %s, %s, %s)",
        (name, email, phone, hashed)
    )
    user_id = res['lastrowid']
    token = generate_token(user_id, 'user', name, email)
    return {
        'user_id': user_id,
        'name': name,
        'email': email,
        'phone': phone,
        'role': 'user',
        'token': token
    }, None

def register_owner(name: str, email: str, phone: str, password: str, address: str):
    """Register a new rental owner (requires admin approval)."""
    if check_email_exists(email):
        return None, "Email address is already registered."

    hashed = hash_password(password)
    res = execute_db(
        "INSERT INTO rental_owner (name, email, phone, password, address, approval_status) VALUES (%s, %s, %s, %s, %s, 'Pending')",
        (name, email, phone, hashed, address)
    )
    owner_id = res['lastrowid']
    return {
        'owner_id': owner_id,
        'name': name,
        'email': email,
        'phone': phone,
        'address': address,
        'role': 'rental_owner',
        'approval_status': 'Pending',
        'message': 'Registration successful. Your account is pending administrator approval before you can log in.'
    }, None

def login_user(email: str, password: str):
    """Authenticate a user across admin, rental_owner, and customer tables."""
    # 1. Check Admin
    admin = query_db("SELECT * FROM `admin` WHERE email = %s", (email,), one=True)
    if admin and check_password(password, admin['password']):
        token = generate_token(admin['admin_id'], 'admin', admin['name'], admin['email'])
        return {
            'user_id': admin['admin_id'],
            'name': admin['name'],
            'email': admin['email'],
            'role': 'admin',
            'token': token
        }, None

    # 2. Check Rental Owner
    owner = query_db("SELECT * FROM rental_owner WHERE email = %s", (email,), one=True)
    if owner and check_password(password, owner['password']):
        if owner['approval_status'] == 'Pending':
            return None, "Your rental owner account is pending approval by an administrator."
        if owner['approval_status'] == 'Rejected':
            return None, "Your rental owner account has been rejected by an administrator."
        
        token = generate_token(owner['owner_id'], 'rental_owner', owner['name'], owner['email'])
        return {
            'user_id': owner['owner_id'],
            'name': owner['name'],
            'email': owner['email'],
            'phone': owner.get('phone', ''),
            'role': 'rental_owner',
            'approval_status': owner['approval_status'],
            'token': token
        }, None

    # 3. Check Customer / User
    user = query_db("SELECT * FROM `user` WHERE email = %s", (email,), one=True)
    if user and check_password(password, user['password']):
        token = generate_token(user['user_id'], 'user', user['name'], user['email'])
        return {
            'user_id': user['user_id'],
            'name': user['name'],
            'email': user['email'],
            'phone': user.get('phone', ''),
            'role': 'user',
            'token': token
        }, None

    return None, "Invalid email or password."

def get_current_user_profile(user_id: int, role: str):
    """Fetch current user profile data based on role."""
    if role == 'admin':
        data = query_db("SELECT admin_id as user_id, name, email FROM `admin` WHERE admin_id = %s", (user_id,), one=True)
    elif role == 'rental_owner':
        data = query_db("SELECT owner_id as user_id, name, email, phone, address, approval_status FROM rental_owner WHERE owner_id = %s", (user_id,), one=True)
    else:
        data = query_db("SELECT user_id, name, email, phone FROM `user` WHERE user_id = %s", (user_id,), one=True)
    if data:
        data['role'] = role
    return data

