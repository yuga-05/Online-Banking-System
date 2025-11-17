from flask import render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.loan import Loan
from extensions import db, app
from controllers.auth_controller import login_required

def get_user_profile():
    """Get the profile of the logged-in user"""
    if 'user_id' not in session:
        flash('Please login to view your profile', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('dashboard/profile.html', user=user)

def update_profile():
    """Update user profile information"""
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        try:
            # Update basic information
            user.name = request.form.get('name', user.name)
            user.contact = request.form.get('contact', user.contact)
            user.gender = request.form.get('gender', user.gender)
            
            # Handle DOB update and recalculate age
            new_dob = request.form.get('dob')
            if new_dob:
                try:
                    dob_date = datetime.strptime(new_dob, '%Y-%m-%d')
                    user.dob = dob_date
                    today = datetime.now()
                    user.age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
                except ValueError:
                    return jsonify({'success': False, 'message': 'Invalid date format. Please use YYYY-MM-DD'}), 400
            
            # Handle profile image upload
            if 'profile_image' in request.files:
                profile_image = request.files['profile_image']
                if profile_image.filename != '':
                    # Check file extension
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    if '.' in profile_image.filename and profile_image.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                        filename = secure_filename(f"user_{user_id}_{profile_image.filename}")
                        profile_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        profile_image.save(profile_path)
                        user.profile_image = filename
                    else:
                        return jsonify({'success': False, 'message': 'Invalid file format. Please upload PNG, JPG, JPEG, or GIF'}), 400
            
            # Handle password change if provided
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if current_password and new_password and confirm_password:
                if not check_password_hash(user.password_hash, current_password):
                    return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
                
                if new_password != confirm_password:
                    return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
                
                user.password_hash = generate_password_hash(new_password)
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile updated successfully'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
    
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405

def get_dashboard():
    """Render user dashboard with account summary"""
    if 'user_id' not in session:
        flash('Please login to access your dashboard', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('home'))
    
    # Get user's accounts
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    # Get user's loans
    loans = Loan.query.filter_by(user_id=user_id).all()
    
    # Get recent transactions (limit to 5)
    recent_transactions = []
    for account in accounts:
        transactions = Transaction.query.filter_by(account_id=account.id).order_by(Transaction.transaction_date.desc()).limit(5).all()
        recent_transactions.extend(transactions)
    
    # Sort transactions by date (most recent first)
    recent_transactions = sorted(recent_transactions, key=lambda x: x.transaction_date, reverse=True)[:5]
    
    # Calculate total balance across all accounts
    total_balance = sum(account.balance for account in accounts)
    
    # Calculate total loan amount
    total_loan_amount = sum(loan.amount for loan in loans if loan.status == 'approved')
    
    return render_template('dashboard/dashboard.html', 
                          user=user,
                          accounts=accounts,
                          loans=loans,
                          recent_transactions=recent_transactions,
                          total_balance=total_balance,
                          total_loan_amount=total_loan_amount,
                          wallet_balance=user.wallet_balance)

def get_account_info(account_id):
    """Get detailed information about a specific account"""
    if 'user_id' not in session:
        flash('Please login to view account information', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    account = Account.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        flash('Account not found or access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get all transactions for this account
    transactions = Transaction.query.filter_by(account_id=account_id).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('dashboard/account_info.html', account=account, transactions=transactions)

def update_wallet():
    """Update user's wallet balance"""
    if request.method == 'POST':
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        try:
            amount = float(request.form.get('amount', 0))
            action = request.form.get('action')  # 'deposit' or 'withdraw'
            
            if action == 'deposit':
                user.wallet_balance += amount
                flash(f'${amount:.2f} added to your wallet', 'success')
            elif action == 'withdraw':
                if amount > user.wallet_balance:
                    return jsonify({'success': False, 'message': 'Insufficient wallet balance'}), 400
                user.wallet_balance -= amount
                flash(f'${amount:.2f} withdrawn from your wallet', 'success')
            else:
                return jsonify({'success': False, 'message': 'Invalid action specified'}), 400
            
            db.session.commit()
            return jsonify({'success': True, 'message': 'Wallet updated successfully', 'new_balance': user.wallet_balance})
            
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid amount specified'}), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
    
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405