from .user import db
from datetime import datetime
import uuid

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # deposit, withdrawal, transfer, loan_disbursement, loan_payment
    amount = db.Column(db.Float, nullable=False)
    balance_after = db.Column(db.Float, nullable=False)  # Balance after transaction
    description = db.Column(db.String(256))
    status = db.Column(db.String(20), default='completed')  # pending, completed, failed, reversed
    recipient_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)  # For transfers
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # For transfers
    recipient_account = db.relationship('Account', foreign_keys=[recipient_account_id], backref='incoming_transfers', lazy=True)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id} - {self.transaction_type} - {self.amount}>'
    
    @staticmethod
    def create_deposit(account, amount, description=None):
        """Create a deposit transaction"""
        account.deposit(amount)
        transaction = Transaction(
            account_id=account.id,
            transaction_type='deposit',
            amount=amount,
            balance_after=account.balance,
            description=description or f"Deposit to account {account.account_number}"
        )
        db.session.add(transaction)
        return transaction
    
    @staticmethod
    def create_withdrawal(account, amount, description=None):
        """Create a withdrawal transaction"""
        try:
            account.withdraw(amount)
            transaction = Transaction(
                account_id=account.id,
                transaction_type='withdrawal',
                amount=amount,
                balance_after=account.balance,
                description=description or f"Withdrawal from account {account.account_number}"
            )
            db.session.add(transaction)
            return transaction
        except ValueError as e:
            # Create a failed transaction
            transaction = Transaction(
                account_id=account.id,
                transaction_type='withdrawal',
                amount=amount,
                balance_after=account.balance,
                description=str(e),
                status='failed'
            )
            db.session.add(transaction)
            raise e