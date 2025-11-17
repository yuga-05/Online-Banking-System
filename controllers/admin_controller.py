from flask import render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
import math
from models.user import User
from models.account import Account
from models.transaction import Transaction
from models.loan import Loan
from extensions import db, app
from controllers.auth_controller import admin_required

def admin_dashboard():
    """Render the admin dashboard with summary statistics"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    # Get summary statistics
    total_users = User.query.filter_by(is_admin=False).count()
    total_accounts = Account.query.count()
    active_accounts = Account.query.filter_by(status='active').count()
    
    # Calculate total deposits in the system
    total_deposits = db.session.query(db.func.sum(Account.balance)).scalar() or 0
    
    # Get loan statistics
    total_loans = Loan.query.count()
    pending_loans = Loan.query.filter_by(status='pending').count()
    approved_loans = Loan.query.filter_by(status='approved').count()
    
    # Calculate total loan amount and interest
    total_loan_amount = db.session.query(db.func.sum(Loan.amount)).filter(Loan.status.in_(['approved', 'paid'])).scalar() or 0
    total_interest = db.session.query(db.func.sum(Loan.total_interest)).filter(Loan.status.in_(['approved', 'paid'])).scalar() or 0
    
    # Get recent transactions (limit to 10)
    recent_transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).limit(10).all()
    
    return render_template('admin/admin_dashboard.html',
                          total_users=total_users,
                          total_accounts=total_accounts,
                          active_accounts=active_accounts,
                          total_deposits=total_deposits,
                          total_loans=total_loans,
                          pending_loans=pending_loans,
                          approved_loans=approved_loans,
                          total_loan_amount=total_loan_amount,
                          total_interest=total_interest,
                          recent_transactions=recent_transactions)

def view_users():
    """View list of all users"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get search parameters
    search_term = request.args.get('search', '')
    
    # Base query
    query = User.query.filter_by(is_admin=False)
    
    # Apply search filter if provided
    if search_term:
        query = query.filter(
            db.or_(
                User.name.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%'),
                User.uid.ilike(f'%{search_term}%')
            )
        )
    
    # Order by registration date (newest first)
    query = query.order_by(User.created_at.desc())
    
    # Pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / per_page)
    
    # Ensure valid page number
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Get paginated results
    users = query.paginate(page=page, per_page=per_page, error_out=False).items
    
    return render_template('admin/user_list.html', 
                          users=users,
                          total_pages=total_pages,
                          current_page=page,
                          search_term=search_term)

def view_user_details(user_id):
    """View detailed information about a specific user"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    user = User.query.get(user_id)
    
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('view_users'))
    
    # Get user's accounts
    accounts = Account.query.filter_by(user_id=user_id).all()
    
    # Get user's loans
    loans = Loan.query.filter_by(user_id=user_id).all()
    
    return render_template('admin/user_details.html', user=user, accounts=accounts, loans=loans)

def view_account_details(account_id):
    """View detailed information about a specific account"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    account = Account.query.get(account_id)
    
    if not account:
        flash('Account not found', 'danger')
        return redirect(url_for('view_users'))
    
    # Get account owner
    user = User.query.get(account.user_id)
    
    # Get transactions for this account
    transactions = Transaction.query.filter_by(account_id=account_id).order_by(Transaction.transaction_date.desc()).all()
    
    return render_template('admin/account_details.html', account=account, user=user, transactions=transactions)

def view_all_transactions():
    """View all transactions in the system"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get filter parameters
    transaction_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    account_id = request.args.get('account_id')
    
    # Base query
    query = Transaction.query
    
    # Apply filters
    if transaction_type:
        query = query.filter(Transaction.transaction_type == transaction_type)
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
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
    
    # Join with Account to get account numbers and user IDs
    query = query.join(Account)
    
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
    
    # Get account IDs for filtering
    accounts = Account.query.all()
    
    return render_template('admin/transactions.html', 
                          transactions=transactions,
                          accounts=accounts,
                          total_pages=total_pages,
                          current_page=page,
                          transaction_type=transaction_type,
                          date_from=date_from,
                          date_to=date_to,
                          account_id=account_id)

def manage_loans():
    """View and manage loan applications"""
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Admin access required', 'warning')
        return redirect(url_for('admin_login'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Get filter parameters
    status = request.args.get('status', 'pending')  # Default to pending loans
    
    # Base query
    query = Loan.query
    
    # Apply status filter
    if status:
        query = query.filter(Loan.status == status)
    
    # Order by application date (newest first)
    query = query.order_by(Loan.application_date.desc())
    
    # Pagination
    total_items = query.count()
    total_pages = math.ceil(total_items / per_page)
    
    # Ensure valid page number
    if page < 1:
        page = 1
    elif page > total_pages and total_pages > 0:
        page = total_pages
    
    # Get paginated results
    loans = query.paginate(page=page, per_page=per_page, error_out=False).items
    
    # Get users and accounts for each loan
    loan_details = []
    for loan in loans:
        user = User.query.get(loan.user_id)
        account = Account.query.get(loan.account_id)
        loan_details.append({
            'loan': loan,
            'user': user,
            'account': account
        })
    
    return render_template('admin/loans.html', 
                          loan_details=loan_details,
                          total_pages=total_pages,
                          current_page=page,
                          status=status)

def process_loan_request():
    """Approve or reject a loan application"""
    if request.method == 'POST':
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'warning')
            return redirect(url_for('admin_login'))
        
        loan_id = request.form.get('loan_id')
        action = request.form.get('action')  # 'approve' or 'reject'
        
        if not loan_id or not action:
            flash('Missing required parameters', 'danger')
            return redirect(url_for('manage_loans'))
        
        loan = Loan.query.get(loan_id)
        
        if not loan:
            flash('Loan not found', 'danger')
            return redirect(url_for('manage_loans'))
        
        # Only process pending loans
        if loan.status != 'pending':
            flash('This loan has already been processed', 'warning')
            return redirect(url_for('manage_loans'))
        
        try:
            if action == 'approve':
                # Approve loan
                loan.status = 'approved'
                loan.approval_date = datetime.now()
                loan.remaining_balance = loan.amount
                
                # Find the associated account
                account = Account.query.get(loan.account_id)
                
                if account:
                    # Add loan amount to account balance
                    account.balance += loan.amount
                    
                    # Create transaction record
                    loan_transaction = Transaction(
                        account_id=account.id,
                        transaction_type='loan_disbursement',
                        amount=loan.amount,
                        transaction_date=datetime.now(),
                        description=f'Loan disbursement for Loan #{loan.id}'
                    )
                    
                    db.session.add(loan_transaction)
                
                flash(f'Loan #{loan_id} has been approved and funds have been disbursed', 'success')
                
            elif action == 'reject':
                # Reject loan
                loan.status = 'rejected'
                loan.rejection_date = datetime.now()
                flash(f'Loan #{loan_id} has been rejected', 'info')
                
            else:
                flash('Invalid action specified', 'danger')
                return redirect(url_for('manage_loans'))
            
            db.session.commit()
            return redirect(url_for('manage_loans'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while processing the loan: {str(e)}', 'danger')
            return redirect(url_for('manage_loans'))
    
    return redirect(url_for('manage_loans'))

def manage_account_status():
    """Activate or deactivate a bank account"""
    if request.method == 'POST':
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'warning')
            return redirect(url_for('admin_login'))
        
        account_id = request.form.get('account_id')
        action = request.form.get('action')  # 'activate' or 'deactivate'
        
        if not account_id or not action:
            flash('Missing required parameters', 'danger')
            return redirect(url_for('view_users'))
        
        account = Account.query.get(account_id)
        
        if not account:
            flash('Account not found', 'danger')
            return redirect(url_for('view_users'))
        
        try:
            if action == 'activate':
                account.status = 'active'
                flash(f'Account #{account.account_number} has been activated', 'success')
                
            elif action == 'deactivate':
                account.status = 'inactive'
                flash(f'Account #{account.account_number} has been deactivated', 'info')
                
            else:
                flash('Invalid action specified', 'danger')
                return redirect(url_for('view_account_details', account_id=account_id))
            
            db.session.commit()
            return redirect(url_for('view_account_details', account_id=account_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating the account status: {str(e)}', 'danger')
            return redirect(url_for('view_account_details', account_id=account_id))
    
    return redirect(url_for('view_users'))