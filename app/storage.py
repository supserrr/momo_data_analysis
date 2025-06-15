# app/storage.py - JSON file-based storage system
import json
import os
from datetime import datetime
import glob
import threading

class JSONStorage:
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        self.transactions_file = os.path.join(data_dir, 'transactions.json')
        self.upload_history_file = os.path.join(data_dir, 'upload_history.json')
        self.stats_file = os.path.join(data_dir, 'stats.json')
        
        # Thread lock for file operations
        self._lock = threading.Lock()
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(os.path.join(data_dir, 'uploads'), exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize JSON files with empty data"""
        if not os.path.exists(self.transactions_file):
            self._save_json(self.transactions_file, [])
        
        if not os.path.exists(self.upload_history_file):
            self._save_json(self.upload_history_file, [])
        
        if not os.path.exists(self.stats_file):
            self._save_json(self.stats_file, {
                'total_transactions': 0,
                'total_amount': 0,
                'total_fees': 0,
                'categories': {},
                'last_updated': datetime.now().isoformat()
            })
    
    def _load_json(self, file_path):
        """Load data from JSON file with error handling"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if data is not None else []
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load {file_path}: {e}")
            # Return appropriate empty structure
            if 'transactions' in file_path or 'upload_history' in file_path:
                return []
            else:
                return {}
    
    def _save_json(self, file_path, data):
        """Save data to JSON file with error handling"""
        try:
            # Create backup of existing file
            if os.path.exists(file_path):
                backup_path = file_path + '.backup'
                try:
                    os.rename(file_path, backup_path)
                except OSError:
                    pass  # Backup failed, continue anyway
            
            # Write new data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            # Remove backup if write was successful
            backup_path = file_path + '.backup'
            if os.path.exists(backup_path):
                try:
                    os.remove(backup_path)
                except OSError:
                    pass  # Backup removal failed, not critical
                    
        except Exception as e:
            # Restore backup if write failed
            backup_path = file_path + '.backup'
            if os.path.exists(backup_path):
                try:
                    os.rename(backup_path, file_path)
                except OSError:
                    pass
            raise e
    
    def detect_xml_files(self):
        """Detect XML files in the data directory"""
        xml_files = []
        
        # Look for XML files in data directory and subdirectories
        patterns = [
            os.path.join(self.data_dir, '*.xml'),
            os.path.join(self.data_dir, '**', '*.xml')
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
                    'relative_path': os.path.relpath(file_path, self.data_dir)
                })
            except OSError as e:
                print(f"Warning: Could not access file {file_path}: {e}")
                continue
        
        # Sort by modification date (newest first)
        file_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return file_info
    
    def add_multiple_transactions(self, transactions_list):
        """Add multiple transactions at once"""
        with self._lock:
            existing_transactions = self._load_json(self.transactions_file)
            
            # Ensure existing_transactions is a list
            if not isinstance(existing_transactions, list):
                existing_transactions = []
            
            added_count = 0
            
            for i, transaction_data in enumerate(transactions_list):
                try:
                    # Convert datetime to string if present
                    if transaction_data.get('date') and hasattr(transaction_data['date'], 'isoformat'):
                        transaction_data['date'] = transaction_data['date'].isoformat()
                    
                    # Add unique ID
                    transaction_data['id'] = len(existing_transactions) + added_count + 1
                    transaction_data['created_at'] = datetime.now().isoformat()
                    
                    # Validate transaction data
                    if self._validate_transaction(transaction_data):
                        existing_transactions.append(transaction_data)
                        added_count += 1
                    else:
                        print(f"Warning: Invalid transaction data at index {i}, skipping")
                        
                except Exception as e:
                    print(f"Error processing transaction at index {i}: {e}")
                    continue
            
            self._save_json(self.transactions_file, existing_transactions)
            self._update_stats()
            
            return added_count
    
    def _validate_transaction(self, transaction):
        """Validate transaction data structure"""
        required_fields = ['date', 'category', 'amount']
        
        for field in required_fields:
            if field not in transaction:
                return False
        
        # Validate amount is numeric
        try:
            float(transaction['amount'])
        except (ValueError, TypeError):
            return False
        
        return True
    
    def get_all_transactions(self, page=1, per_page=20, category=None, search=None):
        """Get transactions with pagination, filtering and search"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
        
        # Ensure transactions is a list
        if not isinstance(transactions, list):
            transactions = []
        
        # Filter by category if specified
        if category and category != 'all':
            transactions = [t for t in transactions if t.get('category') == category]
        
        # Search filter
        if search:
            search_lower = search.lower()
            filtered_transactions = []
            for t in transactions:
                # Search in multiple fields
                searchable_fields = [
                    t.get('recipient_name', ''),
                    t.get('sender_name', ''),
                    t.get('message', ''),
                    t.get('category', ''),
                    str(t.get('amount', '')),
                    t.get('transaction_id', '')
                ]
                
                if any(search_lower in str(field).lower() for field in searchable_fields):
                    filtered_transactions.append(t)
            
            transactions = filtered_transactions
        
        # Sort by date (newest first)
        transactions.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # Calculate pagination
        total = len(transactions)
        start = (page - 1) * per_page
        end = start + per_page
        
        return {
            'transactions': transactions[start:end],
            'total': total,
            'pages': (total + per_page - 1) // per_page if total > 0 else 1,
            'current_page': page,
            'per_page': per_page
        }
    
    def clear_transactions(self):
        """Clear all transactions"""
        with self._lock:
            self._save_json(self.transactions_file, [])
            self._update_stats()
    
    def get_stats(self):
        """Get transaction statistics"""
        with self._lock:
            return self._load_json(self.stats_file)
    
    def _update_stats(self):
        """Update statistics based on current transactions"""
        transactions = self._load_json(self.transactions_file)
        
        if not isinstance(transactions, list):
            transactions = []
        
        total_transactions = len(transactions)
        total_amount = 0
        total_fees = 0
        
        # Category breakdown
        categories = {}
        
        for transaction in transactions:
            try:
                # Calculate totals
                amount = float(transaction.get('amount', 0))
                fee = float(transaction.get('fee', 0))
                
                total_amount += amount
                total_fees += fee
                
                # Category statistics
                cat = transaction.get('category', 'unknown')
                if cat not in categories:
                    categories[cat] = {'count': 0, 'amount': 0, 'fees': 0}
                
                categories[cat]['count'] += 1
                categories[cat]['amount'] += amount
                categories[cat]['fees'] += fee
                
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid transaction data in stats calculation: {e}")
                continue
        
        stats = {
            'total_transactions': total_transactions,
            'total_amount': total_amount,
            'total_fees': total_fees,
            'categories': categories,
            'last_updated': datetime.now().isoformat()
        }
        
        self._save_json(self.stats_file, stats)
        return stats
    
    def get_monthly_stats(self):
        """Get monthly transaction statistics"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
        
        if not isinstance(transactions, list):
            transactions = []
        
        monthly_data = {}
        
        for transaction in transactions:
            date_str = transaction.get('date', '')
            if not date_str:
                continue
            
            try:
                # Parse date string
                if 'T' in date_str:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                
                year_month = f"{date.year}-{date.month:02d}"
                
                if year_month not in monthly_data:
                    monthly_data[year_month] = {
                        'year': date.year,
                        'month': date.month,
                        'count': 0,
                        'total_amount': 0,
                        'total_fees': 0
                    }
                
                monthly_data[year_month]['count'] += 1
                
                try:
                    amount = float(transaction.get('amount', 0))
                    fee = float(transaction.get('fee', 0))
                    monthly_data[year_month]['total_amount'] += amount
                    monthly_data[year_month]['total_fees'] += fee
                except (ValueError, TypeError):
                    pass
            
            except (ValueError, TypeError) as e:
                print(f"Warning: Invalid date format in transaction: {date_str}, {e}")
                continue
        
        # Convert to sorted list
        result = list(monthly_data.values())
        result.sort(key=lambda x: (x['year'], x['month']))
        
        return result
    
    def get_category_distribution(self):
        """Get category distribution for charts"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
        
        if not isinstance(transactions, list):
            transactions = []
        
        distribution = {}
        
        for transaction in transactions:
            category = transaction.get('category', 'unknown')
            display_name = category.replace('_', ' ').title()
            
            if display_name not in distribution:
                distribution[display_name] = 0
            
            distribution[display_name] += 1
        
        return [{'category': cat, 'count': count} for cat, count in distribution.items()]
    
    def add_upload_record(self, filename, total_messages=0, processed_messages=0, status='pending'):
        """Add upload history record"""
        with self._lock:
            upload_history = self._load_json(self.upload_history_file)
            
            if not isinstance(upload_history, list):
                upload_history = []
            
            record = {
                'id': len(upload_history) + 1,
                'filename': filename,
                'total_messages': total_messages,
                'processed_messages': processed_messages,
                'upload_date': datetime.now().isoformat(),
                'status': status
            }
            
            upload_history.append(record)
            self._save_json(self.upload_history_file, upload_history)
            
            return record['id']
    
    def update_upload_record(self, record_id, **updates):
        """Update upload history record"""
        with self._lock:
            upload_history = self._load_json(self.upload_history_file)
            
            if not isinstance(upload_history, list):
                upload_history = []
            
            for record in upload_history:
                if record.get('id') == record_id:
                    record.update(updates)
                    break
            
            self._save_json(self.upload_history_file, upload_history)
    
    def get_upload_history(self, limit=10):
        """Get upload history"""
        with self._lock:
            upload_history = self._load_json(self.upload_history_file)
        
        if not isinstance(upload_history, list):
            upload_history = []
        
        # Sort by upload date (newest first)
        upload_history.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        return upload_history[:limit]
    
    def get_transaction_by_id(self, transaction_id):
        """Get a specific transaction by ID"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
        
        if not isinstance(transactions, list):
            return None
        
        for transaction in transactions:
            if transaction.get('id') == transaction_id:
                return transaction
        
        return None
    
    def delete_transaction(self, transaction_id):
        """Delete a specific transaction"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
            
            if not isinstance(transactions, list):
                return False
            
            original_count = len(transactions)
            transactions = [t for t in transactions if t.get('id') != transaction_id]
            
            if len(transactions) < original_count:
                self._save_json(self.transactions_file, transactions)
                self._update_stats()
                return True
            
            return False
    
    def get_categories(self):
        """Get list of all categories"""
        with self._lock:
            transactions = self._load_json(self.transactions_file)
        
        if not isinstance(transactions, list):
            return []
        
        categories = set()
        for transaction in transactions:
            category = transaction.get('category')
            if category:
                categories.add(category)
        
        return sorted(list(categories))
    
    def backup_data(self, backup_dir='backups'):
        """Create a backup of all data"""
        try:
            os.makedirs(backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Backup each JSON file
            files_to_backup = [
                self.transactions_file,
                self.upload_history_file,
                self.stats_file
            ]
            
            for file_path in files_to_backup:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    backup_path = os.path.join(backup_dir, f"{timestamp}_{filename}")
                    
                    with open(file_path, 'r', encoding='utf-8') as src:
                        with open(backup_path, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())
            
            return True
        except Exception as e:
            print(f"Backup failed: {e}")
            return False