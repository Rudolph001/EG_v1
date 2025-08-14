#!/usr/bin/env python3
"""
Quick fix script for local database issues
Run this if you're getting "Dashboard data temporarily unavailable" errors
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_local_database():
    """Fix common local database issues"""
    try:
        # Ensure instance directory exists
        instance_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        logger.info(f"Instance directory: {instance_dir}")
        
        # Set environment for local development
        db_path = os.path.join(instance_dir, 'email_guardian.db')
        os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
        logger.info(f"Database path: {db_path}")
        
        # Check if database file exists
        if os.path.exists(db_path):
            logger.info("✓ Database file exists")
        else:
            logger.info("✗ Database file does not exist")
        
        # Import and test app
        from app import app, db
        from models import EmailRecord, SecurityRule, WhitelistDomain
        
        with app.app_context():
            # Test database connection
            try:
                db.session.execute(db.text('SELECT 1'))
                logger.info("✓ Database connection successful")
            except Exception as conn_error:
                logger.error(f"✗ Database connection failed: {conn_error}")
                logger.info("Creating database tables...")
                db.create_all()
                logger.info("✓ Database tables created")
            
            # Check table contents
            email_count = EmailRecord.query.count()
            rule_count = SecurityRule.query.count()
            domain_count = WhitelistDomain.query.count()
            
            logger.info(f"Database contents:")
            logger.info(f"  - Email records: {email_count}")
            logger.info(f"  - Security rules: {rule_count}")
            logger.info(f"  - Whitelist domains: {domain_count}")
            
            if rule_count == 0:
                logger.info("Adding default security rules...")
                from setup_local_db import setup_local_database
                setup_local_database()
            
            logger.info("✅ Database is ready for local development")
            return True
            
    except Exception as e:
        logger.error(f"❌ Fix failed: {str(e)}")
        logger.info("\nTroubleshooting steps:")
        logger.info("1. Make sure you're in the project directory")
        logger.info("2. Run: python setup_local_db.py")
        logger.info("3. Try running the app again: python run_local.py")
        return False

if __name__ == '__main__':
    print("🔧 Email Guardian - Database Fix Tool")
    print("=====================================")
    success = fix_local_database()
    print("\n" + "="*50)
    if success:
        print("✅ Your local database should now work properly!")
        print("You can start the app with: python run_local.py")
    else:
        print("❌ Could not fix the database issue automatically")
        print("Please check the error messages above")
    
    sys.exit(0 if success else 1)