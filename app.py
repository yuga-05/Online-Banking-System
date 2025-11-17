from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash
import secrets
from config import Config
from extensions import app, db

#Configure the app
app.config.from_object(Config)

# Set up a secret key for session management
app.secret_key = app.config['SECRET_KEY']

#initialize the app wth db
db.init_app(app)


# Import models and controllers after db initialization to avoid circular imports
from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.loan import Loan

from controllers.auth_controller import (
    login_required, admin_required, register_user, login_user, admin_login, logout
)
from controllers.user_controller import (
    get_user_profile, update_profile, get_dashboard, get_account_info, update_wallet
)
from controllers.account_controller import (
    create_account, render_create_account, deposit_amount, render_deposit_page,
    withdraw_amount, render_withdraw_page, get_account_balance
)
from controllers.transaction_controller import (
    get_transaction_history, apply_for_loan, render_loan_page, get_loan_details,
    process_loan_payment
)
from controllers.admin_controller import (
    admin_dashboard, view_users, view_user_details, view_account_details,
    view_all_transactions, manage_loans, process_loan_request, manage_account_status
)

# Create uploads folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Route: Landing/Entry page
@app.route('/')
def index():
    return render_template('index.html')

# Route: Home page with login button
@app.route('/home')
def home():
    return render_template('home.html')

# Route: Login and Registration page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'register':
            return register_user()
        elif action == 'login':
            return login_user()
    return render_template('login.html')

# Route: Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login_route():
    return admin_login()

# Route: Logout
@app.route('/logout')
def logout_route():
    return logout()

# Route: User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    return get_dashboard()

# Route: User Profile
@app.route('/profile')
@login_required
def profile():
    return get_user_profile()

# Route: Update Profile
@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile_route():
    return update_profile()

# Route: Create Bank Account Form
@app.route('/create-account', methods=['GET'])
@login_required
def create_account_page():
    return render_create_account()

# Route: Process Create Bank Account
@app.route('/create-account', methods=['POST'])
@login_required
def create_account_route():
    return create_account()

# Route: Deposit Form
@app.route('/deposit', methods=['GET'])
@login_required
def deposit_page():
    return render_deposit_page()

# Route: Process Deposit
@app.route('/deposit', methods=['POST'])
@login_required
def deposit_route():
    return deposit_amount()

# Route: Withdraw Form
@app.route('/withdraw', methods=['GET'])
@login_required
def withdraw_page():
    return render_withdraw_page()

# Route: Process Withdrawal
@app.route('/withdraw', methods=['POST'])
@login_required
def withdraw_route():
    return withdraw_amount()

# Route: Account Information and Transactions
@app.route('/account/<int:account_id>')
@login_required
def account_info(account_id):
    return get_account_info(account_id)

# Route: Get Account Balance (API endpoint)
@app.route('/api/account/balance')
@login_required
def get_balance():
    return get_account_balance()

# Route: Update Wallet
@app.route('/wallet/update', methods=['POST'])
@login_required
def update_wallet_route():
    return update_wallet()

# Route: Loan Application Form
@app.route('/loan', methods=['GET'])
@login_required
def loan_page():
    return render_loan_page()

# Route: Process Loan Application
@app.route('/loan', methods=['POST'])
@login_required
def loan_route():
    return apply_for_loan()

# Route: Loan Details
@app.route('/loan/<int:loan_id>')
@login_required
def loan_details(loan_id):
    return get_loan_details(loan_id)

# Route: Process Loan Payment
@app.route('/loan/payment', methods=['POST'])
@login_required
def loan_payment():
    return process_loan_payment()

# Admin Routes
# Route: Admin Dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard_route():
    return admin_dashboard()

# Route: View Users List
@app.route('/admin/users')
@admin_required
def admin_users():
    return view_users()

# Route: View User Details
@app.route('/admin/users/<int:user_id>')
@admin_required
def admin_user_details(user_id):
    return view_user_details(user_id)

# Route: View Account Details
@app.route('/admin/accounts/<int:account_id>')
@admin_required
def admin_account_details(account_id):
    return view_account_details(account_id)

# Route: View All Transactions
@app.route('/admin/transactions')
@admin_required
def admin_transactions():
    return view_all_transactions()

# Route: Manage Loans
@app.route('/admin/loans')
@admin_required
def admin_loans():
    return manage_loans()

# Route: Process Loan Request
@app.route('/admin/loans/process', methods=['POST'])
@admin_required
def process_loan():
    return process_loan_request()

# Route: Manage Account Status
@app.route('/admin/accounts/status', methods=['POST'])
@admin_required
def account_status():
    return manage_account_status()

# Create admin user if it doesn't exist
@app.before_request
def create_admin():
    admin_exists = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
    if not admin_exists:
        admin_user = User(
            name='Admin',
            email=app.config['ADMIN_EMAIL'],
            password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
            contact='admin',
            dob=datetime.now(),
            age=0,
            gender='other',
            uid='ADMIN001',
            is_admin=True,
            created_at=datetime.now()
        )
        db.session.add(admin_user)
        db.session.commit()

if __name__ == '__main__':
    # Create all database tables
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(debug=app.config['DEBUG'], host='0.0.0.0')