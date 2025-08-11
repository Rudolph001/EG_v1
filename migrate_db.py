from app import app, db
from sqlalchemy import text
import logging

def migrate_database():
    """Apply database migrations"""
    with app.app_context():
        try:
            # Check if new columns exist, add them if not
            inspector = db.inspect(db.engine)
            recipient_columns = [col['name'] for col in inspector.get_columns('recipient_records')]

            if 'matched_security_rules' not in recipient_columns:
                db.engine.execute('ALTER TABLE recipient_records ADD COLUMN matched_security_rules TEXT')
                logging.info("Added matched_security_rules column")

            if 'matched_risk_keywords' not in recipient_columns:
                db.engine.execute('ALTER TABLE recipient_records ADD COLUMN matched_risk_keywords TEXT')
                logging.info("Added matched_risk_keywords column")

            if 'whitelist_reason' not in recipient_columns:
                db.engine.execute('ALTER TABLE recipient_records ADD COLUMN whitelist_reason VARCHAR(255)')
                logging.info("Added whitelist_reason column")

            # Create any missing tables
            db.create_all()
            logging.info("Database migration completed successfully!")

        except Exception as e:
            logging.error(f"Migration error: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_database()