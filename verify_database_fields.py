
#!/usr/bin/env python3
"""
Database Field Verification Script
Ensures all SQLite database fields match the expected schema
"""

import os
import sys
from sqlalchemy import inspect, text
from app import app, db
from models import *

def verify_and_fix_database_fields():
    """Verify and fix database field names and structure"""
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            
            print("🔍 Verifying database field names...")
            
            # Check EmailRecord table
            email_columns = [col['name'] for col in inspector.get_columns('email_records')]
            required_email_fields = [
                'id', 'timestamp', 'sender', 'subject', 'attachments', 
                'original_recipients', 'time_month', 'processed_at', 
                'pipeline_status', 'created_at'
            ]
            
            missing_email_fields = [f for f in required_email_fields if f not in email_columns]
            if missing_email_fields:
                print(f"❌ Missing email_records fields: {missing_email_fields}")
            else:
                print("✅ email_records table fields are correct")
            
            # Check RecipientRecord table
            recipient_columns = [col['name'] for col in inspector.get_columns('recipient_records')]
            required_recipient_fields = [
                'id', 'email_id', 'recipient', 'recipient_email_domain',
                'leaver', 'termination_date', 'bunit', 'department',
                'user_response', 'final_outcome', 'policy_name', 'justifications',
                'excluded', 'whitelisted', 'security_score', 'risk_score',
                'ml_score', 'advanced_ml_score', 'flagged', 'case_generated',
                'matched_security_rules', 'matched_risk_keywords', 'whitelist_reason'
            ]
            
            missing_recipient_fields = [f for f in required_recipient_fields if f not in recipient_columns]
            if missing_recipient_fields:
                print(f"❌ Missing recipient_records fields: {missing_recipient_fields}")
            else:
                print("✅ recipient_records table fields are correct")
            
            # Check SenderMetadata table
            sender_columns = [col['name'] for col in inspector.get_columns('sender_metadata')]
            required_sender_fields = [
                'id', 'email', 'email_domain', 'leaver', 'termination',
                'account_type', 'bunit', 'department', 'active',
                'last_email_sent', 'total_emails_sent', 'created_at', 'updated_at'
            ]
            
            missing_sender_fields = [f for f in required_sender_fields if f not in sender_columns]
            if missing_sender_fields:
                print(f"❌ Missing sender_metadata fields: {missing_sender_fields}")
            else:
                print("✅ sender_metadata table fields are correct")
            
            # Recreate all tables to ensure correct schema
            print("\n🔧 Recreating database tables with correct schema...")
            db.drop_all()
            db.create_all()
            
            print("✅ Database tables recreated successfully!")
            
            # Verify the recreation worked
            inspector = inspect(db.engine)
            all_tables = inspector.get_table_names()
            expected_tables = [
                'email_records', 'recipient_records', 'cases', 'whitelist_domains',
                'whitelist_senders', 'security_rules', 'risk_keywords', 'exclusion_rules',
                'sender_metadata', 'processing_logs', 'email_states', 'flagged_events',
                'escalated_events', 'cleared_events'
            ]
            
            missing_tables = [t for t in expected_tables if t not in all_tables]
            if missing_tables:
                print(f"❌ Missing tables after recreation: {missing_tables}")
                return False
            else:
                print("✅ All required tables present after recreation")
            
            # Add some default data
            add_default_data()
            
            print("\n🎉 Database field verification and fix completed successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Error during database verification: {str(e)}")
            return False

def add_default_data():
    """Add default data to empty tables"""
    try:
        # Add default security rules if none exist
        if SecurityRule.query.count() == 0:
            print("📝 Adding default security rules...")
            
            default_rules = [
                SecurityRule(
                    name="Suspicious Attachment",
                    description="Flags emails with suspicious file attachments",
                    rule_type="attachment",
                    pattern=r"\.(exe|scr|bat|com|pif|vbs|js)$",
                    action="flag",
                    severity="high",
                    active=True
                ),
                SecurityRule(
                    name="External Sender",
                    description="Flags external senders",
                    rule_type="sender",
                    pattern=r"^(?!.*@company\.com).*$",
                    action="flag",
                    severity="medium",
                    active=True
                )
            ]
            
            for rule in default_rules:
                db.session.add(rule)
        
        # Add default risk keywords if none exist
        if RiskKeyword.query.count() == 0:
            print("📝 Adding default risk keywords...")
            
            default_keywords = [
                RiskKeyword(keyword="bitcoin", category="financial", weight=2.0, active=True),
                RiskKeyword(keyword="verify account", category="phishing", weight=2.5, active=True),
                RiskKeyword(keyword="click here", category="phishing", weight=1.5, active=True),
                RiskKeyword(keyword="urgent", category="social_engineering", weight=1.8, active=True)
            ]
            
            for keyword in default_keywords:
                db.session.add(keyword)
        
        # Add default whitelist domain if none exist
        if WhitelistDomain.query.count() == 0:
            print("📝 Adding default whitelist domain...")
            
            default_domain = WhitelistDomain(
                domain="company.com",
                description="Internal company domain",
                active=True
            )
            db.session.add(default_domain)
        
        db.session.commit()
        print("✅ Default data added successfully")
        
    except Exception as e:
        print(f"❌ Error adding default data: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    success = verify_and_fix_database_fields()
    sys.exit(0 if success else 1)
