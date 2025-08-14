#!/usr/bin/env python3
"""
Simple database setup script for local SQLite development

Run this script on your local machine to set up the SQLite database
with all required tables and default data.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_local_database():
    """Set up local SQLite database"""
    try:
        # Ensure we're using SQLite for local development
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        
        db_path = os.path.join(instance_dir, 'email_guardian.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        
        logger.info(f"Setting up SQLite database at: {db_path}")
        
        # Import app and models
        from app import app, db
        from models import (SecurityRule, RiskKeyword, WhitelistDomain, 
                          EmailRecord, RecipientRecord, Case)
        
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Add default security rules if none exist
            if SecurityRule.query.count() == 0:
                logger.info("Adding default security rules...")
                
                rules = [
                    SecurityRule(
                        name="Suspicious Attachment",
                        description="Flags emails with suspicious file attachments",
                        rule_type="attachment",
                        pattern=r"\.(exe|scr|bat|com|pif|vbs|js)$",
                        action="flag",
                        severity="high"
                    ),
                    SecurityRule(
                        name="External Sender",
                        description="Flags external senders",
                        rule_type="sender", 
                        pattern=r"^(?!.*@company\.com).*$",
                        action="flag",
                        severity="medium"
                    )
                ]
                
                for rule in rules:
                    db.session.add(rule)
            
            # Add default risk keywords if none exist
            if RiskKeyword.query.count() == 0:
                logger.info("Adding default risk keywords...")
                
                keywords = [
                    ("bitcoin", "financial", 2.0),
                    ("verify account", "phishing", 2.5),
                    ("click here", "phishing", 1.5),
                    ("download", "malware", 1.5),
                    ("confidential", "social_engineering", 1.5)
                ]
                
                for keyword, category, weight in keywords:
                    risk_keyword = RiskKeyword(
                        keyword=keyword,
                        category=category,
                        weight=weight
                    )
                    db.session.add(risk_keyword)
            
            # Add default whitelist domains if none exist
            if WhitelistDomain.query.count() == 0:
                logger.info("Adding default whitelist domains...")
                
                domains = [
                    ("github.com", "Software development platform"),
                    ("google.com", "Google services")
                ]
                
                for domain, description in domains:
                    whitelist = WhitelistDomain(
                        domain=domain,
                        description=description
                    )
                    db.session.add(whitelist)
            
            # Commit all changes
            db.session.commit()
            logger.info("Default data added successfully")
            
            # Verify setup
            table_count = len(db.metadata.tables)
            logger.info(f"Database setup complete! {table_count} tables created.")
            logger.info(f"Database location: {db_path}")
            
            return True
            
    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False

if __name__ == '__main__':
    success = setup_local_database()
    if success:
        print("\n✅ Local database setup completed successfully!")
        print("You can now run the application locally with: python run_local.py")
    else:
        print("\n❌ Database setup failed. Check the error messages above.")
    
    sys.exit(0 if success else 1)