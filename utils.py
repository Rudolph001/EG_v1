import re
import hashlib
from datetime import datetime
import logging

def validate_email(email):
    """Validate email address format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def extract_domain(email):
    """Extract domain from email address"""
    if '@' in email:
        return email.split('@')[1].lower()
    return ''

def sanitize_input(text):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ''
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', str(text))
    return text.strip()

def hash_email(email):
    """Generate hash for email address (for privacy)"""
    return hashlib.sha256(email.encode()).hexdigest()[:16]

def parse_recipients(recipients_string):
    """Parse recipients string into list"""
    if not recipients_string:
        return []
    
    # Split by common delimiters
    recipients = re.split(r'[;,\n]', recipients_string)
    return [r.strip() for r in recipients if r.strip()]

def calculate_text_entropy(text):
    """Calculate entropy of text (for anomaly detection)"""
    if not text:
        return 0.0
    
    # Count character frequencies
    char_counts = {}
    for char in text.lower():
        char_counts[char] = char_counts.get(char, 0) + 1
    
    # Calculate entropy
    text_length = len(text)
    entropy = 0.0
    for count in char_counts.values():
        probability = count / text_length
        if probability > 0:
            entropy -= probability * (probability ** 0.5)  # Simplified entropy calculation
    
    return entropy

def detect_suspicious_patterns(text):
    """Detect suspicious patterns in text"""
    if not text:
        return []
    
    patterns = []
    text_lower = text.lower()
    
    # Check for suspicious keywords
    suspicious_keywords = [
        'urgent', 'immediate', 'confidential', 'secret',
        'password', 'login', 'verify', 'suspend',
        'click here', 'download', 'install'
    ]
    
    for keyword in suspicious_keywords:
        if keyword in text_lower:
            patterns.append(f'suspicious_keyword:{keyword}')
    
    # Check for excessive punctuation
    if text.count('!') > 2:
        patterns.append('excessive_exclamation')
    
    # Check for suspicious URLs (simplified)
    if re.search(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text):
        patterns.append('contains_url')
    
    # Check for IP addresses
    if re.search(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b', text):
        patterns.append('contains_ip_address')
    
    return patterns

def format_risk_score(score):
    """Format risk score for display"""
    if score < 2:
        return f"{score:.1f} (Low)"
    elif score < 5:
        return f"{score:.1f} (Medium)"
    elif score < 8:
        return f"{score:.1f} (High)"
    else:
        return f"{score:.1f} (Critical)"

def get_severity_color(severity):
    """Get Bootstrap color class for severity"""
    color_map = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'critical': 'dark'
    }
    return color_map.get(severity.lower(), 'secondary')

def time_ago(timestamp):
    """Format timestamp as 'time ago' string"""
    if not timestamp:
        return 'Unknown'
    
    now = datetime.utcnow()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def generate_case_id():
    """Generate unique case ID"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    return f"CASE-{timestamp}"

class SecurityLogger:
    """Security-focused logging utility"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        
    def log_security_event(self, event_type, details, severity='info'):
        """Log security-related events"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': severity
        }
        
        if severity == 'critical':
            self.logger.critical(log_entry)
        elif severity == 'high':
            self.logger.error(log_entry)
        elif severity == 'medium':
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)
    
    def log_processing_error(self, stage, error_details):
        """Log processing pipeline errors"""
        self.log_security_event(
            'processing_error',
            f'Stage: {stage}, Error: {error_details}',
            'high'
        )
    
    def log_threat_detection(self, threat_type, risk_score, email_details):
        """Log threat detections"""
        self.log_security_event(
            'threat_detection',
            f'Type: {threat_type}, Risk Score: {risk_score}, Email: {email_details}',
            'critical' if risk_score > 8 else 'high'
        )
