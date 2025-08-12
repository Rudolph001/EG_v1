#!/usr/bin/env python3
"""
Standalone database setup script for Email Guardian
This script ensures proper database initialization for local development
"""

import os
import sys
from pathlib import Path

def setup_database():
    """Set up the database with proper error handling"""
    
    # Ensure required directories exist
    print("Creating required directories...")
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    print("✓ Directories created")
    
    # Set up environment for local development
    os.environ.setdefault('DATABASE_URL', 'sqlite:///instance/email_guardian.db')
    os.environ.setdefault('SESSION_SECRET', 'dev-secret-key-for-local-development')
    
    try:
        print("Initializing database...")
        
        # Import and initialize
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database initialized successfully")
            
            # Verify database file was created
            db_path = Path('instance/email_guardian.db')
            if db_path.exists():
                print(f"✓ Database file created: {db_path.absolute()}")
            else:
                print("⚠ Database file not found at expected location")
                
        return True
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure you're running this from the project root directory")
        print("2. Ensure all required packages are installed:")
        print("   pip install flask flask-sqlalchemy")
        print("3. Check that app.py and models.py exist in the current directory")
        return False

if __name__ == '__main__':
    print("========================================")
    print("Email Guardian - Database Setup")
    print("========================================")
    print("")
    
    success = setup_database()
    
    if success:
        print("\n✓ Database setup completed successfully!")
        print("\nYou can now run the application with:")
        print("  python run_local.py")
    else:
        print("\n✗ Database setup failed")
        sys.exit(1)