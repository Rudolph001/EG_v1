import os
import csv
import json
import pandas as pd
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from sqlalchemy import func, or_, and_, exists
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
    
    # Also count unique senders from recipient records marked as leavers
    leaver_recipients_senders = db.session.query(func.count(func.distinct(EmailRecord.sender))).join(
        RecipientRecord, EmailRecord.id == RecipientRecord.email_id
    ).filter(RecipientRecord.leaver == 'yes').scalar() or 0
    
    # Use the higher count (recipients data is usually more complete)
    if leaver_recipients_senders > leaver_senders:
        leaver_senders = leaver_recipients_senders

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
    """Display all processed emails (only emails in 'processed' state)"""
    page = request.args.get('page', 1, type=int)

    # Only show emails that are in 'processed' state (or have no state set)
    # Also eagerly load recipients to access rule matching data
    emails = db.session.query(EmailRecord).outerjoin(
        EmailState, EmailRecord.id == EmailState.email_id
    ).filter(
        or_(
            EmailState.current_state == 'processed',
            EmailState.current_state == None
        )
    ).options(
        db.joinedload(EmailRecord.recipients)
    ).order_by(EmailRecord.processed_at.desc()).paginate(
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

@app.route('/flagged-events')
def flagged_events():
    """Display flagged sender events"""
    page = request.args.get('page', 1, type=int)
    
    # Get emails from flagged senders (leavers, high-risk senders, etc.)
    # Use LEFT JOIN to include emails even without sender metadata
    flagged_emails = db.session.query(EmailRecord, SenderMetadata).outerjoin(
        SenderMetadata, EmailRecord.sender == SenderMetadata.email
    ).filter(
        db.or_(
            SenderMetadata.leaver == 'yes',  # Leaver senders from metadata
            db.exists().where(
                db.and_(
                    RecipientRecord.email_id == EmailRecord.id,
                    RecipientRecord.leaver == 'yes'  # Leaver recipients
                )
            ),
            db.exists().where(
                db.and_(
                    RecipientRecord.email_id == EmailRecord.id,
                    RecipientRecord.flagged == True
                )
            )  # Emails with flagged recipients
        )
    ).order_by(EmailRecord.processed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get summary statistics
    total_flagged = db.session.query(EmailRecord).outerjoin(
        SenderMetadata, EmailRecord.sender == SenderMetadata.email
    ).filter(
        db.or_(
            SenderMetadata.leaver == 'yes',
            db.exists().where(
                db.and_(
                    RecipientRecord.email_id == EmailRecord.id,
                    RecipientRecord.leaver == 'yes'
                )
            ),
            db.exists().where(
                db.and_(
                    RecipientRecord.email_id == EmailRecord.id,
                    RecipientRecord.flagged == True
                )
            )
        )
    ).count()
    
    # Count high-risk flagged events (leaver senders from metadata or recipients)
    high_risk_metadata = db.session.query(EmailRecord).join(
        SenderMetadata, EmailRecord.sender == SenderMetadata.email
    ).filter(SenderMetadata.leaver == 'yes').count()
    
    high_risk_recipients = db.session.query(EmailRecord).join(
        RecipientRecord, EmailRecord.id == RecipientRecord.email_id
    ).filter(RecipientRecord.leaver == 'yes').count()
    
    high_risk_count = max(high_risk_metadata, high_risk_recipients)
    
    stats = {
        'total_flagged': total_flagged,
        'high_risk_count': high_risk_count,
        'open_cases': Case.query.filter_by(status='open').count()
    }
    
    return render_template('flagged_events.html', 
                         flagged_emails=flagged_emails, 
                         stats=stats)

@app.route('/reports')
def reports():
    """Reports dashboard with real data"""
    try:
        # Get threat trends data for the last 4 weeks
        four_weeks_ago = datetime.utcnow() - timedelta(weeks=4)
        
        # Weekly threat detection (cases created)
        weekly_threats = []
        weekly_false_positives = []
        week_labels = []
        
        for i in range(4, 0, -1):
            week_start = datetime.utcnow() - timedelta(weeks=i)
            week_end = datetime.utcnow() - timedelta(weeks=i-1)
            week_labels.append(f'Week {5-i}')
            
            # Count actual cases/threats for this week
            threats = Case.query.filter(
                Case.created_at >= week_start,
                Case.created_at < week_end
            ).count()
            
            # Count resolved cases as potential false positives
            false_pos = Case.query.filter(
                Case.created_at >= week_start,
                Case.created_at < week_end,
                Case.status == 'resolved'
            ).count()
            
            weekly_threats.append(threats)
            weekly_false_positives.append(false_pos)
        
        # Risk distribution from actual recipient data
        risk_low = RecipientRecord.query.filter(RecipientRecord.risk_score < 3.0).count()
        risk_medium = RecipientRecord.query.filter(
            RecipientRecord.risk_score >= 3.0,
            RecipientRecord.risk_score < 7.0
        ).count()
        risk_high = RecipientRecord.query.filter(
            RecipientRecord.risk_score >= 7.0,
            RecipientRecord.risk_score < 9.0
        ).count()
        risk_critical = RecipientRecord.query.filter(RecipientRecord.risk_score >= 9.0).count()
        
        # Recent report activity (using actual processing data)
        recent_activity = []
        recent_emails = EmailRecord.query.order_by(EmailRecord.processed_at.desc()).limit(3).all()
        
        for email in recent_emails:
            recent_activity.append({
                'report': f'Analysis Report - {email.processed_at.strftime("%Y-%m-%d")}',
                'generated': email.processed_at.strftime("%Y-%m-%d %H:%M"),
                'status': 'Complete',
                'email_id': email.id
            })
        
        # Summary statistics
        total_emails = EmailRecord.query.count()
        total_cases = Case.query.count()
        high_risk_cases = Case.query.filter(Case.severity.in_(['high', 'critical'])).count()
        
        report_data = {
            'threat_trends': {
                'labels': week_labels,
                'threats': weekly_threats,
                'false_positives': weekly_false_positives
            },
            'risk_distribution': {
                'low': risk_low,
                'medium': risk_medium,
                'high': risk_high,
                'critical': risk_critical
            },
            'recent_activity': recent_activity,
            'summary': {
                'total_emails': total_emails,
                'total_cases': total_cases,
                'high_risk_cases': high_risk_cases
            }
        }
        
        return render_template('reports.html', report_data=report_data)
        
    except Exception as e:
        logging.error(f"Error loading reports data: {str(e)}")
        # Fallback to empty data structure
        report_data = {
            'threat_trends': {
                'labels': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
                'threats': [0, 0, 0, 0],
                'false_positives': [0, 0, 0, 0]
            },
            'risk_distribution': {
                'low': 0, 'medium': 0, 'high': 0, 'critical': 0
            },
            'recent_activity': [],
            'summary': {
                'total_emails': 0,
                'total_cases': 0,
                'high_risk_cases': 0
            }
        }
        flash('Reports data temporarily unavailable. Please check database connection.', 'warning')
        return render_template('reports.html', report_data=report_data)

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

# Email State Management Routes
@app.route('/move-to-flagged/<int:email_id>', methods=['POST'])
def move_to_flagged(email_id):
    """Move email to flagged events dashboard"""
    try:
        email = EmailRecord.query.get_or_404(email_id)
        
        # Get or create email state
        email_state = EmailState.query.filter_by(email_id=email_id).first()
        if not email_state:
            email_state = EmailState(email_id=email_id, current_state='processed')
            db.session.add(email_state)
        
        # Update state
        email_state.previous_state = email_state.current_state
        email_state.current_state = 'flagged'
        email_state.moved_by = 'User'  # You can implement user authentication later
        email_state.moved_at = datetime.utcnow()
        
        # Create flagged event record
        flagged_event = FlaggedEvent(
            email_id=email_id,
            flagged_reason='Manually flagged by user',
            severity='medium',
            flagged_by='User'
        )
        db.session.add(flagged_event)
        
        db.session.commit()
        flash(f'Email "{email.subject[:50]}..." moved to Flagged Events dashboard.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error moving email: {str(e)}', 'error')
    
    return redirect(url_for('emails'))

@app.route('/move-to-escalation/<int:email_id>', methods=['POST'])
def move_to_escalation(email_id):
    """Move email to escalation dashboard"""
    try:
        email = EmailRecord.query.get_or_404(email_id)
        
        # Get or create email state
        email_state = EmailState.query.filter_by(email_id=email_id).first()
        if not email_state:
            email_state = EmailState(email_id=email_id, current_state='processed')
            db.session.add(email_state)
        
        # Update state
        email_state.previous_state = email_state.current_state
        email_state.current_state = 'escalated'
        email_state.moved_by = 'User'
        email_state.moved_at = datetime.utcnow()
        
        # Create escalated event record
        escalated_event = EscalatedEvent(
            email_id=email_id,
            escalation_reason='Manually escalated by user',
            priority='medium',
            escalated_to='Security Team',
            escalated_by='User'
        )
        db.session.add(escalated_event)
        
        db.session.commit()
        flash(f'Email "{email.subject[:50]}..." moved to Escalation dashboard.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error moving email: {str(e)}', 'error')
    
    return redirect(url_for('emails'))

@app.route('/move-to-cleared/<int:email_id>', methods=['POST'])
def move_to_cleared(email_id):
    """Move email to cleared cases dashboard"""
    try:
        email = EmailRecord.query.get_or_404(email_id)
        
        # Get or create email state
        email_state = EmailState.query.filter_by(email_id=email_id).first()
        if not email_state:
            email_state = EmailState(email_id=email_id, current_state='processed')
            db.session.add(email_state)
        
        # Update state
        email_state.previous_state = email_state.current_state
        email_state.current_state = 'cleared'
        email_state.moved_by = 'User'
        email_state.moved_at = datetime.utcnow()
        
        # Create cleared event record
        cleared_event = ClearedEvent(
            email_id=email_id,
            cleared_reason='Manually cleared by user',
            cleared_by='User'
        )
        db.session.add(cleared_event)
        
        db.session.commit()
        flash(f'Email "{email.subject[:50]}..." moved to Cleared Cases dashboard.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error moving email: {str(e)}', 'error')
    
    return redirect(url_for('emails'))

@app.route('/move-to-processed/<int:email_id>', methods=['POST'])
def move_to_processed(email_id):
    """Move email back to All Processed Emails"""
    try:
        email = EmailRecord.query.get_or_404(email_id)
        
        # Get email state
        email_state = EmailState.query.filter_by(email_id=email_id).first()
        if email_state:
            # Update state
            email_state.previous_state = email_state.current_state
            email_state.current_state = 'processed'
            email_state.moved_by = 'User'
            email_state.moved_at = datetime.utcnow()
            
            # Mark related events as resolved
            if email_state.previous_state == 'flagged':
                flagged_event = FlaggedEvent.query.filter_by(email_id=email_id, resolved=False).first()
                if flagged_event:
                    flagged_event.resolved = True
                    flagged_event.resolved_at = datetime.utcnow()
                    flagged_event.resolved_by = 'User'
            
            elif email_state.previous_state == 'escalated':
                escalated_event = EscalatedEvent.query.filter_by(email_id=email_id, resolved=False).first()
                if escalated_event:
                    escalated_event.resolved = True
                    escalated_event.resolved_at = datetime.utcnow()
                    escalated_event.resolved_by = 'User'
            
            db.session.commit()
            flash(f'Email "{email.subject[:50]}..." moved back to All Processed Emails.', 'success')
        else:
            flash('Email state not found.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error moving email: {str(e)}', 'error')
    
    return redirect(request.referrer or url_for('emails'))

# Dashboard Routes for New Event Types
@app.route('/escalation-dashboard')
def escalation_dashboard():
    """Escalation dashboard showing escalated emails"""
    page = request.args.get('page', 1, type=int)
    
    # Get escalated emails
    escalated_emails = db.session.query(EmailRecord, SenderMetadata).join(
        EmailState, EmailRecord.id == EmailState.email_id
    ).outerjoin(
        SenderMetadata, EmailRecord.sender == SenderMetadata.email
    ).filter(
        EmailState.current_state == 'escalated'
    ).order_by(EmailRecord.processed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('escalation_dashboard.html', 
                         escalated_emails=escalated_emails,
                         title='Escalation Dashboard')

@app.route('/api/reports-data')
def reports_data_api():
    """API endpoint for reports dashboard data"""
    try:
        # Get comprehensive reports data
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        # Email processing trends (last 30 days)
        daily_processing = db.session.query(
            func.date(EmailRecord.processed_at),
            func.count(EmailRecord.id)
        ).filter(
            EmailRecord.processed_at >= thirty_days_ago
        ).group_by(func.date(EmailRecord.processed_at)).all()
        
        # Case creation trends
        daily_cases = db.session.query(
            func.date(Case.created_at),
            func.count(Case.id)
        ).filter(
            Case.created_at >= thirty_days_ago
        ).group_by(func.date(Case.created_at)).all()
        
        # Security rule effectiveness
        security_rules = SecurityRule.query.filter_by(active=True).all()
        rule_effectiveness = []
        
        for rule in security_rules:
            # Count cases generated by this rule type
            cases_generated = Case.query.filter(
                Case.description.contains(rule.name)
            ).count()
            rule_effectiveness.append({
                'rule_name': rule.name,
                'cases_generated': cases_generated,
                'severity': rule.severity
            })
        
        # Top risk senders
        top_risk_senders = db.session.query(
            EmailRecord.sender,
            func.avg(RecipientRecord.risk_score).label('avg_risk'),
            func.count(EmailRecord.id).label('email_count')
        ).join(
            RecipientRecord, EmailRecord.id == RecipientRecord.email_id
        ).group_by(EmailRecord.sender).having(
            func.avg(RecipientRecord.risk_score) > 5.0
        ).order_by(func.avg(RecipientRecord.risk_score).desc()).limit(10).all()
        
        # ML model performance
        basic_ml_flagged = RecipientRecord.query.filter(RecipientRecord.ml_score >= 5.0).count()
        advanced_ml_flagged = RecipientRecord.query.filter(RecipientRecord.advanced_ml_score >= 5.0).count()
        
        return jsonify({
            'daily_processing': [{'date': str(d[0]), 'count': d[1]} for d in daily_processing],
            'daily_cases': [{'date': str(d[0]), 'count': d[1]} for d in daily_cases],
            'rule_effectiveness': rule_effectiveness,
            'top_risk_senders': [
                {
                    'sender': sender[0],
                    'avg_risk': float(sender[1]) if sender[1] else 0,
                    'email_count': sender[2]
                } for sender in top_risk_senders
            ],
            'ml_performance': {
                'basic_ml_flagged': basic_ml_flagged,
                'advanced_ml_flagged': advanced_ml_flagged
            }
        })
        
    except Exception as e:
        logging.error(f"Error loading reports API data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/cleared-cases-dashboard') 
def cleared_cases_dashboard():
    """Cleared cases dashboard showing cleared emails"""
    page = request.args.get('page', 1, type=int)
    
    # Get cleared emails
    cleared_emails = db.session.query(EmailRecord, SenderMetadata).join(
        EmailState, EmailRecord.id == EmailState.email_id
    ).outerjoin(
        SenderMetadata, EmailRecord.sender == SenderMetadata.email
    ).filter(
        EmailState.current_state == 'cleared'
    ).order_by(EmailRecord.processed_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('cleared_cases_dashboard.html',
                         cleared_emails=cleared_emails,
                         title='Cleared Cases Dashboard')

@app.route('/ml-analytics')
def ml_analytics():
    """ML Analytics Dashboard showing model performance and results"""
    
    # Get basic ML model statistics
    try:
        from ml_engines import BasicMLEngine, AdvancedMLEngine
        basic_ml = BasicMLEngine()
        advanced_ml = AdvancedMLEngine()
        
        # Get emails with ML scores
        emails_with_scores = db.session.query(
            EmailRecord.id,
            EmailRecord.sender,
            EmailRecord.subject,
            EmailRecord.processed_at,
            func.avg(RecipientRecord.ml_score).label('avg_basic_ml'),
            func.avg(RecipientRecord.advanced_ml_score).label('avg_advanced_ml'),
            func.avg(RecipientRecord.risk_score).label('avg_risk_score'),
            func.count(RecipientRecord.id).label('recipient_count')
        ).join(
            RecipientRecord, EmailRecord.id == RecipientRecord.email_id
        ).group_by(
            EmailRecord.id, EmailRecord.sender, EmailRecord.subject, EmailRecord.processed_at
        ).order_by(EmailRecord.processed_at.desc()).limit(100).all()
        
        # Calculate model performance metrics
        total_emails = EmailRecord.query.count()
        flagged_by_basic_ml = db.session.query(RecipientRecord).filter(
            RecipientRecord.ml_score >= 5.0
        ).count()
        flagged_by_advanced_ml = db.session.query(RecipientRecord).filter(
            RecipientRecord.advanced_ml_score >= 5.0
        ).count()
        
        # Score distribution for charts
        basic_ml_scores = db.session.query(RecipientRecord.ml_score).filter(
            RecipientRecord.ml_score.isnot(None)
        ).all()
        advanced_ml_scores = db.session.query(RecipientRecord.advanced_ml_score).filter(
            RecipientRecord.advanced_ml_score.isnot(None)
        ).all()
        
        # Model accuracy metrics (simplified)
        high_risk_threshold = 7.0
        medium_risk_threshold = 5.0
        
        basic_ml_high_risk = len([s[0] for s in basic_ml_scores if s[0] >= high_risk_threshold])
        basic_ml_medium_risk = len([s[0] for s in basic_ml_scores if medium_risk_threshold <= s[0] < high_risk_threshold])
        basic_ml_low_risk = len([s[0] for s in basic_ml_scores if s[0] < medium_risk_threshold])
        
        advanced_ml_high_risk = len([s[0] for s in advanced_ml_scores if s[0] >= high_risk_threshold])
        advanced_ml_medium_risk = len([s[0] for s in advanced_ml_scores if medium_risk_threshold <= s[0] < high_risk_threshold])
        advanced_ml_low_risk = len([s[0] for s in advanced_ml_scores if s[0] < medium_risk_threshold])
        
        stats = {
            'total_emails': total_emails,
            'total_recipients': len(basic_ml_scores),
            'basic_ml_flagged': flagged_by_basic_ml,
            'advanced_ml_flagged': flagged_by_advanced_ml,
            'basic_ml_model_status': 'Fitted' if basic_ml.is_fitted else 'Not Fitted',
            'advanced_ml_model_status': 'Fitted' if advanced_ml.is_fitted else 'Not Fitted',
            'basic_ml_distribution': {
                'high_risk': basic_ml_high_risk,
                'medium_risk': basic_ml_medium_risk,
                'low_risk': basic_ml_low_risk
            },
            'advanced_ml_distribution': {
                'high_risk': advanced_ml_high_risk,
                'medium_risk': advanced_ml_medium_risk,
                'low_risk': advanced_ml_low_risk
            }
        }
        
        return render_template('ml_analytics.html', 
                             emails=emails_with_scores,
                             stats=stats,
                             title='ML Analytics Dashboard')
        
    except Exception as e:
        flash(f'Error loading ML analytics: {str(e)}', 'error')
        return render_template('ml_analytics.html', 
                             emails=[],
                             stats={},
                             title='ML Analytics Dashboard')

@app.route('/ml-model-config')
def ml_model_config():
    """ML Model Configuration page"""
    try:
        from ml_engines import BasicMLEngine, AdvancedMLEngine
        basic_ml = BasicMLEngine()
        advanced_ml = AdvancedMLEngine()
        
        # Get current model parameters
        basic_config = {
            'contamination': getattr(basic_ml.isolation_forest, 'contamination', 0.1),
            'random_state': getattr(basic_ml.isolation_forest, 'random_state', 42),
            'is_fitted': basic_ml.is_fitted
        }
        
        advanced_config = {
            'threshold': getattr(advanced_ml, 'threshold', 0.1),
            'is_fitted': advanced_ml.is_fitted,
            'model_type': 'Random Forest + Network Analysis'
        }
        
        return render_template('ml_model_config.html',
                             basic_config=basic_config,
                             advanced_config=advanced_config,
                             title='ML Model Configuration')
        
    except Exception as e:
        flash(f'Error loading model configuration: {str(e)}', 'error')
        return redirect(url_for('ml_analytics'))

@app.route('/retrain-basic-ml', methods=['POST'])
def retrain_basic_ml():
    """Retrain the basic ML model"""
    try:
        contamination = float(request.form.get('contamination', 0.1))
        random_state = int(request.form.get('random_state', 42))
        
        from ml_engines import BasicMLEngine
        basic_ml = BasicMLEngine()
        
        # Update parameters
        basic_ml.isolation_forest.contamination = contamination
        basic_ml.isolation_forest.random_state = random_state
        
        # Retrain with recent data
        recent_recipients = RecipientRecord.query.limit(1000).all()
        if recent_recipients:
            for recipient in recent_recipients:
                features = {
                    'subject_length': len(recipient.email.subject or ''),
                    'has_attachments': 1 if recipient.email.attachments else 0,
                    'sender_domain_length': len(recipient.email.sender.split('@')[1]) if '@' in recipient.email.sender else 0,
                    'is_external': 1 if '@' in recipient.email.sender and not recipient.email.sender.endswith('.internal') else 0,
                    'is_leaver': 1 if recipient.leaver == 'yes' else 0,
                    'has_termination': 1 if recipient.termination else 0,
                    'security_score': recipient.security_score or 0,
                    'risk_score': recipient.risk_score or 0
                }
                # Update ML score
                new_score = basic_ml.predict_risk(features)
                recipient.ml_score = new_score
            
            db.session.commit()
            flash('Basic ML model retrained successfully!', 'success')
        else:
            flash('No data available for retraining.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error retraining basic ML model: {str(e)}', 'error')
    
    return redirect(url_for('ml_model_config'))

@app.route('/retrain-advanced-ml', methods=['POST'])
def retrain_advanced_ml():
    """Retrain the advanced ML model"""
    try:
        threshold = float(request.form.get('threshold', 0.1))
        
        from ml_engines import AdvancedMLEngine
        advanced_ml = AdvancedMLEngine()
        advanced_ml.threshold = threshold
        
        # Retrain with recent data
        recent_recipients = RecipientRecord.query.limit(1000).all()
        if recent_recipients:
            for recipient in recent_recipients:
                # Update advanced ML score
                # Create features for advanced ML
                features = {
                    'subject_length': len(recipient.email.subject or ''),
                    'has_attachments': 1 if recipient.email.attachments else 0,
                    'sender_domain_length': len(recipient.email.sender.split('@')[1]) if '@' in recipient.email.sender else 0,
                    'is_external': 1 if '@' in recipient.email.sender and not recipient.email.sender.endswith('.internal') else 0,
                    'is_leaver': 1 if recipient.leaver == 'yes' else 0,
                    'has_termination': 1 if recipient.termination else 0,
                    'security_score': recipient.security_score or 0,
                    'risk_score': recipient.risk_score or 0,
                    'hour_of_day': recipient.email.timestamp.hour if recipient.email.timestamp else 12,
                    'day_of_week': recipient.email.timestamp.weekday() if recipient.email.timestamp else 1,
                    'subject_exclamation_count': (recipient.email.subject or '').count('!'),
                    'subject_question_count': (recipient.email.subject or '').count('?'),
                    'subject_caps_ratio': len([c for c in (recipient.email.subject or '') if c.isupper()]) / max(len(recipient.email.subject or ''), 1)
                }
                new_score = advanced_ml.predict_risk(features)
                recipient.advanced_ml_score = new_score
            
            db.session.commit()
            flash('Advanced ML model retrained successfully!', 'success')
        else:
            flash('No data available for retraining.', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error retraining advanced ML model: {str(e)}', 'error')
    
    return redirect(url_for('ml_model_config'))

@app.route('/update-recipient-scores/<int:recipient_id>', methods=['POST'])
def update_recipient_scores(recipient_id):
    """Update recipient scores manually"""
    try:
        recipient = RecipientRecord.query.get_or_404(recipient_id)
        
        # Update scores from form
        recipient.security_score = float(request.form.get('security_score', 0))
        recipient.risk_score = float(request.form.get('risk_score', 0))
        recipient.ml_score = float(request.form.get('ml_score', 0))
        recipient.advanced_ml_score = float(request.form.get('advanced_ml_score', 0))
        recipient.flagged = 'flagged' in request.form
        
        # Recalculate combined risk level
        combined_score = (
            recipient.security_score * 0.3 +
            recipient.risk_score * 0.2 +
            recipient.ml_score * 0.25 +
            recipient.advanced_ml_score * 0.25
        )
        
        # Update flagged status based on combined score if not manually set
        if combined_score > 5.0:
            recipient.flagged = True
        
        db.session.commit()
        flash(f'Scores updated successfully for {recipient.recipient}!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating scores: {str(e)}', 'error')
    
    return redirect(url_for('email_detail', email_id=recipient.email_id))

@app.route('/rescore-email/<int:email_id>', methods=['POST'])
def rescore_email(email_id):
    """Re-run the scoring pipeline for a specific email"""
    try:
        from pipeline import EmailProcessingPipeline
        
        email = EmailRecord.query.get_or_404(email_id)
        pipeline = EmailProcessingPipeline()
        
        # Re-score all recipients for this email
        for recipient in email.recipients:
            # Re-run security rules
            pipeline._stage_5_security_rules(recipient, email)
            # Re-run risk keywords
            pipeline._stage_6_risk_keywords(recipient, email)
            # Re-run ML analysis
            pipeline._stage_8_ml_analysis(recipient, email)
            pipeline._stage_9_advanced_ml(recipient, email)
            # Re-run case generation
            pipeline._stage_10_case_generation(recipient, email)
        
        db.session.commit()
        flash('Email rescored successfully! All recipients have been re-evaluated.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error rescoring email: {str(e)}', 'error')
    
    return redirect(url_for('email_detail', email_id=email_id))

@app.route('/scoring-help')
def scoring_help():
    """Help page explaining the scoring system"""
    # Get current configuration stats
    security_rules_count = SecurityRule.query.filter_by(active=True).count()
    risk_keywords_count = RiskKeyword.query.filter_by(active=True).count()
    whitelist_senders_count = WhitelistSender.query.filter_by(active=True).count()
    whitelist_domains_count = WhitelistDomain.query.filter_by(active=True).count()
    
    # Get some example rules/keywords for display
    example_security_rules = SecurityRule.query.filter_by(active=True).limit(3).all()
    example_risk_keywords = RiskKeyword.query.filter_by(active=True).limit(5).all()
    
    stats = {
        'security_rules_count': security_rules_count,
        'risk_keywords_count': risk_keywords_count,
        'whitelist_senders_count': whitelist_senders_count,
        'whitelist_domains_count': whitelist_domains_count,
        'example_security_rules': example_security_rules,
        'example_risk_keywords': example_risk_keywords
    }
    
    return render_template('scoring_help.html', stats=stats, title='Scoring System Help')

@app.route('/rule-analysis')
def rule_analysis():
    """Analysis of rule matching and whitelist effectiveness"""
    try:
        # Get rule matching statistics
        security_rule_stats = db.session.query(
            SecurityRule.name,
            SecurityRule.severity,
            func.count(RecipientRecord.id).label('match_count')
        ).join(
            RecipientRecord, 
            func.json_extract(RecipientRecord.matched_security_rules, '$[*].name').contains(SecurityRule.name)
        ).filter(SecurityRule.active == True).group_by(
            SecurityRule.name, SecurityRule.severity
        ).all()
        
        # Get whitelist statistics
        whitelisted_count = RecipientRecord.query.filter_by(whitelisted=True).count()
        total_recipients = RecipientRecord.query.count()
        
        whitelist_reasons = db.session.query(
            RecipientRecord.whitelist_reason,
            func.count(RecipientRecord.id).label('count')
        ).filter(
            RecipientRecord.whitelisted == True,
            RecipientRecord.whitelist_reason.isnot(None)
        ).group_by(RecipientRecord.whitelist_reason).all()
        
        # Get recent rule matches
        recent_matches = db.session.query(EmailRecord, RecipientRecord).join(
            RecipientRecord, EmailRecord.id == RecipientRecord.email_id
        ).filter(
            or_(
                RecipientRecord.matched_security_rules.isnot(None),
                RecipientRecord.matched_risk_keywords.isnot(None),
                RecipientRecord.whitelisted == True
            )
        ).order_by(EmailRecord.processed_at.desc()).limit(50).all()
        
        stats = {
            'security_rule_stats': security_rule_stats,
            'whitelisted_count': whitelisted_count,
            'total_recipients': total_recipients,
            'whitelist_percentage': (whitelisted_count / max(total_recipients, 1)) * 100,
            'whitelist_reasons': whitelist_reasons,
            'recent_matches': recent_matches
        }
        
        return render_template('rule_analysis.html', stats=stats)
        
    except Exception as e:
        logging.error(f"Error in rule analysis: {str(e)}")
        flash('Error loading rule analysis data', 'error')
        return redirect(url_for('dashboard'))

@app.route('/bulk-action', methods=['POST'])
def bulk_action():
    """Handle bulk actions on multiple emails"""
    try:
        email_ids = request.form.getlist('email_ids')
        action = request.form.get('action')
        
        if not email_ids or not action:
            return jsonify({'success': False, 'error': 'Missing email IDs or action'}), 400
        
        # Convert string IDs to integers
        try:
            email_ids = [int(email_id) for email_id in email_ids]
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid email ID format'}), 400
        
        # Validate action
        valid_actions = ['flagged', 'escalated', 'cleared']
        if action not in valid_actions:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
        
        success_count = 0
        errors = []
        
        for email_id in email_ids:
            try:
                email = EmailRecord.query.get(email_id)
                if not email:
                    errors.append(f'Email {email_id} not found')
                    continue
                
                # Get or create email state
                email_state = EmailState.query.filter_by(email_id=email_id).first()
                if not email_state:
                    email_state = EmailState(email_id=email_id, current_state='processed')
                    db.session.add(email_state)
                
                # Update state based on action
                email_state.previous_state = email_state.current_state
                email_state.current_state = action
                email_state.moved_by = 'User'  # You can implement user authentication later
                email_state.moved_at = datetime.utcnow()
                
                # Create appropriate event record
                if action == 'flagged':
                    flagged_event = FlaggedEvent(
                        email_id=email_id,
                        flagged_reason='Bulk action by user',
                        severity='medium',
                        flagged_by='User'
                    )
                    db.session.add(flagged_event)
                    
                elif action == 'escalated':
                    escalated_event = EscalatedEvent(
                        email_id=email_id,
                        escalation_reason='Bulk escalation by user',
                        priority='medium',
                        escalated_to='Security Team',
                        escalated_by='User'
                    )
                    db.session.add(escalated_event)
                    
                elif action == 'cleared':
                    cleared_event = ClearedEvent(
                        email_id=email_id,
                        cleared_reason='Bulk clearing by user',
                        cleared_by='User'
                    )
                    db.session.add(cleared_event)
                
                success_count += 1
                
            except Exception as e:
                errors.append(f'Error processing email {email_id}: {str(e)}')
                logging.error(f"Error in bulk action for email {email_id}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        
        # Prepare response
        response = {
            'success': True,
            'count': success_count,
            'total_requested': len(email_ids)
        }
        
        if errors:
            response['errors'] = errors
            response['partial_success'] = True
        
        return jsonify(response)
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in bulk action: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
            (SenderMetadata.leaver == 'yes', 'Leavers'),
            else_='Active'
        ).label('status'),
        func.count(SenderMetadata.id)
    ).group_by(
        db.case(
            (SenderMetadata.leaver == 'yes', 'Leavers'),
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