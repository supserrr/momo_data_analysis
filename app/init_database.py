#!/usr/bin/env python3
"""
Database Initialization Script for MoMo Analytics

This script creates the SQLite database and initializes all tables.
Run this before starting the application for the first time.
"""

import os
import sys
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Transaction, UploadHistory

def init_database():
    """Initialize the database with all required tables"""
    
    print("🔧 Initializing MoMo Analytics Database...")
    print("=" * 50)
    
    # Create the Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Check if database exists
            db_path = 'data/momo.db'
            db_exists = os.path.exists(db_path)
            
            if db_exists:
                print(f"📁 Database file already exists: {db_path}")
                choice = input("🤔 Do you want to recreate the database? (y/N): ").lower()
                if choice in ['y', 'yes']:
                    os.remove(db_path)
                    print("🗑️  Old database removed")
                else:
                    print("✅ Keeping existing database")
                    return
            
            # Create all tables
            print("🏗️  Creating database tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Database created successfully: {db_path}")
            print(f"📊 Tables created: {', '.join(tables)}")
            
            # Display table schemas
            print("\n📋 Table Schemas:")
            print("-" * 30)
            
            for table_name in tables:
                columns = inspector.get_columns(table_name)
                print(f"\n🏷️  {table_name.upper()}:")
                for col in columns:
                    col_type = str(col['type'])
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    primary_key = " (PRIMARY KEY)" if col.get('primary_key') else ""
                    print(f"  • {col['name']}: {col_type} {nullable}{primary_key}")
            
            # Add some sample data for testing (optional)
            add_sample = input("\n🎯 Add sample transaction for testing? (y/N): ").lower()
            if add_sample in ['y', 'yes']:
                sample_transaction = Transaction(
                    transaction_id="TEST001",
                    date=datetime.now(),
                    amount=1000.0,
                    fee=50.0,
                    balance=5000.0,
                    category="incoming_money",
                    recipient_name="Test User",
                    sender_name="Sample Sender",
                    message="Test transaction",
                    raw_body="Test SMS: You have received 1000 RWF from Sample Sender"
                )
                
                db.session.add(sample_transaction)
                db.session.commit()
                print("✅ Sample transaction added")
            
            print("\n🎉 Database initialization complete!")
            print("🚀 You can now run the application with: python run.py")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            sys.exit(1)

def show_database_info():
    """Display information about the current database"""
    
    app = create_app()
    
    with app.app_context():
        try:
            db_path = 'data/momo.db'
            
            if not os.path.exists(db_path):
                print("❌ Database file not found. Run init_database() first.")
                return
            
            # Get database info
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("📊 Database Information")
            print("=" * 30)
            print(f"📁 Location: {db_path}")
            print(f"📦 Size: {os.path.getsize(db_path)} bytes")
            print(f"🏷️  Tables: {len(tables)}")
            
            # Get record counts
            for table_name in tables:
                if table_name == 'transactions':
                    count = Transaction.query.count()
                elif table_name == 'upload_history':
                    count = UploadHistory.query.count()
                else:
                    count = "Unknown"
                
                print(f"  • {table_name}: {count} records")
            
        except Exception as e:
            print(f"❌ Error getting database info: {e}")

def reset_database():
    """Reset the database (drop all tables and recreate)"""
    
    print("⚠️  WARNING: This will delete ALL data in the database!")
    confirm = input("Type 'RESET' to confirm: ")
    
    if confirm != 'RESET':
        print("❌ Reset cancelled")
        return
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  Dropping all tables...")
            db.drop_all()
            
            print("🏗️  Recreating tables...")
            db.create_all()
            
            print("✅ Database reset complete!")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MoMo Analytics Database Management")
    parser.add_argument("action", nargs="?", default="init", 
                       choices=["init", "info", "reset"],
                       help="Action to perform (default: init)")
    
    args = parser.parse_args()
    
    if args.action == "init":
        init_database()
    elif args.action == "info":
        show_database_info()
    elif args.action == "reset":
        reset_database()