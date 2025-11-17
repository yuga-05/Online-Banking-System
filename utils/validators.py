import re
from datetime import datetime

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    return True

def validate_password(password):
    """
    Validate password strength.
    Password should be at least 8 characters long,
    contain at least one digit, one uppercase letter,
    one lowercase letter, and one special character.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def validate_name(name):
    """Validate name format (letters, spaces, hyphens, and apostrophes only)."""
    pattern = r'^[a-zA-Z\s\'-]+$'
    if not re.match(pattern, name) or len(name) < 2:
        return False
    return True

def validate_phone(phone):
    """Validate phone number format."""
    pattern = r'^\d{10,15}$'
    if not re.match(pattern, phone):
        return False
    return True

def validate_dob(dob):
    """Validate date of birth format and that the person is at least 18 years old."""
    try:
        dob_date = datetime.strptime(dob, '%Y-%m-%d')
        today = datetime.today()
        age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        if age < 18:
            return False, "You must be at least 18 years old to register"
        return True, "Valid date of birth"
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD"

def validate_amount(amount):
    """Validate that amount is a positive number."""
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Amount must be positive"
        return True, "Valid amount"
    except ValueError:
        return False, "Invalid amount format"

def validate_passcode(passcode):
    """Validate that passcode is a 6-digit number."""
    pattern = r'^\d{6}$'
    if not re.match(pattern, passcode):
        return False, "Passcode must be a 6-digit number"
    return True, "Valid passcode"

def validate_account_number(account_number):
    """Validate account number format."""
    pattern = r'^\d{10}$'
    if not re.match(pattern, account_number):
        return False, "Account number must be a 10-digit number"
    return True, "Valid account number"

def validate_uid(uid):
    """Validate unique identifier format."""
    pattern = r'^[A-Z0-9]{12}$'
    if not re.match(pattern, uid):
        return False, "UID must be a 12-character alphanumeric string"
    return True, "Valid UID"

def validate_address(address):
    """Validate address format."""
    if len(address) < 10 or len(address) > 200:
        return False, "Address must be between 10 and 200 characters"
    return True, "Valid address"

def validate_loan_amount(amount, max_amount=1000000):
    """Validate loan amount."""
    try:
        amount = float(amount)
        if amount <= 0:
            return False, "Loan amount must be positive"
        if amount > max_amount:
            return False, f"Loan amount cannot exceed {max_amount}"
        return True, "Valid loan amount"
    except ValueError:
        return False, "Invalid loan amount format"