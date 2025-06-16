"""
Database service layer for MoMo Analytics
Handles all database operations using SQLAlchemy
"""

from datetime import datetime
from sqlalchemy import func, extract, desc
from sqlalchemy.exc import SQLAlchemyError
from . import db
from .models import Transaction, UploadHistory
import os
import glob

class DatabaseService:
    """Service class for database operations"""
    
    @staticmethod
    def add_multiple_transactions(transactions_list):
        """Add multiple transactions to the database"""
        try:
            added_count = 0
            
            for transaction_data in transactions_list:
                # Convert datetime string to datetime object if needed
                if isinstance(transaction_data.get('date'), str):
                    try:
                        transaction_data['date'] = datetime.fromisoformat(transaction_data['date'].replace('Z', '+00:00'))
                    except ValueError:
                        transaction_data['date'] = datetime.now()
                
                # Create transaction object
                transaction = Transaction(
                    transaction_id=transaction_data.get('transaction_id'),
                    date=transaction_data.get('date', datetime.now()),
                    amount=float(transaction_data.get('amount', 0)),
                    fee=float(transaction_data.get('fee', 0)),
                    balance=float(transaction_data.get('balance')) if transaction_data.get('balance') else None,
                    category=transaction_data.get('category', 'unknown'),
                    recipient_name=transaction_data.get('recipient_name'),
                    recipient_number=transaction_data.get('recipient_number'),
                    sender_name=transaction_data.get('sender_name'),
                    sender_number=transaction_data.get('sender_number'),
                    message=transaction_data.get('message'),
                    raw_body=transaction_data.get('raw_body', transaction_data.get('body'))
                )
                
                db.session.add(transaction)
                added_count += 1
            
            db.session.commit()
            return added_count
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Database error: {e}")
            raise
        except Exception as e:
            db.session.rollback()
            print(f"Error adding transactions: {e}")
            raise
    
    @staticmethod
    def get_all_transactions(page=1, per_page=20, category=None, search=None):
        """Get paginated transactions with optional filtering"""
        try:
            query = Transaction.query
            
            # Filter by category
            if category and category != 'all':
                query = query.filter(Transaction.category == category)
            
            # Search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    db.or_(
                        Transaction.recipient_name.like(search_term),
                        Transaction.sender_name.like(search_term),
                        Transaction.message.like(search_term),
                        Transaction.category.like(search_term),
                        Transaction.transaction_id.like(search_term)
                    )
                )
            
            # Order by date (newest first)
            query = query.order_by(desc(Transaction.date))
            
            # Paginate
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'transactions': [t.to_dict() for t in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return {
                'transactions': [],
                'total': 0,
                'pages': 1,
                'current_page': 1,
                'per_page': per_page
            }
    
    @staticmethod
    def clear_transactions():
        """Clear all transactions from database"""
        try:
            Transaction.query.delete()
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error clearing transactions: {e}")
            raise
    
    @staticmethod
    def get_stats():
        """Get transaction statistics"""
        try:
            total_transactions = Transaction.query.count()
            
            if total_transactions == 0:
                return {
                    'total_transactions': 0,
                    'total_amount': 0,
                    'total_fees': 0,
                    'categories': {},
                    'last_updated': datetime.now().isoformat()
                }
            
            # Calculate totals
            totals = db.session.query(
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.fee).label('total_fees')
            ).first()
            
            # Category breakdown
            category_stats = db.session.query(
                Transaction.category,
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('amount'),
                func.sum(Transaction.fee).label('fees')
            ).group_by(Transaction.category).all()
            
            categories = {}
            for cat, count, amount, fees in category_stats:
                categories[cat] = {
                    'count': count,
                    'amount': float(amount or 0),
                    'fees': float(fees or 0)
                }
            
            return {
                'total_transactions': total_transactions,
                'total_amount': float(totals.total_amount or 0),
                'total_fees': float(totals.total_fees or 0),
                'categories': categories,
                'last_updated': datetime.now().isoformat()
            }
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return {
                'total_transactions': 0,
                'total_amount': 0,
                'total_fees': 0,
                'categories': {},
                'last_updated': datetime.now().isoformat()
            }
    
    @staticmethod
    def get_monthly_stats():
        """Get monthly transaction statistics"""
        try:
            monthly_data = db.session.query(
                extract('year', Transaction.date).label('year'),
                extract('month', Transaction.date).label('month'),
                func.count(Transaction.id).label('count'),
                func.sum(Transaction.amount).label('total_amount'),
                func.sum(Transaction.fee).label('total_fees')
            ).group_by(
                extract('year', Transaction.date),
                extract('month', Transaction.date)
            ).order_by('year', 'month').all()
            
            result = []
            for year, month, count, total_amount, total_fees in monthly_data:
                result.append({
                    'year': int(year),
                    'month': int(month),
                    'count': count,
                    'total_amount': float(total_amount or 0),
                    'total_fees': float(total_fees or 0)
                })
            
            return result
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []
    
    @staticmethod
    def get_category_distribution():
        """Get category distribution for charts"""
        try:
            categories = db.session.query(
                Transaction.category,
                func.count(Transaction.id).label('count')
            ).group_by(Transaction.category).all()
            
            return [
                {
                    'category': cat.replace('_', ' ').title(),
                    'count': count
                }
                for cat, count in categories
            ]
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []
    
    @staticmethod
    def add_upload_record(filename, total_messages=0, processed_messages=0, status='pending'):
        """Add upload history record"""
        try:
            upload = UploadHistory(
                filename=filename,
                total_messages=total_messages,
                processed_messages=processed_messages,
                status=status
            )
            
            db.session.add(upload)
            db.session.commit()
            
            return upload.id
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error adding upload record: {e}")
            raise
    
    @staticmethod
    def update_upload_record(record_id, **updates):
        """Update upload history record"""
        try:
            upload = UploadHistory.query.get(record_id)
            if upload:
                for key, value in updates.items():
                    if hasattr(upload, key):
                        setattr(upload, key, value)
                
                db.session.commit()
                return True
            
            return False
            
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error updating upload record: {e}")
            raise
    
    @staticmethod
    def get_upload_history(limit=10):
        """Get upload history"""
        try:
            uploads = UploadHistory.query.order_by(
                desc(UploadHistory.upload_date)
            ).limit(limit).all()
            
            return [upload.to_dict() for upload in uploads]
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []
    
    @staticmethod
    def detect_xml_files():
        """Detect XML files in the data directory"""
        xml_files = []
        
        # Look for XML files in data directory and subdirectories
        patterns = [
            os.path.join('data', '*.xml'),
            os.path.join('data', '**', '*.xml')
        ]
        
        for pattern in patterns:
            xml_files.extend(glob.glob(pattern, recursive=True))
        
        # Return file info
        file_info = []
        for file_path in xml_files:
            try:
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_info.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size': size,
                    'modified': modified.isoformat(),
                    'relative_path': os.path.relpath(file_path, 'data')
                })
            except OSError as e:
                print(f"Warning: Could not access file {file_path}: {e}")
                continue
        
        # Sort by modification date (newest first)
        file_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return file_info
    
    @staticmethod
    def get_categories():
        """Get list of all categories"""
        try:
            categories = db.session.query(Transaction.category).distinct().all()
            return [cat[0] for cat in categories]
            
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return []