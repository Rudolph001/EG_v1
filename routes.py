import os
import csv
import json
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from sqlalchemy import func
from app import app, db
from models import *
from pipeline import EmailProcessingPipeline
from datetime import datetime, timedelta
import logging

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'

@app.route('/')
def dashboard():
    """Main dashboard with analytics"""
    try:
        # Get recent statistics
        total_emails = EmailRecord.query.count()
        total_recipients = RecipientRecord.query.count()
        total_cases = Case.query.count()
        open_cases = Case.query.filter_by(status='open').count()
        flagged_recipients = RecipientRecord.query.filter_by(flagged=True).count()
    except Exception as e:
        logging.error(f"Database query error in dashboard: {str(e)}")
        # Return dashboard with zero stats if database query fails
        stats = {
            'total_emails': 0,
            'total_recipients': 0,
            'total_cases': 0,
            'open_cases': 0,
            'flagged_recipients': 0,
            'total_senders': 0,
            'leaver_senders': 0,
            'sender_domains': 0,
            'recent_cases': [],
            'avg_security_score': 0,
            'avg_ml_score': 0,
            'avg_risk_score': 0,
            'top_risk_senders': [],
            'top_active_senders': []
        }
        flash('Dashboard data temporarily unavailable. Please check database connection.', 'warning')
        return render_template('dashboard.html', stats=stats)
    
    # Get sender statistics
    total_senders = SenderMetadata.query.count()
    leaver_senders = SenderMetadata.query.filter_by(leaver='yes').count()
    
    # Get unique sender domains
    sender_domains = db.session.query(func.count(func.distinct(SenderMetadata.email_domain))).scalar() or 0
    
    # Get recent cases
    recent_cases = Case.query.order_by(Case.created_at.desc()).limit(5).all()
    
    # Get processing statistics for the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    
    # Get average risk scores
    avg_security_score = db.session.query(func.avg(RecipientRecord.security_score)).scalar() or 0
    avg_ml_score = db.session.query(func.avg(RecipientRecord.ml_score)).scalar() or 0
    avg_risk_score = db.session.query(func.avg(RecipientRecord.risk_score)).scalar() or 0
    
    # Get top risk senders (senders with highest average risk scores)
    top_risk_senders = db.session.query(
        EmailRecord.sender,
        func.avg(RecipientRecord.risk_score).label('avg_risk'),
        func.count(RecipientRecord.id).label('email_count')
    ).join(RecipientRecord).group_by(EmailRecord.sender).order_by(
        func.avg(RecipientRecord.risk_score).desc()
    ).limit(5).all()
    
    # Get sender activity (top senders by email volume)
    top_active_senders = db.session.query(
        EmailRecord.sender,
        func.count(EmailRecord.id).label('email_count')
    ).group_by(EmailRecord.sender).order_by(
        func.count(EmailRecord.id).desc()
    ).limit(5).all()
    
    stats = {
        'total_emails': total_emails,
        'total_recipients': total_recipients,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'flagged_recipients': flagged_recipients,
        'total_senders': total_senders,
        'leaver_senders': leaver_senders,
        'sender_domains': sender_domains,
        'recent_cases': recent_cases,
        'avg_security_score': round(avg_security_score, 2),
        'avg_ml_score': round(avg_ml_score, 2),
        'avg_risk_score': round(avg_risk_score, 2),
        'top_risk_senders': top_risk_senders,
        'top_active_senders': top_active_senders
    }
    
    return render_template('dashboard.html', stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
def upload_csv():
    """Handle CSV file upload and processing"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            try:
                # Process the CSV file
                pipeline = EmailProcessingPipeline()
                results = pipeline.process_csv(filepath)
                
                flash(f'Successfully processed {results["total_emails"]} emails with {results["total_recipients"]} recipients', 'success')
                
                # Clean up uploaded file
                os.remove(filepath)
                
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                logging.error(f"Error processing CSV: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                
        else:
            flash('Invalid file type. Please upload a CSV file.', 'error')
    
    return render_template('upload.html')

@app.route('/cases')
def cases():
    """Display all cases"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    severity_filter = request.args.get('severity', '')
    
    query = Case.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
    
    cases = query.order_by(Case.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('cases.html', cases=cases, 
                         status_filter=status_filter, severity_filter=severity_filter)

@app.route('/cases/<int:case_id>')
def case_detail(case_id):
    """Display detailed case information"""
    case = Case.query.get_or_404(case_id)
    return render_template('case_detail.html', case=case)

@app.route('/cases/<int:case_id>/update', methods=['POST'])
def update_case(case_id):
    """Update case status or assignment"""
    case = Case.query.get_or_404(case_id)
    
    case.status = request.form.get('status', case.status)
    case.assigned_to = request.form.get('assigned_to', case.assigned_to)
    
    if request.form.get('escalate') == 'true':
        case.escalated = True
        case.escalated_at = datetime.utcnow()
    
    if case.status in ['resolved', 'closed']:
        case.resolved_at = datetime.utcnow()
    
    case.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Case updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating case: {str(e)}', 'error')
    
    return redirect(url_for('case_detail', case_id=case_id))


@app.route('/emails')
def emails():
    """Display all processed emails"""
    page = request.args.get('page', 1, type=int)
    
    emails = EmailRecord.query.order_by(EmailRecord.processed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('emails.html', emails=emails)

@app.route('/emails/<int:email_id>')
def email_detail(email_id):
    """Display detailed email information"""
    email = EmailRecord.query.get_or_404(email_id)
    return render_template('email_detail.html', email=email)

@app.route('/recipients')
def recipients():
    """Display all recipients"""
    page = request.args.get('page', 1, type=int)
    
    recipients = RecipientRecord.query.order_by(RecipientRecord.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    return render_template('recipients.html', recipients=recipients)

@app.route('/reports')
def reports():
    """Reports dashboard"""
    return render_template('reports.html')

@app.route('/rules-engine')
def rules_engine():
    """Security rules management"""
    rules = SecurityRule.query.all()
    return render_template('rules_engine.html', rules=rules)

@app.route('/rules-engine/add', methods=['POST'])
def add_security_rule():
    """Add new security rule with multiple conditions"""
    import json
    
    try:
        # Extract conditions from form data
        conditions = []
        form_data = request.form.to_dict()
        
        # Parse conditions from form
        for key in form_data:
            if key.startswith('edit_conditions[') and key.endswith('][field]'):
                index = key.split('[')[1].split(']')[0]
                field_key = f'edit_conditions[{index}][field]'
                operator_key = f'edit_conditions[{index}][operator]'
                value_key = f'edit_conditions[{index}][value]'
                
                if field_key in form_data and operator_key in form_data:
                    condition = {
                        'field': form_data[field_key],
                        'operator': form_data[operator_key],
                        'value': form_data.get(value_key, '')
                    }
                    conditions.append(condition)
            elif key.startswith('conditions[') and key.endswith('][field]'):
                # Handle regular conditions too
                index = key.split('[')[1].split(']')[0]
                field_key = f'conditions[{index}][field]'
                operator_key = f'conditions[{index}][operator]'
                value_key = f'conditions[{index}][value]'
                
                if field_key in form_data and operator_key in form_data:
                    condition = {
                        'field': form_data[field_key],
                        'operator': form_data[operator_key],
                        'value': form_data.get(value_key, '')
                    }
                    conditions.append(condition)
        
        # Get logical operator
        logical_operator = request.form.get('edit_logical_operator', request.form.get('logical_operator', 'AND'))
        
        # Create rule pattern as JSON for multiple conditions
        rule_pattern = {
            'conditions': conditions,
            'logical_operator': logical_operator
        }
        
        # For backward compatibility, set rule_type based on first condition
        rule_type = conditions[0]['field'] if conditions else 'custom'
        
        rule = SecurityRule(
            name=request.form['name'],
            description=request.form.get('description', ''),
            rule_type=rule_type,
            pattern=json.dumps(rule_pattern),
            action=request.form.get('action', 'flag'),
            severity=request.form.get('severity', 'medium')
        )
        
        db.session.add(rule)
        db.session.commit()
        flash('Security rule added successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding rule: {str(e)}', 'error')
        logging.error(f"Error adding security rule: {str(e)}")
    
    return redirect(url_for('rules_engine'))

@app.route('/api/rules/<int:rule_id>', methods=['GET'])
def get_security_rule_api(rule_id):
    """API endpoint to get rule data for editing"""
    rule = SecurityRule.query.get_or_404(rule_id)
    
    import json
    try:
        rule_config = json.loads(rule.pattern)
        conditions = rule_config.get('conditions', [])
        logical_operator = rule_config.get('logical_operator', 'AND')
    except (json.JSONDecodeError, TypeError):
        # Legacy rule - convert to new format
        conditions = [{
            'field': rule.rule_type,
            'operator': 'contains',
            'value': rule.pattern
        }]
        logical_operator = 'AND'
    
    return jsonify({
        'id': rule.id,
        'name': rule.name,
        'description': rule.description,
        'action': rule.action,
        'severity': rule.severity,
        'conditions': conditions,
        'logical_operator': logical_operator
    })

@app.route('/api/rules/<int:rule_id>', methods=['PUT'])
def update_security_rule_api(rule_id):
    """API endpoint to update rule via JSON"""
    rule = SecurityRule.query.get_or_404(rule_id)
    
    try:
        import json
        data = request.get_json()
        
        conditions = data.get('conditions', [])
        logical_operator = data.get('logical_operator', 'AND')
        
        # Create rule pattern as JSON for multiple conditions
        rule_pattern = {
            'conditions': conditions,
            'logical_operator': logical_operator
        }
        
        # Update rule
        rule.name = data['name']
        rule.description = data.get('description', '')
        rule.rule_type = conditions[0]['field'] if conditions else rule.rule_type
        rule.pattern = json.dumps(rule_pattern)
        rule.action = data.get('action', 'flag')
        rule.severity = data.get('severity', 'medium')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Rule updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating security rule: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/rules-engine/edit/<int:rule_id>', methods=['GET', 'POST'])
def edit_security_rule(rule_id):
    """Edit existing security rule"""
    rule = SecurityRule.query.get_or_404(rule_id)
    
    if request.method == 'POST':
        import json
        
        try:
            # Extract conditions from form data
            conditions = []
            form_data = request.form.to_dict()
            
            # Parse conditions from form
            for key in form_data:
                if key.startswith('conditions[') and key.endswith('][field]'):
                    index = key.split('[')[1].split(']')[0]
                    field_key = f'conditions[{index}][field]'
                    operator_key = f'conditions[{index}][operator]'
                    value_key = f'conditions[{index}][value]'
                    
                    if field_key in form_data and operator_key in form_data:
                        condition = {
                            'field': form_data[field_key],
                            'operator': form_data[operator_key],
                            'value': form_data.get(value_key, '')
                        }
                        conditions.append(condition)
            
            # Get logical operator
            logical_operator = request.form.get('logical_operator', 'AND')
            
            # Create rule pattern as JSON for multiple conditions
            rule_pattern = {
                'conditions': conditions,
                'logical_operator': logical_operator
            }
            
            # Update rule
            rule.name = request.form['name']
            rule.description = request.form.get('description', '')
            rule.rule_type = conditions[0]['field'] if conditions else rule.rule_type
            rule.pattern = json.dumps(rule_pattern)
            rule.action = request.form.get('action', 'flag')
            rule.severity = request.form.get('severity', 'medium')
            
            db.session.commit()
            flash('Security rule updated successfully', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating rule: {str(e)}', 'error')
            logging.error(f"Error updating security rule: {str(e)}")
        
        return redirect(url_for('rules_engine'))
    
    # GET request - show edit form
    import json
    try:
        rule_config = json.loads(rule.pattern)
        conditions = rule_config.get('conditions', [])
        logical_operator = rule_config.get('logical_operator', 'AND')
    except (json.JSONDecodeError, TypeError):
        # Legacy rule - convert to new format
        conditions = [{
            'field': rule.rule_type,
            'operator': 'contains',
            'value': rule.pattern
        }]
        logical_operator = 'AND'
    
    return jsonify({
        'id': rule.id,
        'name': rule.name,
        'description': rule.description,
        'action': rule.action,
        'severity': rule.severity,
        'conditions': conditions,
        'logical_operator': logical_operator
    })

@app.route('/rules-engine/toggle/<int:rule_id>', methods=['POST'])
def toggle_security_rule(rule_id):
    """Toggle security rule active status"""
    rule = SecurityRule.query.get_or_404(rule_id)
    
    try:
        rule.active = not rule.active
        db.session.commit()
        
        status = 'activated' if rule.active else 'deactivated'
        flash(f'Security rule {status} successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error toggling rule: {str(e)}', 'error')
    
    return redirect(url_for('rules_engine'))

@app.route('/whitelist-domains')
def whitelist_domains():
    """Whitelist domains management"""
    domains = WhitelistDomain.query.filter_by(active=True).all()
    return render_template('whitelist_domains.html', domains=domains)

@app.route('/whitelist-domains/add', methods=['POST'])
def add_whitelist_domain():
    """Add new whitelist domain"""
    domain = WhitelistDomain(
        domain=request.form['domain'].lower(),
        description=request.form.get('description', '')
    )
    
    try:
        db.session.add(domain)
        db.session.commit()
        flash('Domain added to whitelist', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding domain: {str(e)}', 'error')
    
    return redirect(url_for('whitelist_domains'))

@app.route('/whitelist-senders')
def whitelist_senders():
    """Whitelist senders management"""
    senders = WhitelistSender.query.filter_by(active=True).all()
    return render_template('whitelist_senders.html', senders=senders)

@app.route('/whitelist-senders/add', methods=['POST'])
def add_whitelist_sender():
    """Add new whitelist sender"""
    sender = WhitelistSender(
        email=request.form['email'].lower(),
        description=request.form.get('description', '')
    )
    
    try:
        db.session.add(sender)
        db.session.commit()
        flash('Sender added to whitelist', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding sender: {str(e)}', 'error')
    
    return redirect(url_for('whitelist_senders'))

@app.route('/wordlist-management')
def wordlist_management():
    """Risk keywords management"""
    keywords = RiskKeyword.query.filter_by(active=True).all()
    return render_template('wordlist_management.html', keywords=keywords)

@app.route('/wordlist-management/add', methods=['POST'])
def add_risk_keyword():
    """Add new risk keyword"""
    keyword = RiskKeyword(
        keyword=request.form['keyword'].lower(),
        category=request.form['category'],
        weight=float(request.form.get('weight', 1.0))
    )
    
    try:
        db.session.add(keyword)
        db.session.commit()
        flash('Risk keyword added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding keyword: {str(e)}', 'error')
    
    return redirect(url_for('wordlist_management'))

@app.route('/admin')
def admin():
    """Admin panel"""
    return render_template('admin.html')

@app.route('/admin/populate-sample-data', methods=['POST'])
def populate_sample_data():
    """Populate database with sample security rules and keywords"""
    try:
        # Add sample security rules
        sample_rules = [
            {
                'name': 'External sender with executable attachment',
                'description': 'Detects emails from external senders with executable attachments',
                'rule_type': 'attachment',
                'pattern': json.dumps({
                    'conditions': [
                        {'field': 'attachments', 'operator': 'contains', 'value': '.exe'},
                        {'field': 'sender', 'operator': 'not_contains', 'value': '@company.com'}
                    ],
                    'logical_operator': 'AND'
                }),
                'action': 'quarantine',
                'severity': 'high'
            },
            {
                'name': 'Leaver sending emails',
                'description': 'Detects emails from users marked as leavers',
                'rule_type': 'leaver',
                'pattern': json.dumps({
                    'conditions': [
                        {'field': 'leaver', 'operator': 'equals', 'value': 'yes'}
                    ],
                    'logical_operator': 'AND'
                }),
                'action': 'flag',
                'severity': 'critical'
            },
            {
                'name': 'Urgent phishing keywords',
                'description': 'Detects phishing attempts with urgent language',
                'rule_type': 'subject',
                'pattern': json.dumps({
                    'conditions': [
                        {'field': 'subject', 'operator': 'contains', 'value': 'urgent'},
                        {'field': 'subject', 'operator': 'contains', 'value': 'verify'}
                    ],
                    'logical_operator': 'OR'
                }),
                'action': 'flag',
                'severity': 'medium'
            }
        ]
        
        for rule_data in sample_rules:
            existing_rule = SecurityRule.query.filter_by(name=rule_data['name']).first()
            if not existing_rule:
                rule = SecurityRule(**rule_data)
                db.session.add(rule)
        
        # Add sample risk keywords
        sample_keywords = [
            {'keyword': 'urgent', 'category': 'phishing', 'weight': 2.0},
            {'keyword': 'verify account', 'category': 'phishing', 'weight': 3.0},
            {'keyword': 'bitcoin', 'category': 'financial', 'weight': 2.5},
            {'keyword': 'wire transfer', 'category': 'financial', 'weight': 3.0},
            {'keyword': 'click here', 'category': 'phishing', 'weight': 1.5},
            {'keyword': 'suspended', 'category': 'phishing', 'weight': 2.0},
            {'keyword': 'confidential', 'category': 'data_exfiltration', 'weight': 1.0}
        ]
        
        for keyword_data in sample_keywords:
            existing_keyword = RiskKeyword.query.filter_by(keyword=keyword_data['keyword']).first()
            if not existing_keyword:
                keyword = RiskKeyword(**keyword_data)
                db.session.add(keyword)
        
        # Add sample whitelist domains
        sample_domains = [
            {'domain': 'microsoft.com', 'description': 'Microsoft Corporation'},
            {'domain': 'google.com', 'description': 'Google Services'},
            {'domain': 'company.com', 'description': 'Internal company domain'}
        ]
        
        for domain_data in sample_domains:
            existing_domain = WhitelistDomain.query.filter_by(domain=domain_data['domain']).first()
            if not existing_domain:
                domain = WhitelistDomain(**domain_data)
                db.session.add(domain)
        
        db.session.commit()
        flash('Sample data populated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error populating sample data: {str(e)}', 'error')
        logging.error(f"Error populating sample data: {str(e)}")
    
    return redirect(url_for('admin'))

@app.route('/admin/clear-database', methods=['POST'])
def clear_database():
    """Clear all data from database tables"""
    try:
        # Clear all tables in reverse order to handle foreign key constraints
        db.session.query(ProcessingLog).delete()
        db.session.query(Case).delete()
        db.session.query(RecipientRecord).delete()
        db.session.query(EmailRecord).delete()
        db.session.query(SecurityRule).delete()
        db.session.query(RiskKeyword).delete()
        db.session.query(ExclusionRule).delete()
        db.session.query(WhitelistDomain).delete()
        db.session.query(WhitelistSender).delete()
        db.session.query(SenderMetadata).delete()
        
        db.session.commit()
        flash('Database cleared successfully! All data has been removed.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error clearing database: {str(e)}', 'error')
        logging.error(f"Error clearing database: {str(e)}")
    
    return redirect(url_for('admin'))

@app.route('/sender-metadata')
def sender_metadata():
    """Sender metadata management"""
    page = request.args.get('page', 1, type=int)
    senders = SenderMetadata.query.order_by(SenderMetadata.last_email_sent.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('sender_metadata.html', senders=senders)

@app.route('/sender-metadata/add', methods=['POST'])
def add_sender_metadata():
    """Add or update sender metadata"""
    email = request.form['email'].lower()
    
    # Check if sender already exists
    sender = SenderMetadata.query.filter_by(email=email).first()
    
    if not sender:
        # Extract domain from email
        domain = email.split('@')[1] if '@' in email else ''
        
        sender = SenderMetadata(
            email=email,
            email_domain=domain
        )
        db.session.add(sender)
    
    # Update attributes
    sender.leaver = request.form.get('leaver', '')
    sender.termination = request.form.get('termination', '')
    sender.account_type = request.form.get('account_type', '')
    sender.bunit = request.form.get('bunit', '')
    sender.department = request.form.get('department', '')
    sender.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        flash('Sender metadata updated successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating sender metadata: {str(e)}', 'error')
    
    return redirect(url_for('sender_metadata'))

@app.route('/audit')
def audit():
    """Audit dashboard"""
    logs = ProcessingLog.query.order_by(ProcessingLog.created_at.desc()).limit(100).all()
    return render_template('audit.html', logs=logs)

@app.route('/debug/data-counts')
def debug_data_counts():
    """Debug endpoint to check actual data counts"""
    email_count = EmailRecord.query.count()
    recipient_count = RecipientRecord.query.count()
    sender_count = SenderMetadata.query.count()
    case_count = Case.query.count()
    
    # Get recent emails
    recent_emails = EmailRecord.query.order_by(EmailRecord.processed_at.desc()).limit(5).all()
    
    return jsonify({
        'email_count': email_count,
        'recipient_count': recipient_count,
        'sender_count': sender_count,
        'case_count': case_count,
        'recent_emails': [
            {
                'id': e.id,
                'sender': e.sender,
                'subject': e.subject,
                'processed_at': e.processed_at.isoformat() if e.processed_at else None
            } for e in recent_emails
        ]
    })

@app.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint for dashboard charts data"""
    # Get case distribution by severity with proper ordering
    severity_order = ['low', 'medium', 'high', 'critical']
    severity_counts = db.session.query(
        Case.severity, func.count(Case.id)
    ).group_by(Case.severity).all()
    
    # Create severity data with all categories
    severity_dict = {s[0]: s[1] for s in severity_counts}
    severity_data = {
        'labels': ['Low', 'Medium', 'High', 'Critical'],
        'data': [severity_dict.get(level, 0) for level in severity_order]
    }
    
    # Get processing statistics for the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats = db.session.query(
        func.date(EmailRecord.processed_at),
        func.count(EmailRecord.id)
    ).filter(EmailRecord.processed_at >= seven_days_ago).group_by(
        func.date(EmailRecord.processed_at)
    ).order_by(func.date(EmailRecord.processed_at)).all()
    
    # Create complete 7-day dataset
    date_dict = {str(d[0]) if d[0] else '': d[1] for d in daily_stats}
    daily_labels = []
    daily_values = []
    
    for i in range(6, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_labels.append(date)
        daily_values.append(date_dict.get(date, 0))
    
    daily_data = {
        'labels': daily_labels,
        'data': daily_values
    }
    
    # Get case counts for the same period
    daily_case_stats = db.session.query(
        func.date(Case.created_at),
        func.count(Case.id)
    ).filter(Case.created_at >= seven_days_ago).group_by(
        func.date(Case.created_at)
    ).order_by(func.date(Case.created_at)).all()
    
    case_dict = {str(d[0]) if d[0] else '': d[1] for d in daily_case_stats}
    case_values = []
    
    for i in range(6, -1, -1):
        date = (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d')
        case_values.append(case_dict.get(date, 0))
    
    # Get sender domain distribution
    domain_stats = db.session.query(
        SenderMetadata.email_domain,
        func.count(SenderMetadata.id)
    ).group_by(SenderMetadata.email_domain).order_by(
        func.count(SenderMetadata.id).desc()
    ).limit(10).all()
    
    sender_domain_data = {
        'labels': [d[0] if d[0] else 'Unknown' for d in domain_stats],
        'data': [d[1] for d in domain_stats]
    }
    
    # Get leaver vs active sender distribution
    leaver_stats = db.session.query(
        db.case(
            [(SenderMetadata.leaver == 'yes', 'Leavers')],
            else_='Active'
        ).label('status'),
        func.count(SenderMetadata.id)
    ).group_by(
        db.case(
            [(SenderMetadata.leaver == 'yes', 'Leavers')],
            else_='Active'
        )
    ).all()
    
    leaver_dict = {s[0]: s[1] for s in leaver_stats}
    sender_status_data = {
        'labels': ['Active', 'Leavers'],
        'data': [leaver_dict.get('Active', 0), leaver_dict.get('Leavers', 0)]
    }
    
    # Get risk distribution
    risk_ranges = [
        ('Low (0-2)', 0, 2),
        ('Medium (2-5)', 2, 5),
        ('High (5-8)', 5, 8),
        ('Critical (8+)', 8, 999)
    ]
    
    risk_data = {'labels': [], 'data': []}
    for label, min_score, max_score in risk_ranges:
        if max_score == 999:
            count = RecipientRecord.query.filter(RecipientRecord.risk_score >= min_score).count()
        else:
            count = RecipientRecord.query.filter(
                RecipientRecord.risk_score >= min_score,
                RecipientRecord.risk_score < max_score
            ).count()
        risk_data['labels'].append(label)
        risk_data['data'].append(count)
    
    return jsonify({
        'severity_distribution': severity_data,
        'daily_processing': daily_data,
        'daily_cases': {
            'labels': daily_labels,
            'data': case_values
        },
        'sender_domains': sender_domain_data,
        'sender_status': sender_status_data,
        'risk_distribution': risk_data
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
