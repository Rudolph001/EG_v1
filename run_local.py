
#!/usr/bin/env python3
"""
Local development runner for Email Guardian
Use this instead of gunicorn for local development
"""

import os
import sys
from app import app

if __name__ == '__main__':
    # Set development environment
    os.environ['FLASK_ENV'] = 'development'
    
    print("========================================")
    print("Email Guardian - Local Development Server")
    print("========================================")
    print("")
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
