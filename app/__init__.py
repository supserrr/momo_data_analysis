from flask import Flask
import os

# Import our JSON storage system
from .storage import JSONStorage

# Global storage instance
storage = None

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
    
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Initialize storage
    global storage
    storage = JSONStorage()
    
    # Register routes
    from .routes import main
    app.register_blueprint(main)
    
    return app