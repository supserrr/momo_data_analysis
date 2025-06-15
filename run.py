#!/usr/bin/env python3
"""
MoMo Analytics Application Runner

This script starts the Flask application for MoMo (Mobile Money) SMS data analysis.
It automatically handles port selection and creates necessary directories.
"""

import os
import sys
import socket
import logging
from app import create_app

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_directories():
    """Create necessary directories for the application"""
    directories = [
        'data',
        'static',
        'static/css',
        'static/js',
        'templates',
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except Exception as e:
            print(f"⚠️  Warning: Could not create directory {directory}: {e}")

def is_port_available(port):
    """Check if a port is available for use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def find_available_port(start_port=5000, max_attempts=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return None

def print_startup_info():
    """Print application startup information"""
    print("=" * 60)
    print("🚀 MoMo Analytics Application")
    print("=" * 60)
    print("📱 Mobile Money SMS Data Analysis Platform")
    print("🔧 Built with Flask + JSON Storage")
    print("📊 Features: Upload, Parse, Analyze, Visualize")
    print("=" * 60)

def print_features():
    """Print available features"""
    print("\n🌟 Available Features:")
    features = [
        "✅ Auto-detect XML files in data/ folder",
        "✅ Drag & drop file upload interface",
        "✅ SMS transaction parsing and categorization",
        "✅ Interactive dashboard with charts",
        "✅ Transaction filtering and search",
        "✅ CSV export functionality",
        "✅ Dark/Light theme toggle",
        "✅ Mobile-responsive design",
        "✅ JSON-based storage (no database setup needed)"
    ]
    
    for feature in features:
        print(f"   {feature}")

def print_usage_instructions():
    """Print usage instructions"""
    print("\n📝 How to use:")
    print("   1. Place XML files in the 'data/' folder, or")
    print("   2. Upload files through the web interface")
    print("   3. View analytics on the dashboard")
    print("   4. Export data as CSV when needed")

def main():
    """Main application entry point"""
    # Set up logging
    setup_logging()
    
    # Print startup information
    print_startup_info()
    
    # Create necessary directories
    print("\n📁 Setting up directory structure...")
    create_directories()
    
    # Print features and instructions
    print_features()
    print_usage_instructions()
    
    # Create Flask app
    print("\n🔧 Initializing Flask application...")
    try:
        app = create_app()
        print("✅ Flask application initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Flask application: {e}")
        sys.exit(1)
    
    # Find available port
    print("\n🔍 Finding available port...")
    port = find_available_port()
    
    if port is None:
        print("❌ No available ports found. Please free up ports 5000-5010")
        print("💡 On macOS, try: System Preferences > Sharing > Disable 'AirPlay Receiver'")
        sys.exit(1)
    
    # Start the application
    print(f"\n🚀 Starting MoMo Analytics on port {port}...")
    print(f"📱 Open your browser and go to: http://localhost:{port}")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(
            debug=True,
            host='0.0.0.0',
            port=port,
            use_reloader=False,  # Disable reloader to prevent double startup messages
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()