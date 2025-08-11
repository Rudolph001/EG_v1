
from app import app, db
from sqlalchemy import text
import logging

def migrate_database():
    """Migrate database schema to match current models"""
    with app.app_context():
        try:
            # Check if created_at column exists in email_records
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='email_records' AND column_name='created_at'
            """))
            
            if not result.fetchone():
                print("Adding created_at column to email_records table...")
                db.session.execute(text("""
                    ALTER TABLE email_records 
                    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                """))
                
                # Update existing records to have created_at = processed_at
                db.session.execute(text("""
                    UPDATE email_records 
                    SET created_at = COALESCE(processed_at, CURRENT_TIMESTAMP)
                    WHERE created_at IS NULL
                """))
                
                print("✓ Added created_at column to email_records")
            
            # Check other potential missing columns
            tables_to_check = [
                ('recipient_records', 'created_at'),
                ('cases', 'created_at'),
                ('cases', 'updated_at'),
                ('sender_metadata', 'created_at'),
                ('sender_metadata', 'updated_at'),
            ]
            
            for table_name, column_name in tables_to_check:
                result = db.session.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='{table_name}' AND column_name='{column_name}'
                """))
                
                if not result.fetchone():
                    print(f"Adding {column_name} column to {table_name} table...")
                    
                    if column_name == 'updated_at':
                        db.session.execute(text(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN {column_name} TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        """))
                    else:
                        db.session.execute(text(f"""
                            ALTER TABLE {table_name} 
                            ADD COLUMN {column_name} TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        """))
                    
                    print(f"✓ Added {column_name} column to {table_name}")
            
            db.session.commit()
            print("Database migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during migration: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_database()
