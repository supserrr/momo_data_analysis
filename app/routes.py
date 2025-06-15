from flask import Blueprint, render_template, request, jsonify, current_app, Response
from werkzeug.utils import secure_filename
from . import storage
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
        xml_files = storage.detect_xml_files()
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
        xml_files = storage.detect_xml_files()
        
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
    try:
        data = request.get_json()
        file_path = data.get('file_path')
        
        if not file_path:
            return jsonify({'error': 'No file path provided'}), 400
        
        # Construct full path
        full_path = os.path.join('data', file_path)
        
        # Security check - ensure file is within data directory
        if not os.path.abspath(full_path).startswith(os.path.abspath('data')):
            return jsonify({'error': 'Invalid file path'}), 400
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'File not found'}), 404
        
        # Create upload history record
        filename = os.path.basename(full_path)
        upload_id = storage.add_upload_record(filename, status='processing')
        
        # Parse the XML file
        parser = SMSParser()
        
        # Validate XML structure first
        is_valid, validation_message = parser.validate_xml_structure(full_path)
        if not is_valid:
            storage.update_upload_record(upload_id, status='failed')
            return jsonify({'error': f'Invalid XML file: {validation_message}'}), 400
        
        # Parse transactions
        transactions, total_count = parser.parse_xml_file(full_path)
        
        # Clear existing transactions
        storage.clear_transactions()
        
        # Save transactions to JSON storage
        processed = storage.add_multiple_transactions(transactions)
        
        # Update upload history
        storage.update_upload_record(upload_id, 
            total_messages=total_count,
            processed_messages=processed,
            status='completed'
        )
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed} transactions from {filename}',
            'total_messages': total_count,
            'processed': processed
        })
        
    except ValueError as e:
        if upload_id:
            storage.update_upload_record(upload_id, status='failed')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error processing detected file: {e}")
        if 'upload_id' in locals():
            storage.update_upload_record(upload_id, status='failed')
        return jsonify({'error': 'Internal server error while processing file'}), 500

@main.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload and process XML file"""
    upload_id = None
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload an XML file.'}), 400
        
        filename = secure_filename(file.filename)
        
        # Ensure upload directory exists
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)
        
        # Create upload history record
        upload_id = storage.add_upload_record(filename, status='processing')
        
        # Parse the XML file
        parser = SMSParser()
        
        # Validate XML structure first
        is_valid, validation_message = parser.validate_xml_structure(filepath)
        if not is_valid:
            storage.update_upload_record(upload_id, status='failed')
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': f'Invalid XML file: {validation_message}'}), 400
        
        # Parse transactions
        transactions, total_count = parser.parse_xml_file(filepath)
        
        # Clear existing transactions
        storage.clear_transactions()
        
        # Save transactions to JSON storage
        processed = storage.add_multiple_transactions(transactions)
        
        # Update upload history
        storage.update_upload_record(upload_id,
            total_messages=total_count,
            processed_messages=processed,
            status='completed'
        )
        
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)
        
        return jsonify({
            'success': True,
            'message': f'Successfully processed {processed} transactions',
            'total_messages': total_count,
            'processed': processed
        })
        
    except ValueError as e:
        if upload_id:
            storage.update_upload_record(upload_id, status='failed')
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error uploading file: {e}")
        if upload_id:
            storage.update_upload_record(upload_id, status='failed')
        return jsonify({'error': 'Internal server error while processing file'}), 500

@main.route('/api/stats')
def get_stats():
    """Get overall statistics"""
    try:
        stats = storage.get_stats()
        return jsonify(stats)
    except Exception as e:
        current_app.logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/monthly-stats')
def get_monthly_stats():
    """Get monthly statistics"""
    try:
        monthly_stats = storage.get_monthly_stats()
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
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        result = storage.get_all_transactions(page=page, per_page=per_page, category=category)
        
        # Convert transaction dates for display
        for transaction in result['transactions']:
            if transaction.get('date'):
                try:
                    # Parse ISO format date
                    if isinstance(transaction['date'], str):
                        dt = datetime.fromisoformat(transaction['date'].replace('Z', '+00:00'))
                        transaction['date'] = dt.isoformat()
                except (ValueError, TypeError):
                    pass
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Error getting transactions: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/category-distribution')
def get_category_distribution():
    """Get distribution of transactions by category for pie chart"""
    try:
        distribution = storage.get_category_distribution()
        return jsonify(distribution)
    except Exception as e:
        current_app.logger.error(f"Error getting category distribution: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/export-csv')
def export_csv():
    """Export transactions as CSV"""
    try:
        # Get all transactions
        result = storage.get_all_transactions(per_page=10000)
        transactions = result['transactions']
        
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
        storage.clear_transactions()
        return jsonify({'success': True, 'message': 'All data cleared successfully'})
    except Exception as e:
        current_app.logger.error(f"Error clearing data: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/upload-history')
def get_upload_history():
    """Get upload history"""
    try:
        history = storage.get_upload_history()
        return jsonify(history)
    except Exception as e:
        current_app.logger.error(f"Error getting upload history: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if storage is working
        stats = storage.get_stats()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'transactions_count': stats.get('total_transactions', 0)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500