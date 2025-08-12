#!/usr/bin/env python3
"""
Standalone runner for Email Guardian that doesn't depend on app.py modifications
This creates a complete Flask app with proper database configuration
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

def create_app():
    """Create and configure the Flask application"""
    
    print("========================================")
    print("Email Guardian - Standalone Local Server")
    print("========================================")
    print("")
    
    # Create Flask app
    app = Flask(__name__)
    
    # Set up database path
    current_dir = Path.cwd()
    instance_dir = current_dir / "instance"
    instance_dir.mkdir(exist_ok=True)
    db_path = instance_dir / "email_guardian.db"
    
    # Configure app
    app.secret_key = "dev-secret-key-for-local-development"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.as_posix()}"
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"Database file exists: {db_path.exists()}")
    if db_path.exists():
        print(f"Database file size: {db_path.stat().st_size} bytes")
    
    # Initialize database
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    # Import models and routes within app context to avoid circular imports
    with app.app_context():
        try:
            # Import all the models
            import models
            
            # Only create tables if database is empty or doesn't exist
            if not db_path.exists() or db_path.stat().st_size == 0:
                print("Creating database tables...")
                db.create_all()
                print("✓ Database tables created")
            else:
                print("✓ Using existing database")
            
            # Import routes
            import routes
            
            print("✓ Application initialized successfully")
            return app
            
        except Exception as e:
            print(f"✗ Error initializing application: {e}")
            print(f"✗ Error type: {type(e).__name__}")
            
            # Check if database file exists and is accessible
            if db_path.exists():
                try:
                    import sqlite3
                    conn = sqlite3.connect(str(db_path))
                    conn.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    conn.close()
                    print("✓ Database file is accessible")
                except Exception as db_e:
                    print(f"✗ Database file issue: {db_e}")
            else:
                print("✗ Database file does not exist")
            
            raise

if __name__ == '__main__':
    try:
        app = create_app()
        
        print("")
        print("Starting server on http://localhost:5000")
        print("Press Ctrl+C to stop the server")
        print("")
        
        # Run the application
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Failed to start server: {e}")
        print("\nTroubleshooting steps:")
        print("1. Ensure you're in the project root directory")
        print("2. Check that the database exists: instance/email_guardian.db")
        print("3. Verify all required packages are installed")
        print("4. Try running: python setup_database.py")
        sys.exit(1)