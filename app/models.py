from datetime import datetime
from . import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(50))
    date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    fee = db.Column(db.Float, default=0.0)
    balance = db.Column(db.Float)
    category = db.Column(db.String(50), nullable=False)
    recipient_name = db.Column(db.String(100))
    recipient_number = db.Column(db.String(20))
    sender_name = db.Column(db.String(100))
    sender_number = db.Column(db.String(20))
    message = db.Column(db.Text)
    raw_body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Transaction {self.id}: {self.category} - {self.amount} RWF>'
    
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
            'sender_name': self.sender_name,
            'sender_number': self.sender_number,
            'message': self.message,
            'raw_body': self.raw_body,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    total_messages = db.Column(db.Integer, default=0)
    processed_messages = db.Column(db.Integer, default=0)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='pending')
    
    def __repr__(self):
        return f'<UploadHistory {self.id}: {self.filename} - {self.status}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'total_messages': self.total_messages,
            'processed_messages': self.processed_messages,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'status': self.status
        }