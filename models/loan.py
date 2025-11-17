from .user import db
from datetime import datetime, timedelta
import uuid

class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    interest_rate = db.Column(db.Float, default=10.0)  # Annual interest rate in percentage
    term_months = db.Column(db.Integer, nullable=False)  # Loan term in months
    monthly_payment = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)  # Total amount to be paid including interest
    remaining_amount = db.Column(db.Float, nullable=False)  # Remaining amount to be paid
    purpose = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, active, closed
    start_date = db.Column(db.Date, nullable=True)  # Date when the loan was approved and started
    end_date = db.Column(db.Date, nullable=True)  # Expected end date based on term
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    payments = db.relationship('LoanPayment', backref='loan', lazy=True, cascade="all, delete-orphan")
    
    def calculate_monthly_payment(self):
        """Calculate the monthly payment amount"""
        # Convert annual interest rate to monthly
        monthly_rate = self.interest_rate / 100 / 12
        
        # Calculate monthly payment using the formula: P * r * (1+r)^n / ((1+r)^n - 1)
        if monthly_rate == 0:
            # If interest rate is 0, simply divide the principal by the term
            return self.amount / self.term_months
        else:
            # Use the standard amortization formula
            return self.amount * monthly_rate * (1 + monthly_rate) ** self.term_months / ((1 + monthly_rate) ** self.term_months - 1)
    
    def calculate_total_amount(self):
        """Calculate the total amount to be paid over the loan term"""
        return self.monthly_payment * self.term_months
    
    def approve_loan(self, account):
        """Approve the loan and add the amount to the specified account"""
        if self.status != 'pending':
            raise ValueError("Can only approve pending loans")
        
        self.status = 'approved'
        self.start_date = datetime.utcnow().date()
        self.end_date = self.start_date + timedelta(days=30 * self.term_months)
        
        # Add amount to account
        account.deposit(self.amount)
        
        # Create transaction for loan disbursement
        from .transaction import Transaction
        Transaction(
            account_id=account.id,
            transaction_type='loan_disbursement',
            amount=self.amount,
            balance_after=account.balance,
            description=f"Loan disbursement: {self.loan_id}"
        )
        
        return True
    
    def make_payment(self, amount):
        """Make a payment towards the loan"""
        if amount <= 0:
            raise ValueError("Payment amount must be positive")
        if amount > self.remaining_amount:
            amount = self.remaining_amount  # Adjust payment to remaining amount
        
        self.remaining_amount -= amount
        
        # Create a payment record
        payment = LoanPayment(
            loan_id=self.id,
            amount=amount,
            remaining_balance=self.remaining_amount
        )
        db.session.add(payment)
        
        # Update loan status if fully paid
        if self.remaining_amount <= 0:
            self.status = 'closed'
        
        return payment
    
    def __repr__(self):
        return f'<Loan {self.loan_id} - {self.amount} - {self.status}>'

class LoanPayment(db.Model):
    __tablename__ = 'loan_payments'
    
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    remaining_balance = db.Column(db.Float, nullable=False)  # Remaining loan balance after payment
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<LoanPayment {self.payment_id} - {self.amount}>'