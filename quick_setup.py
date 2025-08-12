#!/usr/bin/env python3
"""
Quick database setup - fixes the 'case' keyword issue
Run this if the main setup fails with "near case: syntax error"
"""

import os
import sys
import sqlite3
from pathlib import Path

def main():
    print("Quick Database Setup - Fixing SQL keyword issues")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    
    # Create directories
    directories = ['uploads', 'instance', 'logs']
    for dir_name in directories:
        dir_path = current_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ {dir_path}")
    
    # Set up database
    db_path = current_dir / 'instance' / 'email_guardian.db'
    print(f"\nCreating database: {db_path}")
    
    # Remove existing database if it exists and is empty/corrupted
    if db_path.exists():
        if db_path.stat().st_size < 1000:  # Less than 1KB, probably empty/corrupted
            db_path.unlink()
            print("Removed existing empty database file")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("Creating tables...")
        
        # Email records - main table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                sender TEXT NOT NULL,
                body TEXT,
                timestamp DATETIME,
                risk_score REAL DEFAULT 0.0,
                flagged BOOLEAN DEFAULT 0,
                case_generated BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ email_record table")
        
        # Recipients
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipient_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                recipient_email TEXT NOT NULL,
                recipient_type TEXT DEFAULT 'to',
                FOREIGN KEY (email_id) REFERENCES email_record (id)
            )
        ''')
        print("✓ recipient_record table")
        
        # Cases table - using quotes to escape the keyword
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS [case] (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ case table (with proper escaping)")
        
        # Security rules
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_rule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                pattern TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ security_rule table")
        
        # Whitelist tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist_domain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ whitelist_domain table")
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist_sender (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ whitelist_sender table")
        
        # Risk keywords
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_keyword (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                enabled BOOLEAN DEFAULT 1
            )
        ''')
        print("✓ risk_keyword table")
        
        conn.commit()
        
        # Add some default data
        print("\nAdding default configuration...")
        
        # Default security rules
        default_rules = [
            ('External sender to multiple recipients', 'pattern', 'external_multiple_recipients', 'medium'),
            ('Executable attachment', 'attachment', r'\.(exe|scr|bat|com|pif|vbs|js)$', 'high'),
            ('Suspicious subject patterns', 'subject', r'(urgent|immediate|action required|verify|suspend)', 'medium')
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO security_rule (name, rule_type, pattern, severity)
            VALUES (?, ?, ?, ?)
        ''', default_rules)
        print("✓ Security rules added")
        
        # Default whitelist domains
        default_domains = [
            'microsoft.com', 'google.com', 'amazon.com', 'office365.com', 'github.com'
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO whitelist_domain (domain)
            VALUES (?)
        ''', [(domain,) for domain in default_domains])
        print("✓ Whitelist domains added")
        
        # Default risk keywords
        default_keywords = [
            ('bitcoin', 'financial', 2.0),
            ('cryptocurrency', 'financial', 2.0),
            ('wire transfer', 'financial', 1.5),
            ('verify account', 'phishing', 2.0),
            ('click here', 'phishing', 1.5),
            ('download', 'malware', 1.5),
            ('urgent', 'social_engineering', 1.0),
            ('confidential', 'data_exfiltration', 1.0)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO risk_keyword (keyword, category, weight)
            VALUES (?, ?, ?)
        ''', default_keywords)
        print("✓ Risk keywords added")
        
        conn.commit()
        conn.close()
        
        print(f"\n✓ Database created successfully!")
        print(f"✓ File size: {db_path.stat().st_size} bytes")
        print(f"✓ Location: {db_path}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if success:
        print("\nYou can now run: python start_local.py")
    else:
        print("\nSetup failed. Check the error message above.")
        sys.exit(1)