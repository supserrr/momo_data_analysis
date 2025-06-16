from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    # Get the parent directory (project root) to properly locate templates and static folders
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_folder = os.path.join(parent_dir, 'templates')
    static_folder = os.path.join(parent_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_folder,
                static_folder=static_folder)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
    app.config['UPLOAD_FOLDER'] = 'data/uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Database configuration - use absolute path
    db_path = os.path.join(parent_dir, 'data', 'momo.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Create necessary directories with proper permissions
    data_dir = os.path.join(parent_dir, 'data')
    upload_dir = os.path.join(data_dir, 'uploads')
    static_css_dir = os.path.join(parent_dir, 'static', 'css')
    static_js_dir = os.path.join(parent_dir, 'static', 'js')
    
    for directory in [data_dir, upload_dir, static_css_dir, static_js_dir]:
        try:
            os.makedirs(directory, mode=0o755, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        except OSError as e:
            print(f"⚠️  Warning: Could not create directory {directory}: {e}")
    
    # Test if we can write to the data directory
    try:
        test_file = os.path.join(data_dir, 'test_write.tmp')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        print(f"✅ Data directory is writable: {data_dir}")
    except Exception as e:
        print(f"❌ Cannot write to data directory: {e}")
        print(f"📁 Please check permissions for: {data_dir}")
        return None
    
    # Initialize extensions
    db.init_app(app)
    
    # Import models after db initialization
    from .models import Transaction, UploadHistory
    
    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            print(f"✅ Database created successfully: {db_path}")
            
            # Verify database file exists
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                print(f"📁 Database file size: {size} bytes")
            else:
                print("⚠️  Database file not found after creation")
                
        except Exception as e:
            print(f"❌ Failed to create database tables: {e}")
            return None
    
    # Register routes
    from .routes import main
    app.register_blueprint(main)
    
    return app