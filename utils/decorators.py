from functools import wraps
from flask import session, redirect, url_for, flash, request, abort

def login_required(f):
    """Decorator to require login for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin access for certain routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('admin_login'))
        
        from models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'admin':
            flash('You do not have permission to access this page', 'error')
            abort(403)
            
        return f(*args, **kwargs)
    return decorated_function

def account_owner_required(f):
    """Decorator to ensure user owns the account they're trying to access."""
    @wraps(f)
    def decorated_function(account_id, *args, **kwargs):
        from models.account import Account
        
        account = Account.query.get_or_404(account_id)
        
        if account.user_id != session.get('user_id'):
            flash('You do not have permission to access this account', 'error')
            abort(403)
            
        return f(account_id, *args, **kwargs)
    return decorated_function

def prevent_authenticated(f):
    """Decorator to prevent authenticated users from accessing certain pages."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function