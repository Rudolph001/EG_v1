#!/usr/bin/env python3
"""
Local database setup for Email Guardian
Simplified version that works with any app.py configuration
"""

import os
import sys
import sqlite3
from pathlib import Path

def main():
    print("========================================")
    print("Email Guardian - Local Database Setup")
    print("========================================")
    print()
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"Working directory: {current_dir}")
    
    # Check required files
    required_files = ['models.py', 'routes.py', 'app.py']
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"ERROR: Missing required files: {', '.join(missing_files)}")
        print("Make sure you're in the Email Guardian project directory")
        return False
    
    # Create directories
    print("Creating directories...")
    directories = ['uploads', 'instance', 'logs']
    for dir_name in directories:
        dir_path = current_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        print(f"✓ {dir_path}")
    
    # Set up database
    db_path = current_dir / 'instance' / 'email_guardian.db'
    print(f"\nSetting up database: {db_path}")
    
    try:
        # Create SQLite database with basic tables
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create basic tables that match the models
        print("Creating database tables...")
        
        # Email records table
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
        
        # Recipients table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipient_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email_id INTEGER,
                recipient_email TEXT NOT NULL,
                recipient_type TEXT DEFAULT 'to',
                FOREIGN KEY (email_id) REFERENCES email_record (id)
            )
        ''')
        
        # Cases table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS case (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Security rules table
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
        
        # Whitelist domains table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist_domain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Whitelist senders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS whitelist_sender (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Risk keywords table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_keyword (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                category TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                enabled BOOLEAN DEFAULT 1
            )
        ''')
        
        conn.commit()
        print("✓ Database tables created successfully")
        
        # Insert some default data
        print("Adding default configuration...")
        
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
        
        # Default whitelist domains
        default_domains = [
            'microsoft.com', 'google.com', 'amazon.com', 'office365.com', 'github.com'
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO whitelist_domain (domain)
            VALUES (?)
        ''', [(domain,) for domain in default_domains])
        
        # Default risk keywords
        default_keywords = [
            ('bitcoin', 'financial', 2.0), ('cryptocurrency', 'financial', 2.0),
            ('wire transfer', 'financial', 1.5), ('verify account', 'phishing', 2.0),
            ('click here', 'phishing', 1.5), ('download', 'malware', 1.5),
            ('urgent', 'social_engineering', 1.0), ('confidential', 'data_exfiltration', 1.0)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO risk_keyword (keyword, category, weight)
            VALUES (?, ?, ?)
        ''', default_keywords)
        
        conn.commit()
        conn.close()
        
        print("✓ Default configuration added")
        print(f"✓ Database file size: {db_path.stat().st_size} bytes")
        
        print("\n✓ Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"✗ Database setup failed: {e}")
        return False

if __name__ == '__main__':
    success = main()
    if not success:
        sys.exit(1)