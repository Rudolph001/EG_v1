import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import func
from flask import session
from app import db
from models import *
from ml_engines import BasicMLEngine, AdvancedMLEngine
import re

class EmailProcessingPipeline:
    """11-stage email processing pipeline"""
    
    def __init__(self):
        self.basic_ml = BasicMLEngine()
        self.advanced_ml = AdvancedMLEngine()
        self.logger = logging.getLogger(__name__)
    
    def process_csv(self, filepath):
        """Process uploaded CSV file through the 11-stage pipeline"""
        self.logger.info(f"Starting CSV processing: {filepath}")
        
        try:
            # Stage 1: Data Ingestion
            df = self._stage_1_data_ingestion(filepath)
            
            # Stage 2: Email Normalization
            normalized_data = self._stage_2_email_normalization(df)
            
            results = {
                'total_emails': 0,
                'total_recipients': 0,
                'flagged': 0,
                'cases_generated': 0
            }
            
            # Group by original email for processing
            email_groups = {}
            for _, row in normalized_data.iterrows():
                email_key = (row['_time'], row['sender'], row['subject'])
                if email_key not in email_groups:
                    email_groups[email_key] = []
                email_groups[email_key].append(row)
            
            # Process emails in batches to avoid memory issues
            batch_size = 10
            email_items = list(email_groups.items())
            
            for i in range(0, len(email_items), batch_size):
                batch = email_items[i:i + batch_size]
                
                for email_key, recipients in batch:
                    email_record = self._create_email_record(recipients[0])
                    results['total_emails'] += 1
                    
                    processed_recipients = []
                    
                    for recipient_data in recipients:
                        recipient_record = self._process_recipient(email_record, recipient_data)
                        if recipient_record:
                            processed_recipients.append(recipient_record)
                            results['total_recipients'] += 1
                            
                            if recipient_record.flagged:
                                results['flagged'] += 1
                            if recipient_record.case_generated:
                                results['cases_generated'] += 1
                    
                    # Stage 11: Database Write
                    self._stage_11_database_write(email_record, processed_recipients)
                
                # Commit batch and clear session to prevent memory buildup
                db.session.commit()
                db.session.close()
                
                self.logger.info(f"Processed batch {i//batch_size + 1} of {(len(email_items) + batch_size - 1)//batch_size}")
            
            self.logger.info(f"CSV processing completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in CSV processing: {str(e)}")
            raise
    
    def _stage_1_data_ingestion(self, filepath):
        """Stage 1: Load CSV, parse fields, and validate data"""
        self.logger.info("Stage 1: Data Ingestion")
        
        try:
            df = pd.read_csv(filepath)
            
            # Validate required columns
            required_columns = [
                '_time', 'sender', 'subject', 'attachments', 'recipients',
                'recipients_email_domain', 'leaver', 'termination', 'account_type',
                'wordlist_attachment', 'wordlist_subject', 'bunit', 'department',
                'user_response', 'final_outcome', 'policy_name', 'justifications'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Convert timestamp
            df['_time'] = pd.to_datetime(df['_time'], errors='coerce')
            
            # Fill NaN values
            df = df.fillna('')
            
            self.logger.info(f"Loaded {len(df)} records from CSV")
            return df
            
        except Exception as e:
            self.logger.error(f"Stage 1 failed: {str(e)}")
            raise
    
    def _stage_2_email_normalization(self, df):
        """Stage 2: Split emails with multiple recipients/attachments"""
        self.logger.info("Stage 2: Email Normalization")
        
        normalized_rows = []
        
        for _, row in df.iterrows():
            # Split recipients if multiple
            recipients = str(row['recipients']).split(';') if row['recipients'] else ['']
            recipients = [r.strip() for r in recipients if r.strip()]
            
            if not recipients:
                recipients = ['']
            
            # Create normalized record for each recipient
            for recipient in recipients:
                normalized_row = row.copy()
                normalized_row['recipients'] = recipient
                
                # Extract domain from recipient email
                if '@' in recipient:
                    domain = recipient.split('@')[1].lower()
                    normalized_row['recipients_email_domain'] = domain
                
                normalized_rows.append(normalized_row)
        
        normalized_df = pd.DataFrame(normalized_rows)
        self.logger.info(f"Normalized to {len(normalized_df)} recipient records")
        
        return normalized_df
    
    def _process_recipient(self, email_record, recipient_data):
        """Process individual recipient through stages 3-10"""
        recipient_record = RecipientRecord(
            email_id=email_record.id,
            recipient=recipient_data.get('recipients', ''),
            recipient_email_domain=recipient_data.get('recipients_email_domain', ''),
            leaver=recipient_data.get('leaver', ''),
            termination=recipient_data.get('termination', ''),
            account_type=recipient_data.get('account_type', ''),
            bunit=recipient_data.get('bunit', ''),
            department=recipient_data.get('department', ''),
            wordlist_attachment=recipient_data.get('wordlist_attachment', ''),
            wordlist_subject=recipient_data.get('wordlist_subject', ''),
            user_response=recipient_data.get('user_response', ''),
            final_outcome=recipient_data.get('final_outcome', ''),
            policy_name=recipient_data.get('policy_name', ''),
            justifications=recipient_data.get('justifications', '')
        )
        
        # Stage 3: Exclusion Rules
        if self._stage_3_exclusion_rules(recipient_record, email_record):
            return None
        
        # Stage 4: Whitelist Filtering
        self._stage_4_whitelist_filtering(recipient_record, email_record)
        
        # Stage 5: Security Rules
        self._stage_5_security_rules(recipient_record, email_record)
        
        # Stage 6: Risk Keywords
        self._stage_6_risk_keywords(recipient_record, email_record)
        
        # Stage 7: Exclusion Keywords
        self._stage_7_exclusion_keywords(recipient_record, email_record)
        
        # Stage 8: ML Analysis
        self._stage_8_ml_analysis(recipient_record, email_record)
        
        # Stage 9: Advanced ML
        self._stage_9_advanced_ml(recipient_record, email_record)
        
        # Stage 10: Case Generation
        self._stage_10_case_generation(recipient_record, email_record)
        
        return recipient_record
    
    def _stage_3_exclusion_rules(self, recipient_record, email_record):
        """Stage 3: Filter out emails based on exclusion criteria"""
        # Cache exclusion rules to avoid repeated database queries
        if not hasattr(self, '_cached_exclusion_rules'):
            self._cached_exclusion_rules = ExclusionRule.query.filter_by(active=True).all()
        
        for rule in self._cached_exclusion_rules:
            if self._match_rule(rule, recipient_record, email_record):
                recipient_record.excluded = True
                return True
        
        return False
    
    def _stage_4_whitelist_filtering(self, recipient_record, email_record):
        """Stage 4: Check against whitelisted domains and senders"""
        # Cache whitelist data to avoid repeated database queries
        if not hasattr(self, '_cached_whitelist_senders'):
            self._cached_whitelist_senders = {s.email.lower() for s in WhitelistSender.query.filter_by(active=True).all()}
        if not hasattr(self, '_cached_whitelist_domains'):
            self._cached_whitelist_domains = {d.domain.lower() for d in WhitelistDomain.query.filter_by(active=True).all()}
        
        # Check sender whitelist
        if email_record.sender.lower() in self._cached_whitelist_senders:
            recipient_record.whitelisted = True
            return
        
        # Check domain whitelist
        sender_domain = email_record.sender.split('@')[1].lower() if '@' in email_record.sender else ''
        if sender_domain in self._cached_whitelist_domains:
            recipient_record.whitelisted = True
            return
    
    def _stage_5_security_rules(self, recipient_record, email_record):
        """Stage 5: Apply security rules and calculate score"""
        # Cache security rules to avoid repeated database queries
        if not hasattr(self, '_cached_security_rules'):
            self._cached_security_rules = SecurityRule.query.filter_by(active=True).all()
        
        security_score = 0.0
        
        for rule in self._cached_security_rules:
            if self._match_rule(rule, recipient_record, email_record):
                # Add score based on severity
                severity_weights = {'low': 1.0, 'medium': 2.0, 'high': 3.0, 'critical': 5.0}
                security_score += severity_weights.get(rule.severity, 1.0)
        
        recipient_record.security_score = security_score
    
    def _stage_6_risk_keywords(self, recipient_record, email_record):
        """Stage 6: Detect risk keywords and calculate risk score"""
        # Cache risk keywords to avoid repeated database queries
        if not hasattr(self, '_cached_risk_keywords'):
            self._cached_risk_keywords = RiskKeyword.query.filter_by(active=True).all()
        
        risk_score = 0.0
        
        text_to_analyze = f"{email_record.subject} {email_record.attachments} {recipient_record.wordlist_subject} {recipient_record.wordlist_attachment}".lower()
        
        for keyword in self._cached_risk_keywords:
            if keyword.keyword.lower() in text_to_analyze:
                risk_score += keyword.weight
        
        recipient_record.risk_score = risk_score
    
    def _stage_7_exclusion_keywords(self, recipient_record, email_record):
        """Stage 7: Apply exclusion keywords to reduce false positives"""
        exclusion_keywords = ['automated', 'system notification', 'no-reply', 'unsubscribe']
        
        text_to_analyze = f"{email_record.subject} {email_record.sender}".lower()
        
        for keyword in exclusion_keywords:
            if keyword in text_to_analyze:
                # Reduce risk score for automated/system emails
                recipient_record.risk_score *= 0.5
                break
    
    def _stage_8_ml_analysis(self, recipient_record, email_record):
        """Stage 8: Basic ML risk scoring"""
        features = self._extract_features(recipient_record, email_record)
        ml_score = self.basic_ml.predict_risk(features)
        recipient_record.ml_score = ml_score
    
    def _stage_9_advanced_ml(self, recipient_record, email_record):
        """Stage 9: Advanced ML with network analysis"""
        features = self._extract_advanced_features(recipient_record, email_record)
        advanced_ml_score = self.advanced_ml.predict_risk(features)
        recipient_record.advanced_ml_score = advanced_ml_score
    
    def _stage_10_case_generation(self, recipient_record, email_record):
        """Stage 10: Generate cases for flagged events"""
        # Calculate combined risk score
        combined_score = (
            recipient_record.security_score * 0.3 +
            recipient_record.risk_score * 0.2 +
            recipient_record.ml_score * 0.25 +
            recipient_record.advanced_ml_score * 0.25
        )
        
        # Flag high-risk recipients
        if combined_score > 5.0 or recipient_record.security_score > 3.0:
            recipient_record.flagged = True
            
            # Generate case for high-risk scenarios
            if combined_score > 8.0:
                case = Case(
                    email_id=email_record.id,
                    case_type='high_risk_email',
                    severity=self._determine_severity(combined_score),
                    title=f'High-risk email detected: {email_record.subject[:100]}',
                    description=f'Email from {email_record.sender} to {recipient_record.recipient} flagged with combined risk score: {combined_score:.2f}',
                    risk_factors={
                        'security_score': recipient_record.security_score,
                        'risk_score': recipient_record.risk_score,
                        'ml_score': recipient_record.ml_score,
                        'advanced_ml_score': recipient_record.advanced_ml_score
                    }
                )
                
                db.session.add(case)
                recipient_record.case_generated = True
    
    def _stage_11_database_write(self, email_record, processed_recipients):
        """Stage 11: Save email record with all processed recipient data"""
        try:
            # First save the email record to get its ID
            db.session.add(email_record)
            db.session.flush()  # This assigns the ID without committing
            
            # Now set the email_id for all recipients and add them in batch
            for recipient in processed_recipients:
                recipient.email_id = email_record.id
            
            # Add all recipients at once
            db.session.add_all(processed_recipients)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Database write error: {str(e)}")
            raise
    
    def _create_email_record(self, first_recipient_data):
        """Create email record from first recipient data"""
        return EmailRecord(
            timestamp=first_recipient_data['_time'],
            sender=first_recipient_data.get('sender', ''),
            subject=first_recipient_data.get('subject', ''),
            attachments=first_recipient_data.get('attachments', ''),
            original_recipients=first_recipient_data.get('recipients', ''),
            pipeline_status='processing'
        )
    
    def _match_rule(self, rule, recipient_record, email_record):
        """Check if a rule matches the email/recipient"""
        pattern = rule.pattern.lower()
        
        if rule.rule_type == 'sender':
            return pattern in email_record.sender.lower()
        elif rule.rule_type == 'subject':
            return pattern in (email_record.subject or '').lower()
        elif rule.rule_type == 'recipient':
            return pattern in recipient_record.recipient.lower()
        elif rule.rule_type == 'domain':
            return pattern in (recipient_record.recipient_email_domain or '').lower()
        elif rule.rule_type == 'attachment':
            return pattern in (email_record.attachments or '').lower()
        
        return False
    
    def _extract_features(self, recipient_record, email_record):
        """Extract features for basic ML analysis"""
        features = {}
        
        # Email metadata features
        features['subject_length'] = len(email_record.subject or '')
        features['has_attachments'] = 1 if email_record.attachments else 0
        features['sender_domain_length'] = len(email_record.sender.split('@')[1]) if '@' in email_record.sender else 0
        
        # Recipient features
        features['is_external'] = 1 if recipient_record.recipient_email_domain else 0
        features['is_leaver'] = 1 if recipient_record.leaver == 'yes' else 0
        features['has_termination'] = 1 if recipient_record.termination else 0
        
        # Risk indicators
        features['security_score'] = recipient_record.security_score
        features['risk_score'] = recipient_record.risk_score
        
        return features
    
    def _extract_advanced_features(self, recipient_record, email_record):
        """Extract features for advanced ML analysis"""
        features = self._extract_features(recipient_record, email_record)
        
        # Add advanced features
        features['hour_of_day'] = email_record.timestamp.hour if email_record.timestamp else 12
        features['day_of_week'] = email_record.timestamp.weekday() if email_record.timestamp else 1
        
        # Text analysis features
        features['subject_exclamation_count'] = (email_record.subject or '').count('!')
        features['subject_question_count'] = (email_record.subject or '').count('?')
        features['subject_caps_ratio'] = sum(1 for c in (email_record.subject or '') if c.isupper()) / max(len(email_record.subject or ''), 1)
        
        return features
    
    def _determine_severity(self, combined_score):
        """Determine case severity based on combined risk score"""
        if combined_score >= 15.0:
            return 'critical'
        elif combined_score >= 10.0:
            return 'high'
        elif combined_score >= 5.0:
            return 'medium'
        else:
            return 'low'
    
    def _log_processing(self, email_id, stage, status, message, processing_time=None):
        """Log processing step - using Python logging instead of database for performance"""
        self.logger.info(f"Email {email_id} - {stage}: {status} - {message}")
