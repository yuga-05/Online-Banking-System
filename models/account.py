from .user import db
from datetime import datetime
import random
import string

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    account_type = db.Column(db.String(20), nullable=False)  # 'savings' or 'current'
    balance = db.Column(db.Float, default=0.0)
    passcode = db.Column(db.String(256), nullable=False)  # Hashed 6-digit passcode
    status = db.Column(db.String(20), default='active')  # active, suspended, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade="all, delete-orphan")
    
    @staticmethod
    def generate_account_number():
        """Generate a random 10-digit account number"""
        prefix = '10'  # Bank prefix
        random_digits = ''.join(random.choices(string.digits, k=8))
        return prefix + random_digits
    
    @staticmethod
    def hash_passcode(passcode):
        """Hash a 6-digit passcode"""
        # Using the same hashing mechanism as for passwords
        from werkzeug.security import generate_password_hash
        return generate_password_hash(passcode)
    
    def check_passcode(self, passcode):
        """Verify a 6-digit passcode"""
        from werkzeug.security import check_password_hash
        return check_password_hash(self.passcode, passcode)
    
    def deposit(self, amount):
        """Add amount to balance"""
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        self.balance += amount
        return True
    
    def withdraw(self, amount):
        """Remove amount from balance"""
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        return True
    
    def __repr__(self):
        return f'<Account {self.account_number}>'