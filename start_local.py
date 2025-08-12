#!/usr/bin/env python3
"""
Complete local starter for Email Guardian
This creates a fully functional Flask app for local development
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

def create_local_app():
    """Create Flask app configured for local development"""
    
    print("========================================")
    print("Email Guardian - Local Development Server")
    print("========================================")
    print()
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure for local development
    current_dir = Path.cwd()
    instance_dir = current_dir / "instance"
    db_path = instance_dir / "email_guardian.db"
    
    # App configuration
    app.secret_key = "dev-secret-key-for-local-development"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = str(current_dir / 'uploads')
    
    # Check database exists
    if not db_path.exists():
        print("✗ Database not found! Run: python setup_local_db.py")
        sys.exit(1)
    
    print(f"✓ Database: {db_path}")
    print(f"✓ Database size: {db_path.stat().st_size} bytes")
    
    # Initialize SQLAlchemy
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    # Import models and routes within app context
    with app.app_context():
        try:
            # Import models
            import models
            logger.info("✓ Models imported")
            
            # Import routes
            import routes
            logger.info("✓ Routes imported")
            
            # Test database connection
            from models import EmailRecord
            email_count = db.session.query(EmailRecord).count()
            logger.info(f"✓ Database connected - {email_count} emails in database")
            
            return app
            
        except ImportError as e:
            logger.error(f"✗ Import error: {e}")
            logger.error("Make sure you're in the project directory with models.py and routes.py")
            raise
        except Exception as e:
            logger.error(f"✗ App initialization error: {e}")
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
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n✓ Server stopped by user")
    except FileNotFoundError:
        print("\n✗ Required files missing")
        print("Make sure you have: models.py, routes.py, templates/, static/")
        print("Run the installation script first")
    except Exception as e:
        print(f"\n✗ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Run: python setup_local_db.py")
        print("2. Check you're in the project root directory")
        print("3. Verify all packages installed: pip install -r requirements.txt")

if __name__ == '__main__':
    main()