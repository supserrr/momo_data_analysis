from flask import Blueprint, render_template, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from .database import DatabaseService
from .parser import SMSParser
from datetime import datetime
import os
import io
import csv

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

@main.route('/')
def index():
    """Main upload page"""
    try:
        # Check for existing XML files in data directory
        xml_files = DatabaseService.detect_xml_files()
        return render_template('index.html', xml_files=xml_files)
    except Exception as e:
        current_app.logger.error(f"Error loading index page: {e}")
        return render_template('index.html', xml_files=[])

@main.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@main.route('/api/detect-files')
def detect_files():
    """API endpoint to detect XML files in data directory"""
    try:
        xml_files = DatabaseService.detect_xml_files()
        
        # Format file info for frontend
        formatted_files = []
        for file_info in xml_files:
            formatted_files.append({
                'name': file_info['name'],
                'path': file_info['relative_path'],
                'size': format_file_size(file_info['size']),
                'size_bytes': file_info['size'],
                'modified': file_info['modified']
            })
        
        return jsonify({
            'files': formatted_files,
            'count': len(formatted_files)
        })
    except Exception as e:
        current_app.logger.error(f"Error detecting files: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/process-detected-file', methods=['POST'])
def process_detected_file():
    """Process a detected XML file from data directory"""
    print("🔧 [WEB] Starting process_detected_file...")
    upload_id = None
    
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            print("❌ [WEB] No file path provided")
            return jsonify({'error': 'No file path provided'}), 400
        
        print(f"📁 [WEB] Processing file: {file_path}")
        
        # Construct full path
        full_path = os.path.join('data', file_path)
        
        # Security check
        if not os.path.abspath(full_path).startswith(os.path.abspath('data')):
            print("❌ [WEB] Invalid file path")
            return jsonify({'error': 'Invalid file path'}), 400
        
        if not os.path.exists(full_path):
            print("❌ [WEB] File not found")
            return jsonify({'error': 'File not found'}), 404
        
        print(f"✅ [WEB] File exists: {full_path}")
        
        # Check current database state
        from app.models import Transaction
        initial_count = Transaction.query.count()
        print(f"📊 [WEB] Initial database count: {initial_count}")
        
        # Create upload history record
        filename = os.path.basename(full_path)
        upload_id = DatabaseService.add_upload_record(filename, status='processing')
        print(f"📋 [WEB] Created upload record: {upload_id}")
        
        # Parse the XML file
        parser = SMSParser()
        
        # Validate XML structure
        print("🔍 [WEB] Validating XML structure...")
        is_valid, validation_message = parser.validate_xml_structure(full_path)
        if not is_valid:
            print(f"❌ [WEB] XML validation failed: {validation_message}")
            if upload_id:
                DatabaseService.update_upload_record(upload_id, status='failed')
            return jsonify({'error': f'Invalid XML file: {validation_message}'}), 400
        
        print("✅ [WEB] XML validation passed")
        
        # Parse transactions
        print("⚙️ [WEB] Parsing XML file...")
        transactions, total_count = parser.parse_xml_file(full_path)
        print(f"📊 [WEB] Found {len(transactions)} MoMo transactions from {total_count} SMS messages")
        
        if not transactions:
            print("⚠️ [WEB] No MoMo transactions found")
            if upload_id:
                DatabaseService.update_upload_record(upload_id, status='completed', 
                                                    total_messages=total_count, 
                                                    processed_messages=0)
            return jsonify({
                'success': True,
                'message': 'No MoMo transactions found in XML file',
                'total_messages': total_count,
                'processed': 0
            })
        
        # CLEAR EXISTING DATA to prevent duplicates
        print("🗑️ [WEB] Clearing existing transactions to prevent duplicates...")
        DatabaseService.clear_transactions()
        cleared_count = Transaction.query.count()
        print(f"📊 [WEB] After clearing: {cleared_count} transactions")
        
        # Add new transactions
        print("💾 [WEB] Adding new transactions to database...")
        processed = DatabaseService.add_multiple_transactions(transactions)
        print(f"✅ [WEB] Successfully added {processed} transactions to database")
        
        # Update upload history
        if upload_id:
            DatabaseService.update_upload_record(upload_id, 
                total_messages=total_count,
                processed_messages=processed,
                status='completed'
            )
        
        # Verify final state
        final_count = Transaction.query.count()
        print(f"📊 [WEB] Total transactions in database now: {final_count}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed} transactions from {filename}',
            'total_messages': total_count,
            'processed': processed,
            'total_in_db': final_count
        })
        
    except ValueError as e:
        print(f"❌ [WEB] ValueError: {e}")
        if upload_id:
            DatabaseService.update_upload_record(upload_id, status='failed')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ [WEB] Exception: {e}")
        import traceback
        traceback.print_exc()
        if upload_id:
            DatabaseService.update_upload_record(upload_id, status='failed')
        return jsonify({'error': 'Internal server error while processing file'}), 500

@main.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process XML file through web interface"""
    print("🔧 [WEB] Starting file upload via web interface...")
    upload_id = None
    
    try:
        if 'file' not in request.files:
            print("❌ [WEB] No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            print("❌ [WEB] Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            print("❌ [WEB] Invalid file type")
            return jsonify({'error': 'Invalid file type. Please upload an XML file.'}), 400
        
        filename = secure_filename(file.filename)
        print(f"📁 [WEB] Uploading file: {filename}")
        
        # Check current database state
        from app.models import Transaction
        initial_count = Transaction.query.count()
        print(f"📊 [WEB] Initial database count: {initial_count}")
        
        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        print(f"💾 [WEB] File saved to: {filepath}")
        
        # Create upload history record
        upload_id = DatabaseService.add_upload_record(filename, status='processing')
        print(f"📋 [WEB] Created upload record: {upload_id}")
        
        # Parse the XML file
        parser = SMSParser()
        
        # Validate XML structure
        print("🔍 [WEB] Validating uploaded XML...")
        is_valid, validation_message = parser.validate_xml_structure(filepath)
        if not is_valid:
            print(f"❌ [WEB] XML validation failed: {validation_message}")
            if upload_id:
                DatabaseService.update_upload_record(upload_id, status='failed')
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Invalid XML file: {validation_message}'}), 400
        
        print("✅ [WEB] XML validation passed")
        
        # Parse transactions
        print("⚙️ [WEB] Parsing uploaded XML...")
        transactions, total_count = parser.parse_xml_file(filepath)
        print(f"📊 [WEB] Found {len(transactions)} MoMo transactions from {total_count} SMS messages")
        
        if not transactions:
            print("⚠️ [WEB] No MoMo transactions found in uploaded file")
            if upload_id:
                DatabaseService.update_upload_record(upload_id, status='completed',
                                                    total_messages=total_count,
                                                    processed_messages=0)
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({
                'success': True,
                'message': 'No MoMo transactions found in uploaded XML file',
                'total_messages': total_count,
                'processed': 0
            })
        
        # CLEAR EXISTING DATA to prevent duplicates
        print("🗑️ [WEB] Clearing existing transactions to prevent duplicates...")
        DatabaseService.clear_transactions()
        cleared_count = Transaction.query.count()
        print(f"📊 [WEB] After clearing: {cleared_count} transactions")
        
        # Add new transactions
        print("💾 [WEB] Adding uploaded transactions to database...")
        processed = DatabaseService.add_multiple_transactions(transactions)
        print(f"✅ [WEB] Successfully added {processed} transactions from upload")
        
        # Update upload history
        if upload_id:
            DatabaseService.update_upload_record(upload_id,
                total_messages=total_count,
                processed_messages=processed,
                status='completed'
            )
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
            print("🗑️ [WEB] Cleaned up uploaded file")
        
        # Verify final state
        final_count = Transaction.query.count()
        print(f"📊 [WEB] Total transactions in database after upload: {final_count}")
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed} transactions from uploaded file',
            'total_messages': total_count,
            'processed': processed,
            'total_in_db': final_count
        })
        
    except ValueError as e:
        print(f"❌ [WEB] Upload ValueError: {e}")
        if upload_id:
            DatabaseService.update_upload_record(upload_id, status='failed')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"❌ [WEB] Upload Exception: {e}")
        import traceback
        traceback.print_exc()
        if upload_id:
            DatabaseService.update_upload_record(upload_id, status='failed')
        return jsonify({'error': 'Internal server error while processing uploaded file'}), 500

@main.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    try:
        stats = DatabaseService.get_stats()
        print(f"📊 [API] Stats request - returning {stats.get('total_transactions', 0)} transactions")
        return jsonify(stats)
    except Exception as e:
        print(f"❌ [API] Error getting stats: {e}")
        current_app.logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/monthly-stats')
def get_monthly_stats():
    """Get monthly statistics"""
    try:
        monthly_stats = DatabaseService.get_monthly_stats()
        return jsonify(monthly_stats)
    except Exception as e:
        current_app.logger.error(f"Error getting monthly stats: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/transactions')
def get_transactions():
    """Get paginated transactions"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        category = request.args.get('category', None)
        search = request.args.get('search', None)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        result = DatabaseService.get_all_transactions(
            page=page, 
            per_page=per_page, 
            category=category,
            search=search
        )
        
        print(f"📋 [API] Transactions request - returning {len(result['transactions'])} of {result['total']} total")
        
        return jsonify(result)
    except Exception as e:
        print(f"❌ [API] Error getting transactions: {e}")
        current_app.logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/category-distribution')
def get_category_distribution():
    """Get distribution of transactions by category for pie chart"""
    try:
        distribution = DatabaseService.get_category_distribution()
        return jsonify(distribution)
    except Exception as e:
        current_app.logger.error(f"Error getting category distribution: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/export-csv')
def export_csv():
    """Export transactions as CSV"""
    try:
        # Get all transactions
        result = DatabaseService.get_all_transactions(per_page=10000)
        transactions = result['transactions']
        
        print(f"📄 [API] CSV export - exporting {len(transactions)} transactions")
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Date', 'Category', 'Recipient', 'Sender', 'Amount', 
            'Fee', 'Balance', 'Transaction ID', 'Message', 'Raw Body'
        ])
        
        # Write data
        for t in transactions:
            # Format date
            date_str = ''
            if t.get('date'):
                try:
                    if isinstance(t['date'], str):
                        dt = datetime.fromisoformat(t['date'].replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        date_str = str(t['date'])
                except:
                    date_str = str(t.get('date', ''))
            
            writer.writerow([
                date_str,
                t.get('category', '').replace('_', ' ').title(),
                t.get('recipient_name', ''),
                t.get('sender_name', ''),
                t.get('amount', 0),
                t.get('fee', 0),
                t.get('balance', ''),
                t.get('transaction_id', ''),
                t.get('message', ''),
                t.get('raw_body', '')
            ])
        
        # Create response
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=momo_transactions_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    except Exception as e:
        current_app.logger.error(f"Error exporting CSV: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear all transaction data"""
    try:
        print("🗑️ [API] Clearing all data via API...")
        DatabaseService.clear_transactions()
        print("✅ [API] Data cleared successfully")
        return jsonify({'success': True, 'message': 'All data cleared successfully'})
    except Exception as e:
        print(f"❌ [API] Error clearing data: {e}")
        current_app.logger.error(f"Error clearing data: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/upload-history')
def get_upload_history():
    """Get upload history"""
    try:
        history = DatabaseService.get_upload_history()
        return jsonify(history)
    except Exception as e:
        current_app.logger.error(f"Error getting upload history: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if database is working
        stats = DatabaseService.get_stats()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'transactions_count': stats.get('total_transactions', 0),
            'database': 'SQLite'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500