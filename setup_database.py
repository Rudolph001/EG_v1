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
    
    # Get current working directory
    current_dir = Path.cwd()
    print(f"Working directory: {current_dir}")
    
    # Check if we're in the right directory
    app_py = current_dir / "app.py"
    if not app_py.exists():
        print("✗ app.py not found in current directory")
        print("Make sure you're running this from the Email Guardian project folder")
        return False
    
    # Ensure required directories exist with proper permissions
    print("Creating required directories...")
    uploads_dir = current_dir / "uploads"
    instance_dir = current_dir / "instance"
    
    try:
        uploads_dir.mkdir(exist_ok=True)
        instance_dir.mkdir(exist_ok=True)
        print(f"✓ Created: {uploads_dir}")
        print(f"✓ Created: {instance_dir}")
    except Exception as e:
        print(f"✗ Error creating directories: {e}")
        return False
    
    # Use absolute path for database to avoid path issues
    db_path = instance_dir / "email_guardian.db"
    database_url = f"sqlite:///{db_path.as_posix()}"
    
    print(f"Database URL: {database_url}")
    
    # Set up environment for local development
    os.environ['DATABASE_URL'] = database_url
    os.environ.setdefault('SESSION_SECRET', 'dev-secret-key-for-local-development')
    
    try:
        print("Initializing database...")
        
        # Test if we can create a simple SQLite connection first
        import sqlite3
        try:
            test_conn = sqlite3.connect(str(db_path))
            test_conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER)")
            test_conn.commit()
            test_conn.close()
            print("✓ SQLite connection test passed")
        except Exception as e:
            print(f"✗ SQLite connection test failed: {e}")
            return False
        
        # Import and initialize Flask app
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Verify database file was created and has content
            if db_path.exists() and db_path.stat().st_size > 0:
                print(f"✓ Database file created: {db_path.absolute()}")
                print(f"✓ Database file size: {db_path.stat().st_size} bytes")
            else:
                print("⚠ Database file issue - file empty or missing")
                return False
                
        return True
        
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        print(f"✗ Error type: {type(e).__name__}")
        
        # Additional troubleshooting info
        print("\nDiagnostic information:")
        print(f"- Current directory: {current_dir}")
        print(f"- Instance directory exists: {instance_dir.exists()}")
        print(f"- Instance directory writable: {os.access(instance_dir, os.W_OK)}")
        print(f"- Database path: {db_path}")
        
        print("\nTroubleshooting steps:")
        print("1. Run Command Prompt as Administrator (Windows)")
        print("2. Check if antivirus is blocking file creation")
        print("3. Try a different location (not in Downloads folder)")
        print("4. Ensure all required packages are installed:")
        print("   pip install flask flask-sqlalchemy")
        
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