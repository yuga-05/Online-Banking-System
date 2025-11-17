from flask import render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.loan import Loan
from extensions import db, app
from controllers.auth_controller import login_required
import math

def get_transaction_history():
    """Get transaction history for user's accounts"""
    if 'user_id' not in session:
        flash('Please login to view your transactions', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    account_id = request.args.get('account_id', type=int)
    
    # Get filter parameters
    transaction_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Get user's accounts
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    if not accounts:
        flash('No accounts found', 'info')
        return render_template('dashboard/account_info.html', transactions=[], accounts=[], 
                              total_pages=0, current_page=1, account_id=None)
    
    # Base query for transactions
    query = Transaction.query.join(Account).filter(Account.user_id == user_id)
    
    # Apply filters
    if account_id:
        # Verify this account belongs to the user
        account_exists = any(acc.id == account_id for acc in accounts)
        if account_exists:
            query = query.filter(Transaction.account_id == account_id)
        else:
            flash('Invalid account selected', 'danger')
    
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Transaction.transaction_date >= from_date)
        except ValueError:
            flash('Invalid from date format', 'warning')
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Transaction.transaction_date <= to_date)
        except ValueError:
            flash('Invalid to date format', 'warning')
    
    # Order by most recent first
    query = query.order_by(Transaction.transaction_date.desc())
    
    # Pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / per_page)
    
    # Ensure valid page number
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Get paginated results
    transactions = query.paginate(page=page, per_page=per_page, error_out=False).items
    
    return render_template('dashboard/account_info.html', 
                          transactions=transactions,
                          accounts=accounts,
                          total_pages=total_pages,
                          current_page=page,
                          account_id=account_id)

def render_loan_page():
    """Render the loan application page"""
    if 'user_id' not in session:
        flash('Please login to apply for a loan', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Get user's accounts for dropdown
    accounts = Account.query.filter_by(user_id=user_id, status='active').all()
    
    # Get existing loans
    active_loans = Loan.query.filter_by(user_id=user_id).filter(
        Loan.status.in_(['pending', 'approved', 'active'])).all()
    
    return render_template('dashboard/loan.html', 
                          accounts=accounts,
                          active_loans=active_loans)

def apply_for_loan():
    """Handle loan application"""
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to apply for a loan', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        loan_amount = request.form.get('loan_amount')
        loan_purpose = request.form.get('loan_purpose')
        loan_term = request.form.get('loan_term')  # in months
        account_number = request.form.get('account_number')
        
        # Validation
        if not all([loan_amount, loan_purpose, loan_term, account_number]):
            flash('Please provide all required information', 'danger')
            return redirect(url_for('loan_page'))
        
        try:
            loan_amount = float(loan_amount)
            loan_term = int(loan_term)
            
            if loan_amount <= 0:
                flash('Loan amount must be greater than zero', 'danger')
                return redirect(url_for('loan_page'))
            
            if loan_term < 1:
                flash('Loan term must be at least 1 month', 'danger')
                return redirect(url_for('loan_page'))
                
        except ValueError:
            flash('Invalid amount or term specified', 'danger')
            return redirect(url_for('loan_page'))
        
        # Find the account
        account = Account.query.filter_by(account_number=account_number, user_id=user_id).first()
        if not account:
            flash('Account not found or access denied', 'danger')
            return redirect(url_for('loan_page'))
        
        # Check if account is active
        if account.status != 'active':
            flash('Selected account is not active', 'danger')
            return redirect(url_for('loan_page'))
        
        # Check for existing active loans
        active_loans = Loan.query.filter_by(user_id=user_id, status='approved').count()
        if active_loans >= 3:  # Limit to 3 active loans
            flash('You already have the maximum number of active loans allowed', 'danger')
            return redirect(url_for('loan_page'))
        
        # Create new loan application
        try:
            interest_rate = 0.05  # 5% - Example rate
            
            new_loan = Loan(
                user_id=user_id,
                account_id=account.id,
                amount=loan_amount,
                purpose=loan_purpose,
                term_months=loan_term,
                interest_rate=interest_rate,
                status='pending',
                application_date=datetime.now(),
                remaining_balance=loan_amount + (loan_amount * interest_rate * loan_term / 12)
            )
            
            db.session.add(new_loan)
            db.session.commit()
            
            flash('Loan application submitted successfully! It will be reviewed shortly.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during loan application: {str(e)}', 'danger')
            return redirect(url_for('loan_page'))
    
    return redirect(url_for('loan_page'))

def get_loan_details(loan_id):
    """Get details for a specific loan"""
    if 'user_id' not in session:
        flash('Please login to view loan details', 'warning')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Find the loan
    loan = Loan.query.filter_by(id=loan_id, user_id=user_id).first()
    
    if not loan:
        flash('Loan not found or access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get account information
    account = Account.query.get(loan.account_id)
    
    # Get user accounts for payment options
    user_accounts = Account.query.filter_by(user_id=user_id, status='active').all()
    
    # Calculate payment history if available
    payment_history = []
    if loan.payment_history:
        payment_entries = loan.payment_history.strip().split('\n')
        for entry in payment_entries:
            if entry:  # Skip empty entries
                payment_history.append(entry)
    
    # Calculate interest and repayment information if loan is approved
    monthly_payment = 0
    total_repayment = 0
    total_interest = 0
    
    if loan.status == 'approved':
        # Calculate monthly payment (simplified)
        r = loan.interest_rate / 12  # Monthly interest rate
        n = loan.term_months  # Number of months
        p = loan.amount  # Principal
        
        # Monthly payment formula: P * r * (1 + r)^n / ((1 + r)^n - 1)
        if r > 0:  # Avoid division by zero if interest rate is 0
            monthly_payment = p * r * (1 + r)**n / ((1 + r)**n - 1)
        else:
            monthly_payment = p / n
            
        total_repayment = monthly_payment * n
        total_interest = total_repayment - p
    
    return render_template('dashboard/loan_details.html',
                          loan=loan,
                          account=account,
                          user_accounts=user_accounts,
                          payment_history=payment_history,
                          monthly_payment=monthly_payment,
                          total_repayment=total_repayment,
                          total_interest=total_interest)

def process_loan_payment():
    """Process a loan payment"""
    if request.method == 'POST':
        if 'user_id' not in session:
            flash('Please login to make a loan payment', 'warning')
            return redirect(url_for('login'))
        
        user_id = session['user_id']
        loan_id = request.form.get('loan_id')
        payment_amount = request.form.get('payment_amount')
        payment_method = request.form.get('payment_method')  # 'account' or 'wallet'
        account_number = request.form.get('account_number')
        passcode = request.form.get('passcode')
        
        # Validation
        if not all([loan_id, payment_amount, payment_method]):
            flash('Please provide all required information', 'danger')
            return redirect(url_for('loan_page'))
        
        try:
            payment_amount = float(payment_amount)
            if payment_amount <= 0:
                flash('Payment amount must be greater than zero', 'danger')
                return redirect(url_for('loan_page'))
        except ValueError:
            flash('Invalid payment amount', 'danger')
            return redirect(url_for('loan_page'))
        
        # Find the loan
        loan = Loan.query.filter_by(id=loan_id, user_id=user_id).first()
        
        if not loan:
            flash('Loan not found or access denied', 'danger')
            return redirect(url_for('loan_page'))
        
        # Check if loan is approved
        if loan.status != 'approved':
            flash('This loan is not in active repayment status', 'danger')
            return redirect(url_for('loan_page'))
        
        try:
            # Process payment based on payment method
            if payment_method == 'account':
                if not account_number or not passcode:
                    flash('Account number and passcode are required for account payments', 'danger')
                    return redirect(url_for('loan_page'))
                
                # Find the account
                account = Account.query.filter_by(account_number=account_number, user_id=user_id).first()
                
                if not account:
                    flash('Account not found or access denied', 'danger')
                    return redirect(url_for('loan_page'))
                
                # Verify passcode
                if account.passcode != passcode:
                    flash('Incorrect passcode', 'danger')
                    return redirect(url_for('loan_page'))
                
                # Check if sufficient balance
                if payment_amount > account.balance:
                    flash('Insufficient balance in your account', 'danger')
                    return redirect(url_for('loan_page'))
                
                # Update account balance
                account.balance -= payment_amount
                
                # Create transaction record
                payment_transaction = Transaction(
                    account_id=account.id,
                    transaction_type='loan_payment',
                    amount=payment_amount,
                    transaction_date=datetime.now(),
                    description=f'Loan payment for Loan #{loan.id}'
                )
                
                db.session.add(payment_transaction)
                
            elif payment_method == 'wallet':
                # Get user
                user = User.query.get(user_id)
                
                # Check if sufficient wallet balance
                if payment_amount > user.wallet_balance:
                    flash('Insufficient balance in your wallet', 'danger')
                    return redirect(url_for('loan_page'))
                
                # Update wallet balance
                user.wallet_balance -= payment_amount
                
            else:
                flash('Invalid payment method', 'danger')
                return redirect(url_for('loan_page'))
            
            # Update loan balance
            remaining_balance = loan.remaining_balance or loan.amount
            new_balance = remaining_balance - payment_amount
            
            if new_balance <= 0:
                # Loan fully paid
                loan.remaining_balance = 0
                loan.status = 'paid'
                loan.completion_date = datetime.now()
            else:
                loan.remaining_balance = new_balance
            
            # Update payment history
            loan.payment_history = loan.payment_history or ""
            payment_record = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: ${payment_amount:.2f} paid via {payment_method}\n"
            loan.payment_history += payment_record
            
            db.session.commit()
            
            if loan.status == 'paid':
                flash('Congratulations! Your loan has been fully paid off.', 'success')
            else:
                flash(f'Payment of ${payment_amount:.2f} processed successfully. Remaining balance: ${loan.remaining_balance:.2f}', 'success')
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during payment processing: {str(e)}', 'danger')
            return redirect(url_for('loan_page'))
    
    return redirect(url_for('loan_page'))