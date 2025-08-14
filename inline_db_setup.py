#!/usr/bin/env python3
"""
Inline database setup for installation scripts
This script embeds all necessary setup logic without external dependencies
"""

import os
import sys

def setup_database():
    # Ensure instance directory exists
    instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    # Set database URL for SQLite
    db_path = os.path.join(instance_dir, 'email_guardian.db')
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    
    try:
        from app import app, db
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print(f"✓ Database tables created at: {db_path}")
            
            # Import models after app context is set
            from models import SecurityRule, RiskKeyword, WhitelistDomain
            
            # Add basic security rules if none exist
            if SecurityRule.query.count() == 0:
                print("+ Adding default security rules...")
                
                # Create rules with basic constructor
                rule1 = SecurityRule()
                rule1.name = "Suspicious Attachment"
                rule1.description = "Flags emails with suspicious file attachments"
                rule1.rule_type = "attachment"
                rule1.pattern = r"\.(exe|scr|bat|com|pif|vbs|js)$"
                rule1.action = "flag"
                rule1.severity = "high"
                rule1.enabled = True
                
                rule2 = SecurityRule()
                rule2.name = "External Sender"
                rule2.description = "Flags external senders"
                rule2.rule_type = "sender"
                rule2.pattern = r"^(?!.*@company\.com).*$"
                rule2.action = "flag"
                rule2.severity = "medium"
                rule2.enabled = True
                
                db.session.add(rule1)
                db.session.add(rule2)
                
            # Add basic keywords if none exist
            if RiskKeyword.query.count() == 0:
                print("+ Adding default risk keywords...")
                
                keyword1 = RiskKeyword()
                keyword1.keyword = "bitcoin"
                keyword1.category = "financial"
                keyword1.weight = 2.0
                
                keyword2 = RiskKeyword()
                keyword2.keyword = "verify account"
                keyword2.category = "phishing"
                keyword2.weight = 2.5
                
                keyword3 = RiskKeyword()
                keyword3.keyword = "click here"
                keyword3.category = "phishing"
                keyword3.weight = 1.5
                
                db.session.add(keyword1)
                db.session.add(keyword2)
                db.session.add(keyword3)
                
            # Add default whitelist domain if none exist
            if WhitelistDomain.query.count() == 0:
                print("+ Adding default whitelist domains...")
                
                domain1 = WhitelistDomain()
                domain1.domain = "company.com"
                domain1.description = "Internal company domain"
                domain1.enabled = True
                
                db.session.add(domain1)
            
            # Commit all changes
            db.session.commit()
            print("✓ Default data added successfully")
            print(f"✓ Database setup complete! Tables created at: {db_path}")
            
            return True
            
    except Exception as e:
        print(f"ERROR: Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)