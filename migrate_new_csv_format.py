#!/usr/bin/env python3
"""
Database migration script for new CSV format
Adds new fields: time_month to email_records and updates termination to termination_date in recipient_records
"""

import os
import logging
from sqlalchemy import text
from app import app, db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Run database migration for new CSV format"""
    try:
        with app.app_context():
            logger.info("Starting database migration for new CSV format...")
            
            # Check if we're using SQLite or PostgreSQL
            database_url = os.environ.get('DATABASE_URL', '')
            is_sqlite = database_url.startswith('sqlite')
            
            # Add time_month column to email_records if it doesn't exist
            try:
                if is_sqlite:
                    db.session.execute(text("ALTER TABLE email_records ADD COLUMN time_month VARCHAR(20)"))
                else:
                    db.session.execute(text("ALTER TABLE email_records ADD COLUMN time_month VARCHAR(20)"))
                logger.info("✓ Added time_month column to email_records")
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    logger.info("✓ time_month column already exists in email_records")
                else:
                    logger.error(f"Error adding time_month column: {e}")
                    
            # Rename termination to termination_date in recipient_records
            try:
                if is_sqlite:
                    # SQLite doesn't support column renaming directly, need to recreate table
                    # Check if old column exists
                    result = db.session.execute(text("PRAGMA table_info(recipient_records)")).fetchall()
                    columns = [row[1] for row in result]
                    
                    if 'termination' in columns and 'termination_date' not in columns:
                        # Add new column and copy data
                        db.session.execute(text("ALTER TABLE recipient_records ADD COLUMN termination_date VARCHAR(50)"))
                        db.session.execute(text("UPDATE recipient_records SET termination_date = termination"))
                        logger.info("✓ Added termination_date column and copied data from termination")
                        
                        # Note: We'll keep both columns for now to avoid data loss
                        logger.info("✓ Keeping original termination column for backward compatibility")
                    elif 'termination_date' in columns:
                        logger.info("✓ termination_date column already exists")
                    else:
                        # Neither column exists, add termination_date
                        db.session.execute(text("ALTER TABLE recipient_records ADD COLUMN termination_date VARCHAR(50)"))
                        logger.info("✓ Added termination_date column")
                else:
                    # PostgreSQL
                    # Check if columns exist
                    result = db.session.execute(text("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'recipient_records' 
                        AND column_name IN ('termination', 'termination_date')
                    """)).fetchall()
                    existing_columns = [row[0] for row in result]
                    
                    if 'termination' in existing_columns and 'termination_date' not in existing_columns:
                        # Rename the column
                        db.session.execute(text("ALTER TABLE recipient_records RENAME COLUMN termination TO termination_date"))
                        logger.info("✓ Renamed termination column to termination_date")
                    elif 'termination_date' in existing_columns:
                        logger.info("✓ termination_date column already exists")
                    else:
                        # Add new column
                        db.session.execute(text("ALTER TABLE recipient_records ADD COLUMN termination_date VARCHAR(50)"))
                        logger.info("✓ Added termination_date column")
                        
            except Exception as e:
                if "already exists" in str(e) or "duplicate column" in str(e).lower():
                    logger.info("✓ termination_date column already exists")
                else:
                    logger.error(f"Error with termination_date column: {e}")
            
            # Remove old account_type and wordlist columns that are no longer in the new CSV format
            try:
                # These columns are not in the new CSV format, but we'll keep them for backward compatibility
                # Just log that they exist but won't be populated by new imports
                logger.info("ℹ Note: account_type, wordlist_attachment, wordlist_subject columns exist but won't be used in new CSV format")
            except Exception as e:
                logger.info("Old columns may not exist, which is fine for new installations")
            
            # Commit the changes
            db.session.commit()
            logger.info("✅ Database migration completed successfully!")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = migrate_database()
    if success:
        print("✅ Migration completed successfully!")
    else:
        print("❌ Migration failed!")
        exit(1)