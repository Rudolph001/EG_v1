#!/usr/bin/env python3
"""
Simple local Email Guardian app - bypasses SQLAlchemy path issues
Creates a minimal Flask app that works with your existing database
"""

import os
import sys
import sqlite3
import csv
import io
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename

def create_simple_app():
    """Create a simple Flask app without SQLAlchemy complications"""
    
    print("========================================")
    print("Email Guardian - Simple Local Server")
    print("========================================")
    print()
    
    app = Flask(__name__)
    app.secret_key = "dev-secret-for-local"
    
    # Get database path
    current_dir = Path.cwd()
    db_path = current_dir / "instance" / "email_guardian.db"
    
    print(f"Working directory: {current_dir}")
    print(f"Database: {db_path}")
    
    # Check database
    if not db_path.exists():
        print("✗ Database not found! Run: python quick_setup.py")
        return None
    
    print(f"✓ Database file: {db_path.stat().st_size} bytes")
    
    # Test database connection
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        print(f"✓ Database connection successful - {len(tables)} tables found")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return None
    
    # Define routes directly in this file
    @app.route('/')
    def dashboard():
        """Main dashboard"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get email count
            cursor.execute("SELECT COUNT(*) FROM email_record")
            email_count = cursor.fetchone()[0]
            
            # Get flagged count
            cursor.execute("SELECT COUNT(*) FROM email_record WHERE flagged = 1")
            flagged_count = cursor.fetchone()[0]
            
            # Get cases count (handle different table name formats)
            try:
                cursor.execute('SELECT COUNT(*) FROM "case"')
                case_count = cursor.fetchone()[0]
            except:
                try:
                    cursor.execute('SELECT COUNT(*) FROM [case]')
                    case_count = cursor.fetchone()[0]
                except:
                    case_count = 0
            
            # Get recent emails
            cursor.execute("""
                SELECT subject, sender, risk_score, flagged, created_at 
                FROM email_record 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            recent_emails = cursor.fetchall()
            
            conn.close()
            
            stats = {
                'total_emails': email_count,
                'flagged_emails': flagged_count,
                'total_cases': case_count,
                'recent_emails': recent_emails
            }
            
            return render_template('dashboard.html', stats=stats)
            
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            return render_template('dashboard.html', stats={
                'total_emails': 0,
                'flagged_emails': 0, 
                'total_cases': 0,
                'recent_emails': []
            })
    
    @app.route('/upload', methods=['GET', 'POST'])
    def upload_page():
        """File upload page"""
        if request.method == 'POST':
            return handle_file_upload()
        return render_template('upload.html')
    
    @app.route('/emails')
    def emails():
        """Email list page"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, subject, sender, risk_score, flagged, created_at 
                FROM email_record 
                ORDER BY created_at DESC
            """)
            emails = cursor.fetchall()
            conn.close()
            
            return render_template('emails.html', emails=emails)
            
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            return render_template('emails.html', emails=[])
    
    @app.route('/cases')
    def cases():
        """Cases page"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Try different case table formats
            cases = []
            try:
                cursor.execute('SELECT id, title, severity, status, created_at FROM "case" ORDER BY created_at DESC')
                cases = cursor.fetchall()
            except:
                try:
                    cursor.execute('SELECT id, title, severity, status, created_at FROM [case] ORDER BY created_at DESC')
                    cases = cursor.fetchall()
                except:
                    pass
            
            conn.close()
            return render_template('cases.html', cases=cases)
            
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            return render_template('cases.html', cases=[])
    
    @app.route('/rules')
    def rules():
        """Security rules page"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, rule_type, severity, enabled FROM security_rule")
            rules = cursor.fetchall()
            conn.close()
            
            return render_template('rules.html', rules=rules)
            
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            return render_template('rules.html', rules=[])
    
    @app.route('/whitelist')
    def whitelist():
        """Whitelist management page"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Get domains
            cursor.execute("SELECT domain FROM whitelist_domain ORDER BY domain")
            domains = [row[0] for row in cursor.fetchall()]
            
            # Get senders
            cursor.execute("SELECT email FROM whitelist_sender ORDER BY email")
            senders = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return render_template('whitelist.html', domains=domains, senders=senders)
            
        except Exception as e:
            flash(f'Database error: {e}', 'error')
            return render_template('whitelist.html', domains=[], senders=[])
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'ok',
            'database': 'connected' if db_path.exists() else 'missing'
        })
    
    def handle_file_upload():
        """Handle CSV file upload and processing"""
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(url_for('upload_page'))
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(url_for('upload_page'))
            
            if not file.filename.lower().endswith('.csv'):
                flash('Please upload a CSV file', 'error')
                return redirect(url_for('upload_page'))
            
            # Read CSV content
            csv_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            # Process emails
            emails_processed = 0
            emails_added = 0
            
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            for row in csv_reader:
                emails_processed += 1
                
                # Extract email data
                subject = row.get('subject', '').strip()
                sender = row.get('sender', '').strip()
                recipients = row.get('recipients', '').strip()
                body = row.get('body', '').strip()
                timestamp_str = row.get('timestamp', '').strip()
                
                # Skip if no sender
                if not sender:
                    continue
                
                # Parse timestamp
                email_timestamp = None
                if timestamp_str:
                    try:
                        email_timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    except:
                        try:
                            email_timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            pass
                
                # Calculate basic risk score
                risk_score = calculate_risk_score(subject, sender, body, recipients)
                flagged = risk_score > 5.0
                case_generated = risk_score > 8.0
                
                # Insert email record
                cursor.execute('''
                    INSERT INTO email_record (subject, sender, body, timestamp, risk_score, flagged, case_generated, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (subject, sender, body, email_timestamp, risk_score, flagged, case_generated, datetime.now()))
                
                email_id = cursor.lastrowid
                emails_added += 1
                
                # Insert recipients
                if recipients:
                    recipient_list = [r.strip() for r in recipients.split(',')]
                    for recipient in recipient_list:
                        if recipient:
                            cursor.execute('''
                                INSERT INTO recipient_record (email_id, recipient_email, recipient_type)
                                VALUES (?, ?, ?)
                            ''', (email_id, recipient, 'to'))
                
                # Generate case if high risk
                if case_generated:
                    case_title = f"High Risk Email from {sender}"
                    case_description = f"Subject: {subject}\nRisk Score: {risk_score:.1f}\nSender: {sender}"
                    
                    cursor.execute('''
                        INSERT INTO [case] (title, description, severity, status, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (case_title, case_description, 'high', 'open', datetime.now()))
            
            conn.commit()
            conn.close()
            
            flash(f'Successfully processed {emails_processed} emails, added {emails_added} new records', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(url_for('upload_page'))
    
    def calculate_risk_score(subject, sender, body, recipients):
        """Calculate basic risk score for email"""
        score = 0.0
        
        # Check subject for suspicious keywords
        if subject:
            suspicious_subjects = ['urgent', 'verify', 'suspend', 'click here', 'winner', 'lottery', 'bitcoin', 'cryptocurrency']
            for keyword in suspicious_subjects:
                if keyword.lower() in subject.lower():
                    score += 2.0
        
        # Check body for suspicious content
        if body:
            suspicious_body = ['wire transfer', 'bank account', 'verify account', 'click link', 'download attachment', 'urgent action']
            for keyword in suspicious_body:
                if keyword.lower() in body.lower():
                    score += 1.5
        
        # Check for external sender patterns
        if sender:
            # Simple check for suspicious domains
            suspicious_domains = ['tempmail', '10minutemail', 'guerrillamail', 'mailinator']
            sender_domain = sender.split('@')[-1] if '@' in sender else ''
            for domain in suspicious_domains:
                if domain in sender_domain.lower():
                    score += 3.0
        
        # Check for multiple recipients (potential spam)
        if recipients:
            recipient_count = len([r for r in recipients.split(',') if r.strip()])
            if recipient_count > 5:
                score += 2.0
            elif recipient_count > 10:
                score += 4.0
        
        return min(score, 10.0)  # Cap at 10.0

    print("✓ Routes and upload handler configured")
    return app

def main():
    """Main entry point"""
    try:
        app = create_simple_app()
        if not app:
            print("✗ Failed to create application")
            sys.exit(1)
        
        print()
        print("✓ Application ready")
        print("✓ Starting server on http://localhost:5000")
        print("✓ Press Ctrl+C to stop")
        print()
        
        # Start server
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nCheck:")
        print("1. Database exists: instance/email_guardian.db")
        print("2. Templates directory exists")
        print("3. Run: python quick_setup.py")

if __name__ == '__main__':
    main()