import os
import re
import uuid
from datetime import datetime
from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def generate_account_number():
    """Generate a unique 10-digit account number."""
    return str(uuid.uuid4().int)[:10]

def generate_transaction_id():
    """Generate a unique transaction ID."""
    return str(uuid.uuid4())

def calculate_age(dob):
    """Calculate age based on date of birth."""
    today = datetime.today()
    born = datetime.strptime(dob, '%Y-%m-%d')
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age

def format_currency(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_image(file):
    """Save the profile image and return the filename."""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        upload_folder = os.path.join('static', 'uploads')
        
        # Ensure upload directory exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
            
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        return os.path.join('uploads', unique_filename)
    return None

def calculate_loan_interest(amount, rate=10, period=1):
    """Calculate loan interest amount."""
    # Simple interest: P * R * T / 100
    interest = (float(amount) * rate * period) / 100
    return interest

def calculate_loan_payment(principal, rate=10, period=1):
    """Calculate monthly loan payment."""
    # Total amount to be paid
    total = float(principal) + calculate_loan_interest(principal, rate, period)
    # Monthly payment
    monthly = total / (period * 12)
    return monthly

def format_date(date_obj):
    """Format a date object into a readable string."""
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, '%Y-%m-%d')
        except ValueError:
            return date_obj
    return date_obj.strftime("%B %d, %Y")

def get_transaction_description(transaction_type, amount, account_number=None):
    """Generate a description for a transaction."""
    if transaction_type == "deposit":
        return f"Deposit of {format_currency(amount)} to account {account_number}"
    elif transaction_type == "withdrawal":
        return f"Withdrawal of {format_currency(amount)} from account {account_number}"
    elif transaction_type == "transfer":
        return f"Transfer of {format_currency(amount)}"
    elif transaction_type == "loan_disbursement":
        return f"Loan disbursement of {format_currency(amount)}"
    elif transaction_type == "loan_payment":
        return f"Loan payment of {format_currency(amount)}"
    return f"{transaction_type.capitalize()} of {format_currency(amount)}"