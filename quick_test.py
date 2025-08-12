#!/usr/bin/env python3
"""
Quick test script to diagnose local setup issues
"""

import os
import sqlite3
from pathlib import Path

def main():
    print("========================================")
    print("Email Guardian - Quick Diagnostic Test")
    print("========================================")
    print()
    
    # Basic file system checks
    print("1. File System Checks:")
    cwd = Path.cwd()
    print(f"   Current directory: {cwd}")
    print(f"   app.py exists: {(cwd / 'app.py').exists()}")
    print(f"   models.py exists: {(cwd / 'models.py').exists()}")
    
    # Directory creation test
    print("\n2. Directory Creation Test:")
    try:
        test_dir = cwd / "test_instance"
        test_dir.mkdir(exist_ok=True)
        print(f"   ✓ Can create directory: {test_dir}")
        
        # Test file creation
        test_file = test_dir / "test.db"
        test_file.touch()
        print(f"   ✓ Can create file: {test_file}")
        
        # Clean up
        test_file.unlink()
        test_dir.rmdir()
        print("   ✓ Test cleanup successful")
        
    except Exception as e:
        print(f"   ✗ Directory/file creation failed: {e}")
        return False
    
    # SQLite test
    print("\n3. SQLite Test:")
    try:
        test_db = cwd / "test_sqlite.db"
        conn = sqlite3.connect(str(test_db))
        conn.execute("CREATE TABLE test (id INTEGER)")
        conn.commit()
        conn.close()
        print("   ✓ SQLite works")
        
        # Clean up
        test_db.unlink()
        
    except Exception as e:
        print(f"   ✗ SQLite test failed: {e}")
        return False
    
    # Python imports test
    print("\n4. Python Imports Test:")
    try:
        import flask
        print(f"   ✓ Flask version: {flask.__version__}")
    except ImportError:
        print("   ✗ Flask not installed")
        return False
    
    try:
        import flask_sqlalchemy
        print(f"   ✓ Flask-SQLAlchemy available")
    except ImportError:
        print("   ✗ Flask-SQLAlchemy not installed")
        return False
    
    print("\n✓ All basic tests passed!")
    print("\nTry running: python setup_database.py")
    return True

if __name__ == '__main__':
    main()