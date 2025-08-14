
"""
Legacy migration script - replaced by database_sync.py
This file is kept for compatibility but database_sync.py is recommended.
"""

from app import app, db
from sqlalchemy import text, inspect
import logging

def migrate_database():
    """Apply database migrations - DEPRECATED: Use database_sync.py instead"""
    logging.warning("migrate_db.py is deprecated. Use 'python database_sync.py' instead.")
    
    with app.app_context():
        try:
            # Simply create all tables - SQLAlchemy handles schema updates
            db.create_all()
            logging.info("Database migration completed successfully!")

        except Exception as e:
            logging.error(f"Migration error: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_database()
