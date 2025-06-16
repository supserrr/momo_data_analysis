#!/usr/bin/env python3
"""
MoMo Analytics Enhanced Start Script

Enhanced version that combines quick start with automatic XML processing:
1. Scans data folder for XML files
2. Auto-processes XML files to populate database
3. Starts Flask application
"""

import socket
import os
import glob
from datetime import datetime
from pathlib import Path

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

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

def scan_for_xml_files():
    """Scan for XML files in data directory and current directory"""
    print("🔍 Scanning for XML files...")
    
    # Look for XML files in data directory and current directory
    xml_patterns = [
        'data/*.xml',
        'data/**/*.xml',
        '*.xml',
    ]
    
    xml_files = []
    for pattern in xml_patterns:
        xml_files.extend(glob.glob(pattern, recursive=True))
    
    # Remove duplicates and get file info
    unique_files = list(set(xml_files))
    file_info = []
    
    for file_path in unique_files:
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                file_info.append({
                    'path': file_path,
                    'name': os.path.basename(file_path),
                    'size': size,
                    'modified': modified,
                    'size_str': format_file_size(size)
                })
        except OSError:
            continue
    
    # Sort by modification date (newest first)
    file_info.sort(key=lambda x: x['modified'], reverse=True)
    
    return file_info

def auto_process_xml():
    """Automatically process XML files if database is empty"""
    try:
        from app import create_app
        from app.models import Transaction
        from app.database import DatabaseService
        from app.parser import SMSParser
        
        # Create Flask app context
        app = create_app()
        if app is None:
            return False
            
        with app.app_context():
            # Check if database already has data
            try:
                existing_count = Transaction.query.count()
                if existing_count > 0:
                    print(f"✅ Database already contains {existing_count} transactions")
                    return True
            except:
                existing_count = 0
            
            print("📂 Database is empty, looking for XML files...")
            
            # Scan for XML files
            xml_files = scan_for_xml_files()
            
            if not xml_files:
                print("📁 No XML files found")
                print("💡 To auto-populate:")
                print("   • Place SMS backup XML file in 'data/' folder")
                print("   • Or use the web interface to upload files")
                return True  # Not an error, just no files to process
            
            # Show found files
            print(f"📁 Found {len(xml_files)} XML file(s):")
            for i, file_info in enumerate(xml_files[:3]):  # Show first 3
                print(f"   {i+1}. {file_info['name']} ({file_info['size_str']})")
            
            # Process the first (newest) file
            selected_file = xml_files[0]
            print(f"\n🚀 Auto-processing: {selected_file['name']}")
            
            try:
                # Parse the XML file
                parser = SMSParser()
                
                # Validate XML structure
                is_valid, validation_message = parser.validate_xml_structure(selected_file['path'])
                if not is_valid:
                    print(f"❌ Invalid XML: {validation_message}")
                    return False
                
                print("✅ XML validation passed")
                
                # Parse transactions
                print("⚙️  Parsing SMS messages...")
                transactions, total_count = parser.parse_xml_file(selected_file['path'])
                
                if not transactions:
                    print("⚠️  No MoMo transactions found")
                    print("💡 Ensure XML contains Mobile Money SMS messages")
                    return False
                
                print(f"📊 Found {len(transactions)} MoMo transactions out of {total_count} SMS messages")
                
                # Save to database
                print("💾 Saving to database...")
                processed = DatabaseService.add_multiple_transactions(transactions)
                
                # Create upload record
                DatabaseService.add_upload_record(
                    filename=selected_file['name'],
                    total_messages=total_count,
                    processed_messages=processed,
                    status='completed'
                )
                
                print(f"✅ Successfully processed {processed} transactions!")
                
                # Show stats
                stats = DatabaseService.get_stats()
                print(f"📊 Database populated:")
                print(f"   • Transactions: {stats['total_transactions']}")
                print(f"   • Total amount: {stats['total_amount']:,.0f} RWF")
                print(f"   • Categories: {len(stats['categories'])}")
                
                return True
                
            except Exception as e:
                print(f"❌ Processing error: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Auto-processing failed: {e}")
        return False

def main():
    print("🚀 MoMo Analytics - Enhanced Start")
    print("=" * 40)
    
    # Create Flask app
    try:
        from app import create_app
        app = create_app()
        if app is None:
            print("❌ Failed to create Flask app")
            return
        print("✅ Flask application created")
    except Exception as e:
        print(f"❌ Error creating Flask app: {e}")
        return
    
    # Auto-process XML files if database is empty
    print("\n🤖 Auto-processing XML files...")
    xml_processed = auto_process_xml()
    
    # Find available port
    port = find_available_port()
    if port is None:
        print("❌ No available ports found")
        return
    
    # Print startup summary
    print(f"\n🎉 MoMo Analytics Ready!")
    print("=" * 30)
    
    if xml_processed:
        print("📊 Database populated with transaction data")
        print(f"🌐 Dashboard: http://localhost:{port}/dashboard")
    else:
        print("📤 Upload XML files through web interface")
    
    print(f"📱 Main app: http://localhost:{port}")
    print("🛑 Press Ctrl+C to stop")
    print("=" * 40)
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=port,
            use_reloader=False,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == '__main__':
    main()