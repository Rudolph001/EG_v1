#!/usr/bin/env python3
"""
Database Synchronization Script for Email Guardian

This script ensures database schema compatibility between:
- Replit environment (PostgreSQL)
- Local development (SQLite)

Run this script when setting up the application locally or after schema changes.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_compatibility():
    """Check if database schema is compatible and up to date"""
    try:
        # Import after setting up the path
        from app import app, db
        import models  # Import models module
        
        with app.app_context():
            logger.info("Checking database compatibility...")
            
            # Get database type
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            is_sqlite = db_url.startswith('sqlite')
            is_postgres = 'postgresql' in db_url or 'postgres' in db_url
            
            logger.info(f"Database type: {'SQLite' if is_sqlite else 'PostgreSQL' if is_postgres else 'Unknown'}")
            
            # Create all tables
            db.create_all()
            logger.info("Database tables created/verified successfully")
            
            # Check for required tables
            inspector = inspect(db.engine)
            required_tables = [
                'email_records', 'recipient_records', 'cases', 'whitelist_domains',
                'whitelist_senders', 'security_rules', 'risk_keywords', 'exclusion_rules',
                'sender_metadata', 'processing_logs', 'email_states', 'flagged_events',
                'escalated_events', 'cleared_events'
            ]
            
            existing_tables = inspector.get_table_names()
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                logger.warning(f"Missing tables: {missing_tables}")
                logger.info("Recreating all tables...")
                db.create_all()
                logger.info("Tables recreated successfully")
            else:
                logger.info("All required tables present")
            
            # Verify critical columns exist
            verify_table_columns(inspector, is_sqlite)
            
            # Insert default data if needed
            insert_default_data()
            
            logger.info("Database compatibility check completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Database compatibility check failed: {str(e)}")
        return False

def verify_table_columns(inspector, is_sqlite):
    """Verify that all required columns exist in tables"""
    
    # Check recipient_records table for new columns
    recipient_columns = [col['name'] for col in inspector.get_columns('recipient_records')]
    required_recipient_cols = [
        'matched_security_rules', 'matched_risk_keywords', 'whitelist_reason',
        'advanced_ml_score', 'case_generated'
    ]
    
    missing_cols = [col for col in required_recipient_cols if col not in recipient_columns]
    if missing_cols:
        logger.warning(f"Missing columns in recipient_records: {missing_cols}")
        # Note: SQLAlchemy's create_all() should handle this, but we log for awareness
    
    # Check cases table
    case_columns = [col['name'] for col in inspector.get_columns('cases')]
    required_case_cols = ['risk_factors', 'recommended_actions', 'escalated', 'escalated_at']
    
    missing_case_cols = [col for col in required_case_cols if col not in case_columns]
    if missing_case_cols:
        logger.warning(f"Missing columns in cases: {missing_case_cols}")

def insert_default_data():
    """Insert default configuration data"""
    from app import db
    from models import SecurityRule, RiskKeyword, WhitelistDomain
    
    try:
        # Check if we already have default data
        if SecurityRule.query.first() is None:
            logger.info("Inserting default security rules...")
            
            default_rules = [
                SecurityRule(
                    name="Suspicious Attachment",
                    description="Flags emails with suspicious file attachments",
                    rule_type="attachment",
                    pattern=r"\.(exe|scr|bat|com|pif|vbs|js)$",
                    action="flag",
                    severity="high"
                ),
                SecurityRule(
                    name="External Sender to Internal",
                    description="Flags external senders emailing internal recipients",
                    rule_type="sender",
                    pattern=r"^(?!.*@(company\.com|internal\.domain)).*$",
                    action="flag",
                    severity="medium"
                ),
                SecurityRule(
                    name="Urgent Action Required",
                    description="Flags emails with urgent action language",
                    rule_type="subject",
                    pattern=r"(urgent|immediate|action required|verify now)",
                    action="flag",
                    severity="medium"
                )
            ]
            
            for rule in default_rules:
                db.session.add(rule)
        
        # Check if we already have default risk keywords
        if RiskKeyword.query.first() is None:
            logger.info("Inserting default risk keywords...")
            
            default_keywords = [
                # Financial
                ("bitcoin", "financial", 2.0),
                ("cryptocurrency", "financial", 2.0),
                ("wire transfer", "financial", 1.5),
                ("bank account", "financial", 1.5),
                ("payment", "financial", 1.0),
                ("invoice", "financial", 1.0),
                
                # Phishing
                ("verify account", "phishing", 2.5),
                ("suspend", "phishing", 2.0),
                ("click here", "phishing", 1.5),
                ("confirm identity", "phishing", 2.0),
                
                # Malware
                ("download", "malware", 1.5),
                ("install", "malware", 1.5),
                ("update required", "malware", 1.8),
                
                # Social Engineering
                ("confidential", "social_engineering", 1.5),
                ("secret", "social_engineering", 1.5),
                ("don't tell", "social_engineering", 2.0),
            ]
            
            for keyword, category, weight in default_keywords:
                risk_keyword = RiskKeyword(
                    keyword=keyword,
                    category=category,
                    weight=weight
                )
                db.session.add(risk_keyword)
        
        # Add some default whitelist domains for common services
        if WhitelistDomain.query.first() is None:
            logger.info("Inserting default whitelist domains...")
            
            default_domains = [
                ("github.com", "Software development platform"),
                ("stackoverflow.com", "Developer Q&A platform"),
                ("microsoft.com", "Microsoft services"),
                ("google.com", "Google services"),
            ]
            
            for domain, description in default_domains:
                whitelist_domain = WhitelistDomain(
                    domain=domain,
                    description=description
                )
                db.session.add(whitelist_domain)
        
        db.session.commit()
        logger.info("Default data insertion completed")
        
    except Exception as e:
        logger.error(f"Error inserting default data: {str(e)}")
        db.session.rollback()

def create_sqlite_local_setup():
    """Create a local SQLite database setup"""
    try:
        # Ensure instance directory exists
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        
        # Set environment for local SQLite
        db_path = os.path.join(instance_dir, 'email_guardian.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        logger.info(f"Setting up local SQLite database at: {db_path}")
        
        # Run compatibility check
        success = check_database_compatibility()
        
        if success:
            logger.info("Local SQLite database setup completed successfully!")
            logger.info(f"Database location: {db_path}")
            return True
        else:
            logger.error("Local SQLite database setup failed!")
            return False
            
    except Exception as e:
        logger.error(f"Error creating local SQLite setup: {str(e)}")
        return False

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--local':
        # Setup local SQLite database
        success = create_sqlite_local_setup()
    else:
        # Check current database compatibility
        success = check_database_compatibility()
    
    sys.exit(0 if success else 1)