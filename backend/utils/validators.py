import re

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
PHONE_REGEX = r'^[+0-9\s\-()]{7,20}$'

def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False, "Email is required."
    email = email.strip()
    if not re.match(EMAIL_REGEX, email):
        return False, "Invalid email address format."
    return True, email

def validate_password(password):
    """Validate password strength (minimum 6 characters)."""
    if not password or not isinstance(password, str):
        return False, "Password is required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, password

def validate_phone(phone):
    """Validate phone number format."""
    if not phone or not isinstance(phone, str):
        return False, "Phone number is required."
    phone = phone.strip()
    if not re.match(PHONE_REGEX, phone):
        return False, "Invalid phone number format."
    return True, phone

def validate_required(data, required_fields):
    """Ensure all required fields exist and are non-empty."""
    if not data or not isinstance(data, dict):
        return False, "Request body must be valid JSON."
    missing = []
    for field in required_fields:
        val = data.get(field)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(field)
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None

def validate_positive_number(val, field_name="Value", allow_zero=False):
    """Validate that value is a positive number."""
    try:
        num = float(val)
        if allow_zero:
            if num < 0:
                return False, f"{field_name} must be greater than or equal to 0."
        else:
            if num <= 0:
                return False, f"{field_name} must be greater than 0."
        return True, num
    except (TypeError, ValueError):
        return False, f"{field_name} must be a valid number."

