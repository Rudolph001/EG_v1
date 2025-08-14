#!/usr/bin/env python3
"""
Clean existing database records to convert '-' values to empty strings
"""

import os
import logging
from sqlalchemy import text, update
from app import app, db
from models import EmailRecord, RecipientRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_null_values():
    """Clean existing database records to convert '-' to empty strings"""
    try:
        with app.app_context():
            logger.info("Cleaning existing database records...")
            
            # Clean EmailRecord fields
            email_fields = ['sender', 'subject', 'attachments', 'original_recipients', 'time_month']
            for field in email_fields:
                try:
                    result = db.session.execute(
                        text(f"UPDATE email_records SET {field} = '' WHERE {field} = '-'")
                    )
                    if result.rowcount > 0:
                        logger.info(f"✓ Cleaned {result.rowcount} records in email_records.{field}")
                except Exception as e:
                    logger.warning(f"Could not clean email_records.{field}: {e}")
            
            # Clean RecipientRecord fields
            recipient_fields = [
                'recipient', 'recipient_email_domain', 'leaver', 'termination_date', 
                'bunit', 'department', 'user_response', 'final_outcome', 
                'policy_name', 'justifications'
            ]
            for field in recipient_fields:
                try:
                    result = db.session.execute(
                        text(f"UPDATE recipient_records SET {field} = '' WHERE {field} = '-'")
                    )
                    if result.rowcount > 0:
                        logger.info(f"✓ Cleaned {result.rowcount} records in recipient_records.{field}")
                except Exception as e:
                    logger.warning(f"Could not clean recipient_records.{field}: {e}")
            
            # Also clean old 'termination' field if it exists
            try:
                result = db.session.execute(
                    text("UPDATE recipient_records SET termination = '' WHERE termination = '-'")
                )
                if result.rowcount > 0:
                    logger.info(f"✓ Cleaned {result.rowcount} records in recipient_records.termination")
            except Exception as e:
                logger.info("Note: termination field may not exist (which is fine)")
            
            db.session.commit()
            logger.info("✅ Database cleaning completed successfully!")
            
            return True
            
    except Exception as e:
        logger.error(f"Database cleaning failed: {e}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    success = clean_null_values()
    if success:
        print("✅ Database cleaning completed successfully!")
    else:
        print("❌ Database cleaning failed!")
        exit(1)