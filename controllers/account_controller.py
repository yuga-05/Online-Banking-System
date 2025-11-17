from flask import render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import random
import string
from models.user import User
from models.account import Account
from models.transaction import Transaction
from extensions import db, app
from controllers.auth_controller import login_required

def generate_account_number():
    """Generate a random 10-digit account number"""
    return ''.join(random.choices(string.digits, k=10))

def create_account():
    """Create a new bank account for the user"""
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to create an account', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('dashboard'))
        
        account_type = request.form.get('account_type')
        initial_deposit = float(request.form.get('initial_deposit', 0))
        passcode = request.form.get('passcode')
        
        # Validation
        if not account_type or not passcode:
            flash('Please provide all required information', 'danger')
            return redirect(url_for('create_account_page'))
        
        if account_type not in ['savings', 'current']:
            flash('Invalid account type selected', 'danger')
            return redirect(url_for('create_account_page'))
        
        # Validate passcode (6 digits)
        if not passcode.isdigit() or len(passcode) != 6:
            flash('Passcode must be exactly 6 digits', 'danger')
            return redirect(url_for('create_account_page'))
        
        # Check minimum initial deposit
        min_deposit = 500 if account_type == 'savings' else 1000
        if initial_deposit < min_deposit:
            flash(f'Minimum initial deposit for {account_type} account is ${min_deposit}', 'danger')
            return redirect(url_for('create_account_page'))
        
        try:
            # Generate unique account number
            account_number = generate_account_number()
            while Account.query.filter_by(account_number=account_number).first():
                account_number = generate_account_number()
            
            # Create new account
            new_account = Account(
                user_id=user_id,
                account_number=account_number,
                account_type=account_type,
                balance=initial_deposit,
                passcode=passcode,
                created_at=datetime.now(),
                status='active'
            )
            
            db.session.add(new_account)
            
            # Create initial deposit transaction
            if initial_deposit > 0:
                deposit_transaction = Transaction(
                    account_id=new_account.id,
                    transaction_type='deposit',
                    amount=initial_deposit,
                    transaction_date=datetime.now(),
                    description='Initial deposit'
                )
                db.session.add(deposit_transaction)
            
            db.session.commit()
            
            flash(f'Your {account_type.capitalize()} account has been created successfully. Account Number: {account_number}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while creating your account: {str(e)}', 'danger')
            return redirect(url_for('create_account_page'))
    
    return render_template('dashboard/create_account.html')

def render_create_account():
    """Render the create account form"""
    if 'user_id' not in session:
        flash('Please login to create an account', 'warning')
        return redirect(url_for('login'))
    
    return render_template('dashboard/create_account.html')

def deposit_amount():
    """Handle deposits to an account"""
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to make a deposit', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        account_number = request.form.get('account_number')
        passcode = request.form.get('passcode')
        amount = request.form.get('amount')
        
        # Validation
        if not all([account_number, passcode, amount]):
            flash('Please provide all required information', 'danger')
            return redirect(url_for('deposit_page'))
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Deposit amount must be greater than zero', 'danger')
                return redirect(url_for('deposit_page'))
        except ValueError:
            flash('Invalid amount specified', 'danger')
            return redirect(url_for('deposit_page'))
        
        # Find the account
        account = Account.query.filter_by(account_number=account_number).first()
        
        if not account:
            flash('Account not found. Please check the account number.', 'danger')
            return redirect(url_for('deposit_page'))
        
        # Verify account ownership and passcode
        if account.user_id != user_id:
            flash('You do not have permission to access this account', 'danger')
            return redirect(url_for('deposit_page'))
        
        if account.passcode != passcode:
            flash('Incorrect passcode', 'danger')
            return redirect(url_for('deposit_page'))
        
        try:
            # Update account balance
            account.balance += amount
            
            # Create transaction record
            deposit_transaction = Transaction(
                account_id=account.id,
                transaction_type='deposit',
                amount=amount,
                transaction_date=datetime.now(),
                description='Cash deposit'
            )
            
            db.session.add(deposit_transaction)
            db.session.commit()
            
            flash(f'Successfully deposited ${amount:.2f} to account {account_number}', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during the deposit: {str(e)}', 'danger')
            return redirect(url_for('deposit_page'))
    
    return render_template('dashboard/deposit.html')

def render_deposit_page():
    """Render the deposit form"""
    if 'user_id' not in session:
        flash('Please login to make a deposit', 'warning')
        return redirect(url_for('login'))
    
    # Get user's accounts for dropdown
    user_id = session['user_id']
    accounts = Account.query.filter_by(user_id=user_id, status='active').all()
    
    return render_template('dashboard/deposit.html', accounts=accounts)

def withdraw_amount():
    """Handle withdrawals from an account"""
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to make a withdrawal', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        account_number = request.form.get('account_number')
        passcode = request.form.get('passcode')
        amount = request.form.get('amount')
        to_wallet = request.form.get('to_wallet', 'no') == 'yes'
        
        # Validation
        if not all([account_number, passcode, amount]):
            flash('Please provide all required information', 'danger')
            return redirect(url_for('withdraw_page'))
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash('Withdrawal amount must be greater than zero', 'danger')
                return redirect(url_for('withdraw_page'))
        except ValueError:
            flash('Invalid amount specified', 'danger')
            return redirect(url_for('withdraw_page'))
        
        # Find the account
        account = Account.query.filter_by(account_number=account_number).first()
        
        if not account:
            flash('Account not found. Please check the account number.', 'danger')
            return redirect(url_for('withdraw_page'))
        
        # Verify account ownership and passcode
        if account.user_id != user_id:
            flash('You do not have permission to access this account', 'danger')
            return redirect(url_for('withdraw_page'))
        
        if account.passcode != passcode:
            flash('Incorrect passcode', 'danger')
            return redirect(url_for('withdraw_page'))
        
        # Check if sufficient balance
        if amount > account.balance:
            flash('Insufficient balance in your account', 'danger')
            return redirect(url_for('withdraw_page'))
        
        try:
            # Update account balance
            account.balance -= amount
            
            # Create transaction record
            withdraw_transaction = Transaction(
                account_id=account.id,
                transaction_type='withdrawal',
                amount=amount,
                transaction_date=datetime.now(),
                description='Cash withdrawal'
            )
            
            db.session.add(withdraw_transaction)
            
            # If to_wallet is True, add amount to user's wallet
            if to_wallet:
                user = User.query.get(user_id)
                user.wallet_balance += amount
                withdraw_transaction.description = 'Withdrawal to wallet'
            
            db.session.commit()
            
            if to_wallet:
                flash(f'Successfully withdrew ${amount:.2f} from account {account_number} to your wallet', 'success')
            else:
                flash(f'Successfully withdrew ${amount:.2f} from account {account_number}', 'success')
                
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during the withdrawal: {str(e)}', 'danger')
            return redirect(url_for('withdraw_page'))
    
    return render_template('dashboard/withdraw.html')

def render_withdraw_page():
    """Render the withdrawal form"""
    if 'user_id' not in session:
        flash('Please login to make a withdrawal', 'warning')
        return redirect(url_for('login'))
    
    # Get user's accounts for dropdown
    user_id = session['user_id']
    accounts = Account.query.filter_by(user_id=user_id, status='active').all()
    
    return render_template('dashboard/withdraw.html', accounts=accounts)

def get_account_balance():
    """API endpoint to get account balance"""
    if request.method == 'GET':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        account_number = request.args.get('account_number')
        
        if not account_number:
            return jsonify({'success': False, 'message': 'Account number is required'}), 400
        
        user_id = session['user_id']
        account = Account.query.filter_by(account_number=account_number, user_id=user_id).first()
        
        if not account:
            return jsonify({'success': False, 'message': 'Account not found or access denied'}), 404
        
        return jsonify({
            'success': True, 
            'account_number': account.account_number,
            'account_type': account.account_type,
            'balance': account.balance
        })
    
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405