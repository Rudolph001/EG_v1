
#!/usr/bin/env python3
"""
Local development runner for Email Guardian
Use this instead of gunicorn for local development
"""

import os
import sys
from app import app, db

def ensure_database():
    """Ensure database is initialized"""
    try:
        with app.app_context():
            # Check if database exists and is accessible
            with db.engine.connect() as conn:
                conn.execute(db.text('SELECT 1'))
            print("✓ Database connection verified")
    except Exception as e:
        print(f"⚠ Database issue detected: {e}")
        print("Initializing database...")
        try:
            with app.app_context():
                db.create_all()
                print("✓ Database initialized successfully")
        except Exception as init_error:
            print(f"✗ Failed to initialize database: {init_error}")
            print("Run 'python setup_local_db.py' first to set up the database")
            sys.exit(1)

if __name__ == '__main__':
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    
    print("========================================")
    print("Email Guardian - Local Development Server")
    print("========================================")
    print("")
    
    # Ensure required directories exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Check database
    ensure_database()
    
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("Starting server on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("")
    
    try:
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
        sys.exit(1)
