import pandas as pd
import logging
from datetime import datetime
from sqlalchemy import func
from flask import session
from app import db
from models import *
from ml_engines import BasicMLEngine, AdvancedMLEngine
from utils import clean_csv_value, is_empty_value, safe_split_csv
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

            # Validate required columns for new CSV format
            required_columns = [
                '_time', 'sender', 'subject', 'attachments', 'recipients', 
                'time_month', 'leaver', 'termination_date', 'bunit', 'department',
                'user_response', 'final_outcome', 'policy_name', 'justifications'
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            # Convert timestamp
            df['_time'] = pd.to_datetime(df['_time'], errors='coerce')

            # Fill NaN values and convert "-" to empty strings (treat as null)
            df = df.fillna('')
            
            # Replace all "-" values with empty strings to treat as null
            df = df.replace('-', '')

            self.logger.info(f"Loaded {len(df)} records from CSV with new format")
            return df

        except Exception as e:
            self.logger.error(f"Stage 1 failed: {str(e)}")
            raise

    def _stage_2_email_normalization(self, df):
        """Stage 2: Split emails with multiple recipients, attachments, and policy names"""
        self.logger.info("Stage 2: Email Normalization")

        normalized_rows = []

        for _, row in df.iterrows():
            # Split recipients (comma-separated), treating '-' as null
            recipients = safe_split_csv(row['recipients'])
            if not recipients:
                recipients = ['']

            # Split attachments (comma-separated), treating '-' as null
            attachments_list = safe_split_csv(row['attachments'])
            attachments_combined = ', '.join(attachments_list) if attachments_list else ''

            # Split policy names (comma-separated), treating '-' as null
            policy_names = safe_split_csv(row['policy_name'])
            policy_names_combined = ', '.join(policy_names) if policy_names else ''

            # Create normalized record for each recipient
            for recipient in recipients:
                normalized_row = row.copy()
                normalized_row['recipients'] = recipient
                normalized_row['attachments'] = attachments_combined
                normalized_row['policy_name'] = policy_names_combined

                # Extract domain from recipient email
                if '@' in recipient:
                    domain = recipient.split('@')[1].lower()
                    normalized_row['recipients_email_domain'] = domain
                else:
                    normalized_row['recipients_email_domain'] = ''

                normalized_rows.append(normalized_row)

        normalized_df = pd.DataFrame(normalized_rows)
        self.logger.info(f"Normalized to {len(normalized_df)} recipient records")

        return normalized_df

    def _process_recipient(self, email_record, recipient_data):
        """Process individual recipient through stages 3-10"""
        recipient_record = RecipientRecord(
            email_id=email_record.id,
            recipient=clean_csv_value(recipient_data.get('recipients', '')),
            recipient_email_domain=clean_csv_value(recipient_data.get('recipients_email_domain', '')),
            leaver=clean_csv_value(recipient_data.get('leaver', '')),
            termination_date=clean_csv_value(recipient_data.get('termination_date', '')),
            bunit=clean_csv_value(recipient_data.get('bunit', '')),
            department=clean_csv_value(recipient_data.get('department', '')),
            user_response=clean_csv_value(recipient_data.get('user_response', '')),
            final_outcome=clean_csv_value(recipient_data.get('final_outcome', '')),
            policy_name=clean_csv_value(recipient_data.get('policy_name', '')),
            justifications=clean_csv_value(recipient_data.get('justifications', ''))
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
        # Cache exclusion rules data to avoid repeated database queries and session issues
        if not hasattr(self, '_cached_exclusion_rules_data'):
            exclusion_rules = ExclusionRule.query.filter_by(active=True).all()
            self._cached_exclusion_rules_data = []
            for rule in exclusion_rules:
                self._cached_exclusion_rules_data.append({
                    'id': rule.id,
                    'name': rule.name,
                    'rule_type': rule.rule_type,
                    'pattern': rule.pattern,
                    'active': rule.active
                })

        for rule_data in self._cached_exclusion_rules_data:
            if self._match_rule_data(rule_data, recipient_record, email_record):
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
            recipient_record.whitelist_reason = f"Sender '{email_record.sender}' is in whitelist"
            return

        # Check domain whitelist
        sender_domain = email_record.sender.split('@')[1].lower() if '@' in email_record.sender else ''
        if sender_domain in self._cached_whitelist_domains:
            recipient_record.whitelisted = True
            recipient_record.whitelist_reason = f"Domain '{sender_domain}' is in whitelist"
            return

    def _stage_5_security_rules(self, recipient_record, email_record):
        """Stage 5: Apply security rules and calculate score"""
        # Cache security rules data to avoid repeated database queries and session issues
        if not hasattr(self, '_cached_security_rules_data'):
            security_rules = SecurityRule.query.filter_by(active=True).all()
            self._cached_security_rules_data = []
            for rule in security_rules:
                self._cached_security_rules_data.append({
                    'id': rule.id,
                    'name': rule.name,
                    'rule_type': rule.rule_type,
                    'pattern': rule.pattern,
                    'action': rule.action,
                    'severity': rule.severity,
                    'active': rule.active
                })

        security_score = 0.0
        matched_rules = []

        for rule_data in self._cached_security_rules_data:
            if self._match_rule_data(rule_data, recipient_record, email_record):
                # Add score based on severity
                severity_weights = {'low': 1.0, 'medium': 2.0, 'high': 3.0, 'critical': 5.0}
                security_score += severity_weights.get(rule_data['severity'], 1.0)
                
                # Track matched rule
                matched_rules.append({
                    'name': rule_data['name'],
                    'severity': rule_data['severity'],
                    'score_added': severity_weights.get(rule_data['severity'], 1.0)
                })

        recipient_record.security_score = security_score
        recipient_record.matched_security_rules = matched_rules

    def _stage_6_risk_keywords(self, recipient_record, email_record):
        """Stage 6: Detect risk keywords and calculate risk score"""
        # Cache risk keywords data to avoid repeated database queries and session issues
        if not hasattr(self, '_cached_risk_keywords_data'):
            risk_keywords = RiskKeyword.query.filter_by(active=True).all()
            self._cached_risk_keywords_data = []
            for keyword in risk_keywords:
                self._cached_risk_keywords_data.append({
                    'keyword': keyword.keyword,
                    'category': keyword.category,
                    'weight': keyword.weight,
                    'active': keyword.active
                })

        risk_score = 0.0
        matched_keywords = []

        text_to_analyze = f"{email_record.subject} {email_record.attachments} {recipient_record.wordlist_subject} {recipient_record.wordlist_attachment}".lower()

        for keyword_data in self._cached_risk_keywords_data:
            if keyword_data['keyword'].lower() in text_to_analyze:
                risk_score += keyword_data['weight']
                matched_keywords.append({
                    'keyword': keyword_data['keyword'],
                    'category': keyword_data['category'],
                    'weight': keyword_data['weight']
                })

        recipient_record.risk_score = risk_score
        recipient_record.matched_risk_keywords = matched_keywords

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

            # Update sender metadata
            self._update_sender_metadata(email_record.sender)

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
            sender=clean_csv_value(first_recipient_data.get('sender', '')),
            subject=clean_csv_value(first_recipient_data.get('subject', '')),
            attachments=clean_csv_value(first_recipient_data.get('attachments', '')),
            original_recipients=clean_csv_value(first_recipient_data.get('recipients', '')),
            time_month=clean_csv_value(first_recipient_data.get('time_month', '')),
            pipeline_status='processing'
        )

    def _match_rule(self, rule, recipient_record, email_record):
        """Check if a rule matches the given email/recipient"""
        try:
            import json

            # Try to parse pattern as JSON (new multi-condition format)
            try:
                rule_config = json.loads(rule.pattern)
                conditions = rule_config.get('conditions', [])
                logical_operator = rule_config.get('logical_operator', 'AND')

                if conditions:
                    return self._evaluate_conditions(conditions, logical_operator, recipient_record, email_record)
            except json.JSONDecodeError:
                # Fall back to legacy single pattern matching
                pass

            # Legacy single pattern matching
            pattern = rule.pattern.lower()

            if rule.rule_type == 'sender':
                return pattern in email_record.sender.lower()
            elif rule.rule_type == 'subject':
                return pattern in (email_record.subject or '').lower()
            elif rule.rule_type == 'attachment':
                return pattern in (email_record.attachments or '').lower()
            elif rule.rule_type == 'recipient':
                return pattern in recipient_record.recipient.lower()
            elif rule.rule_type == 'domain':
                return pattern in (recipient_record.recipient_email_domain or '').lower()

        except Exception as e:
            self.logger.error(f"Error matching rule {rule.name}: {str(e)}")

        return False

    def _match_rule_data(self, rule_data, recipient_record, email_record):
        """Check if rule matches current email/recipient"""
        try:
            import json
            import re

            pattern = rule_data['pattern']

            # Check if pattern is JSON (new multi-condition rules)
            try:
                rule_config = json.loads(pattern)
                return self._match_complex_rule(rule_config, recipient_record, email_record)
            except (json.JSONDecodeError, TypeError):
                # Legacy simple pattern matching
                rule_type = rule_data['rule_type']
                return self._match_simple_rule(rule_type, pattern, recipient_record, email_record)

        except Exception as e:
            self.logger.error(f"Error matching rule: {str(e)}")
            return False

    def _match_complex_rule(self, rule_config, recipient_record, email_record):
        """Match complex multi-condition rules"""
        conditions = rule_config.get('conditions', [])
        logical_operator = rule_config.get('logical_operator', 'AND')

        if not conditions:
            return False

        results = []
        for condition in conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value', '')

            field_value = self._get_field_value(field, recipient_record, email_record)
            match_result = self._evaluate_condition(field_value, operator, value)
            results.append(match_result)

        # Apply logical operator
        if logical_operator == 'OR':
            return any(results)
        else:  # AND
            return all(results)

    def _match_simple_rule(self, rule_type, pattern, recipient_record, email_record):
        """Match legacy simple pattern rules"""
        if rule_type == 'sender':
            return self._match_pattern(pattern, email_record.sender)
        elif rule_type == 'subject':
            return self._match_pattern(pattern, email_record.subject or '')
        elif rule_type == 'attachment':
            return self._match_pattern(pattern, email_record.attachments or '')
        elif rule_type == 'leaver':
            # Check if sender has leaver status matching the pattern
            sender_metadata = self._get_sender_metadata(email_record.sender)
            if sender_metadata:
                leaver_value = (sender_metadata.leaver or '').lower().strip()
                pattern_value = pattern.lower().strip()
                if pattern_value == 'yes':
                    return leaver_value == 'yes'
                elif pattern_value == 'no':
                    return leaver_value != 'yes' and leaver_value != ''
                else:
                    return pattern_value in leaver_value
            return False
        elif rule_type == 'termination':
            termination_value = (recipient_record.termination or '').lower().strip()
            pattern_value = pattern.lower().strip()
            return pattern_value in termination_value or bool(termination_value)
        elif rule_type == 'recipients':
            return len(email_record.recipients) > 1

        return False

    def _get_field_value(self, field, recipient_record, email_record):
        """Get field value for condition evaluation"""
        if field == 'sender':
            return email_record.sender or ''
        elif field == 'subject':
            return email_record.subject or ''
        elif field == 'attachments':
            return email_record.attachments or ''
        elif field == 'recipients':
            return str(len(email_record.recipients))
        elif field == 'leaver':
            # Check sender metadata for leaver status
            sender_metadata = self._get_sender_metadata(email_record.sender)
            if sender_metadata:
                return sender_metadata.leaver or ''
            return recipient_record.leaver or ''
        elif field == 'termination':
            # Check sender metadata for termination status  
            sender_metadata = self._get_sender_metadata(email_record.sender)
            if sender_metadata:
                return sender_metadata.termination or ''
            return recipient_record.termination or ''
        elif field == 'account_type':
            return recipient_record.account_type or ''
        elif field == 'bunit':
            return recipient_record.bunit or ''
        elif field == 'department':
            return recipient_record.department or ''
        elif field == 'timestamp':
            return email_record.timestamp.isoformat() if email_record.timestamp else ''

        return ''

    def _evaluate_condition(self, field_value, operator, value):
        """Evaluate a single condition"""
        import re

        field_value = str(field_value).lower()
        value = str(value).lower()

        if operator == 'contains':
            return value in field_value
        elif operator == 'equals':
            return field_value == value
        elif operator == 'starts_with':
            return field_value.startswith(value)
        elif operator == 'ends_with':
            return field_value.endswith(value)
        elif operator == 'regex':
            try:
                return bool(re.search(value, field_value, re.IGNORECASE))
            except re.error:
                return False
        elif operator == 'not_contains':
            return value not in field_value
        elif operator == 'not_equals':
            return field_value != value
        elif operator == 'is_empty':
            return field_value == ''
        elif operator == 'is_not_empty':
            return field_value != ''

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

    def _match_pattern(self, pattern, text):
        """Match pattern against text"""
        if not pattern or not text:
            return False
        return pattern.lower() in text.lower()

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

    def _get_sender_metadata(self, sender_email):
        """Get or create sender metadata"""
        if not hasattr(self, '_sender_metadata_cache'):
            self._sender_metadata_cache = {}
        
        sender_email_lower = sender_email.lower()
        
        if sender_email_lower not in self._sender_metadata_cache:
            from models import SenderMetadata
            metadata = SenderMetadata.query.filter_by(email=sender_email_lower).first()
            self._sender_metadata_cache[sender_email_lower] = metadata
        
        return self._sender_metadata_cache[sender_email_lower]

    def _update_sender_metadata(self, sender_email):
        """Update sender metadata with email activity"""
        from models import SenderMetadata
        from sqlalchemy import func
        
        sender_email_lower = sender_email.lower()
        metadata = SenderMetadata.query.filter_by(email=sender_email_lower).first()
        
        if not metadata:
            # Extract domain from sender email
            domain = sender_email.split('@')[1].lower() if '@' in sender_email else ''
            
            metadata = SenderMetadata(
                email=sender_email_lower,
                email_domain=domain,
                last_email_sent=datetime.utcnow(),
                total_emails_sent=1
            )
            db.session.add(metadata)
        else:
            metadata.last_email_sent = datetime.utcnow()
            metadata.total_emails_sent = (metadata.total_emails_sent or 0) + 1
            metadata.updated_at = datetime.utcnow()
        
        return metadata

    def _log_processing(self, email_id, stage, status, message, processing_time=None):
        """Log processing step - using Python logging instead of database for performance"""
        self.logger.info(f"Email {email_id} - {stage}: {status} - {message}")