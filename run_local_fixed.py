#!/usr/bin/env python3
"""
Fixed local development runner for Email Guardian
This version ensures proper environment setup before importing the app
"""

import os
import sys
from pathlib import Path

def setup_local_environment():
    """Set up local environment variables before importing app"""
    
    # Set up database URL for local development
    if not os.environ.get('DATABASE_URL'):
        instance_dir = Path('instance')
        instance_dir.mkdir(exist_ok=True)
        db_path = instance_dir / 'email_guardian.db'
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path.as_posix()}'
    
    # Set session secret for local development
    if not os.environ.get('SESSION_SECRET'):
        os.environ['SESSION_SECRET'] = 'dev-secret-key-for-local-development'
    
    # Set Flask environment
    os.environ['FLASK_ENV'] = 'development'

if __name__ == '__main__':
    print("========================================")
    print("Email Guardian - Local Development Server")
    print("========================================")
    print("")
    
    # Set up environment before importing app
    setup_local_environment()
    
    print(f"Database: {os.environ.get('DATABASE_URL')}")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
        # Now import the app after environment is set up
        from app import app
        
        # Run with Flask development server
        app.run(
            host='127.0.0.1',  # localhost for local development
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure database was initialized: python setup_database.py")
        print("2. Check that all packages are installed")
        print("3. Verify you're in the project root directory")
        sys.exit(1)