from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Import db from the app package
from . import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50), unique=True)
    date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fee = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float)
    category = db.Column(db.String(50), nullable=False)
    recipient_name = db.Column(db.String(100))
    recipient_number = db.Column(db.String(20))
    sender_number = db.Column(db.String(20))
    message = db.Column(db.Text)
    raw_body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'date': self.date.isoformat() if self.date else None,
            'amount': self.amount,
            'fee': self.fee,
            'balance': self.balance,
            'category': self.category,
            'recipient_name': self.recipient_name,
            'recipient_number': self.recipient_number,
            'sender_number': self.sender_number,
            'message': self.message
        }

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    total_messages = db.Column(db.Integer)
    processed_messages = db.Column(db.Integer)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')