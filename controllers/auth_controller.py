from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models.user import User
from extensions import db, app
import re
from functools import wraps

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('admin_login'))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('You need admin privileges to access this page', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def register_user():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        contact = request.form.get('contact')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        uid = request.form.get('uid')  # Unique Identity Number
        
        # Form validation
        if not all([name, email, password, confirm_password, contact, dob, gender, uid]):
            flash('All fields are required', 'danger')
            return redirect(url_for('login'))
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('login'))
        
        # Email validation
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            flash('Please enter a valid email address', 'danger')
            return redirect(url_for('login'))
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return redirect(url_for('login'))
        
        # Calculate age from DOB
        try:
            dob_date = datetime.strptime(dob, '%Y-%m-%d')
            today = datetime.now()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD', 'danger')
            return redirect(url_for('login'))
        
        # Create new user
        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            contact=contact,
            dob=dob_date,
            age=age,
            gender=gender,
            uid=uid,
            is_admin=False,
            created_at=datetime.now()
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'danger')
            return redirect(url_for('login'))
    
    return redirect(url_for('login'))

def login_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'danger')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return redirect(url_for('login'))
    
    return redirect(url_for('login'))

def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Please provide both email and password', 'danger')
            return redirect(url_for('admin_login'))
        
        admin = User.query.filter_by(email=email, is_admin=True).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            session['user_id'] = admin.id
            session['user_name'] = admin.name
            session['is_admin'] = True
            flash(f'Welcome admin, {admin.name}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials or not an admin account', 'danger')
            return redirect(url_for('admin_login'))
    
    return render_template('admin/admin_login.html')

def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('home'))