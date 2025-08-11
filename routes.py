import os
import csv
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
    # Get recent statistics
    total_emails = EmailRecord.query.count()
    total_cases = Case.query.count()
    open_cases = Case.query.filter_by(status='open').count()
    flagged_recipients = RecipientRecord.query.filter_by(flagged=True).count()
    
    # Get recent cases
    recent_cases = Case.query.order_by(Case.created_at.desc()).limit(5).all()
    
    # Get processing statistics for the last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_emails = EmailRecord.query.filter(EmailRecord.processed_at >= thirty_days_ago).all()
    
    # Calculate daily processing counts
    daily_counts = {}
    for email in recent_emails:
        date = email.processed_at.strftime('%Y-%m-%d')
        daily_counts[date] = daily_counts.get(date, 0) + 1
    
    stats = {
        'total_emails': total_emails,
        'total_cases': total_cases,
        'open_cases': open_cases,
        'flagged_recipients': flagged_recipients,
        'recent_cases': recent_cases,
        'daily_counts': daily_counts
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
    """Add new security rule"""
    rule = SecurityRule(
        name=request.form['name'],
        description=request.form.get('description', ''),
        rule_type=request.form['rule_type'],
        pattern=request.form['pattern'],
        action=request.form.get('action', 'flag'),
        severity=request.form.get('severity', 'medium')
    )
    
    try:
        db.session.add(rule)
        db.session.commit()
        flash('Security rule added successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding rule: {str(e)}', 'error')
    
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

@app.route('/audit')
def audit():
    """Audit dashboard"""
    logs = ProcessingLog.query.order_by(ProcessingLog.created_at.desc()).limit(100).all()
    return render_template('audit.html', logs=logs)

@app.route('/api/dashboard-data')
def dashboard_data():
    """API endpoint for dashboard charts data"""
    # Get case distribution by severity
    severity_counts = db.session.query(
        Case.severity, db.func.count(Case.id)
    ).group_by(Case.severity).all()
    
    # Get processing statistics for the last 7 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    daily_stats = db.session.query(
        db.func.date(EmailRecord.processed_at),
        db.func.count(EmailRecord.id)
    ).filter(EmailRecord.processed_at >= seven_days_ago).group_by(
        db.func.date(EmailRecord.processed_at)
    ).all()
    
    return jsonify({
        'severity_distribution': {
            'labels': [s[0] for s in severity_counts],
            'data': [s[1] for s in severity_counts]
        },
        'daily_processing': {
            'labels': [str(d[0]) for d in daily_stats],
            'data': [d[1] for d in daily_stats]
        }
    })

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
