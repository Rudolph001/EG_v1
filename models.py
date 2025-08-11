from app import db
from datetime import datetime
from sqlalchemy import JSON

class EmailRecord(db.Model):
    __tablename__ = 'email_records'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False)
    sender = db.Column(db.String(255), nullable=False)
    subject = db.Column(db.Text)
    attachments = db.Column(db.Text)
    original_recipients = db.Column(db.Text)  # Original recipients list
    
    # Processing metadata
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    pipeline_status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recipients = db.relationship('RecipientRecord', backref='email', lazy=True, cascade='all, delete-orphan')
    cases = db.relationship('Case', backref='email', lazy=True)
    sender_metadata = db.relationship('SenderMetadata', 
                                    primaryjoin='EmailRecord.sender == SenderMetadata.email',
                                    foreign_keys='SenderMetadata.email',
                                    uselist=False,
                                    lazy='select')

class RecipientRecord(db.Model):
    __tablename__ = 'recipient_records'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    
    # Recipient info
    recipient = db.Column(db.String(255), nullable=False)
    recipient_email_domain = db.Column(db.String(255))
    
    # User attributes
    leaver = db.Column(db.String(10))
    termination = db.Column(db.String(50))
    account_type = db.Column(db.String(50))
    bunit = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Analysis results
    wordlist_attachment = db.Column(db.Text)
    wordlist_subject = db.Column(db.Text)
    user_response = db.Column(db.String(50))
    final_outcome = db.Column(db.String(50))
    policy_name = db.Column(db.String(100))
    justifications = db.Column(db.Text)
    
    # Pipeline results
    excluded = db.Column(db.Boolean, default=False)
    whitelisted = db.Column(db.Boolean, default=False)
    security_score = db.Column(db.Float, default=0.0)
    risk_score = db.Column(db.Float, default=0.0)
    ml_score = db.Column(db.Float, default=0.0)
    advanced_ml_score = db.Column(db.Float, default=0.0)
    
    # Processing flags
    flagged = db.Column(db.Boolean, default=False)
    case_generated = db.Column(db.Boolean, default=False)
    
    # Rule matching results
    matched_security_rules = db.Column(JSON)  # List of matched security rule names
    matched_risk_keywords = db.Column(JSON)  # List of matched risk keywords
    whitelist_reason = db.Column(db.String(255))  # Why it was whitelisted
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Case(db.Model):
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    
    case_type = db.Column(db.String(50), nullable=False)  # 'threat', 'policy_violation', etc.
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    status = db.Column(db.String(20), default='open')  # open, investigating, resolved, closed
    
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Risk details
    risk_factors = db.Column(JSON)
    recommended_actions = db.Column(JSON)
    
    # Workflow
    assigned_to = db.Column(db.String(100))
    escalated = db.Column(db.Boolean, default=False)
    escalated_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

class WhitelistDomain(db.Model):
    __tablename__ = 'whitelist_domains'
    
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class WhitelistSender(db.Model):
    __tablename__ = 'whitelist_senders'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SecurityRule(db.Model):
    __tablename__ = 'security_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    rule_type = db.Column(db.String(50), nullable=False)  # 'sender', 'subject', 'attachment', etc.
    pattern = db.Column(db.String(500), nullable=False)
    action = db.Column(db.String(50), default='flag')  # flag, block, quarantine
    severity = db.Column(db.String(20), default='medium')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class RiskKeyword(db.Model):
    __tablename__ = 'risk_keywords'
    
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'financial', 'malware', 'phishing', etc.
    weight = db.Column(db.Float, default=1.0)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ExclusionRule(db.Model):
    __tablename__ = 'exclusion_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rule_type = db.Column(db.String(50), nullable=False)  # 'domain', 'sender', 'subject', etc.
    pattern = db.Column(db.String(500), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SenderMetadata(db.Model):
    __tablename__ = 'sender_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    email_domain = db.Column(db.String(255))
    
    # User attributes
    leaver = db.Column(db.String(10))
    termination = db.Column(db.String(50))
    account_type = db.Column(db.String(50))
    bunit = db.Column(db.String(100))
    department = db.Column(db.String(100))
    
    # Status tracking
    active = db.Column(db.Boolean, default=True)
    last_email_sent = db.Column(db.DateTime)
    total_emails_sent = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProcessingLog(db.Model):
    __tablename__ = 'processing_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    stage = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error, warning
    message = db.Column(db.Text)
    processing_time = db.Column(db.Float)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class EmailState(db.Model):
    __tablename__ = 'email_states'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False, unique=True)
    current_state = db.Column(db.String(50), nullable=False, default='processed')  # processed, flagged, escalated, cleared
    previous_state = db.Column(db.String(50))  # for undo functionality
    notes = db.Column(db.Text)
    moved_by = db.Column(db.String(100))  # user who moved the email
    moved_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    email = db.relationship('EmailRecord', backref='state', lazy=True)

class FlaggedEvent(db.Model):
    __tablename__ = 'flagged_events'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    flagged_reason = db.Column(db.Text)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    flagged_by = db.Column(db.String(100))
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    email = db.relationship('EmailRecord', backref='flagged_event', lazy=True)

class EscalatedEvent(db.Model):
    __tablename__ = 'escalated_events'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    escalation_reason = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    escalated_to = db.Column(db.String(100))
    escalated_by = db.Column(db.String(100))
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    email = db.relationship('EmailRecord', backref='escalated_event', lazy=True)

class ClearedEvent(db.Model):
    __tablename__ = 'cleared_events'
    
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('email_records.id'), nullable=False)
    cleared_reason = db.Column(db.Text)
    cleared_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    email = db.relationship('EmailRecord', backref='cleared_event', lazy=True)
