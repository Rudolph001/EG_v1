#!/usr/bin/env python3
"""
Fixed local starter for Email Guardian
Handles Windows file permission and path issues
"""

import os
import sys
import logging
import tempfile
import shutil
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

def fix_database_permissions(db_path):
    """Fix database file permissions on Windows"""
    try:
        # Check if file exists and is readable
        if db_path.exists():
            # Try to read the file
            with open(db_path, 'rb') as f:
                f.read(1)
            logger.info(f"✓ Database file is readable: {db_path}")
            return True
    except (PermissionError, OSError) as e:
        logger.warning(f"Database permission issue: {e}")
        
        # Try to fix by copying to temp location and back
        try:
            temp_db = Path(tempfile.gettempdir()) / "email_guardian_temp.db"
            shutil.copy2(db_path, temp_db)
            shutil.copy2(temp_db, db_path)
            temp_db.unlink()
            logger.info("✓ Fixed database permissions")
            return True
        except Exception as fix_error:
            logger.error(f"Could not fix permissions: {fix_error}")
            return False
    
    return False

def create_local_app():
    """Create Flask app configured for local development"""
    
    print("========================================")
    print("Email Guardian - Fixed Local Server")
    print("========================================")
    print()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Get absolute paths to avoid Windows path issues
    current_dir = Path.cwd().resolve()
    instance_dir = current_dir / "instance"
    db_path = instance_dir / "email_guardian.db"
    
    print(f"Working directory: {current_dir}")
    print(f"Instance directory: {instance_dir}")
    print(f"Database path: {db_path}")
    
    # Ensure directories exist
    instance_dir.mkdir(exist_ok=True)
    
    # Check database file
    if not db_path.exists():
        print("✗ Database file not found!")
        print("Run: python quick_setup.py")
        sys.exit(1)
    
    print(f"✓ Database file exists: {db_path.stat().st_size} bytes")
    
    # Fix database permissions
    if not fix_database_permissions(db_path):
        print("✗ Cannot access database file due to permissions")
        print("Try running as Administrator or recreate database")
        sys.exit(1)
    
    # Use file:// URI format for better Windows compatibility
    db_uri = f"sqlite:///{db_path.as_posix()}"
    
    # App configuration
    app.secret_key = "dev-secret-key-for-local-development"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "connect_args": {
            "check_same_thread": False,
            "timeout": 30
        }
    }
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = str(current_dir / 'uploads')
    
    print(f"✓ Database URI: {db_uri}")
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    # Import models and routes within app context
    with app.app_context():
        try:
            # Test database connection first
            import sqlite3
            test_conn = sqlite3.connect(str(db_path))
            test_conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
            test_conn.close()
            logger.info("✓ Direct SQLite connection successful")
            
            # Import models
            import models
            logger.info("✓ Models imported")
            
            # Test SQLAlchemy connection
            from models import EmailRecord
            email_count = db.session.query(EmailRecord).count()
            logger.info(f"✓ SQLAlchemy connection successful - {email_count} emails")
            
            # Import routes
            import routes
            logger.info("✓ Routes imported")
            
            return app
            
        except ImportError as e:
            logger.error(f"✗ Import error: {e}")
            logger.error("Missing files: models.py or routes.py")
            raise
        except Exception as e:
            logger.error(f"✗ Database connection error: {e}")
            logger.error(f"Database path: {db_path}")
            logger.error(f"Database exists: {db_path.exists()}")
            logger.error(f"Database size: {db_path.stat().st_size if db_path.exists() else 'N/A'}")
            
            # Try to diagnose the issue
            if "unable to open database file" in str(e):
                logger.error("This is likely a file permissions or path issue")
                logger.error("Solutions:")
                logger.error("1. Run as Administrator")
                logger.error("2. Move project to C:\\EmailGuardian\\")
                logger.error("3. Run: python quick_setup.py")
            
            raise

def main():
    """Main entry point"""
    try:
        # Create and configure app
        app = create_local_app()
        
        print()
        print("✓ Application initialized successfully")
        print("✓ Starting server on http://localhost:5000")
        print("✓ Press Ctrl+C to stop")
        print()
        
        # Start the development server
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            threaded=True,
            use_reloader=False  # Disable reloader to avoid path issues
        )
        
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nQuick fixes to try:")
        print("1. Run as Administrator")
        print("2. Run: python quick_setup.py")
        print("3. Move project to C:\\EmailGuardian\\")
        print("4. Check antivirus isn't blocking database access")

if __name__ == '__main__':
    main()