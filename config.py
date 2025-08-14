
import os

class Config:
    """Application configuration"""
    
    # Database - SQLite for local development
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'email_guardian.db')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    
    # File uploads
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'csv'}
    
    # Processing
    BATCH_SIZE = 1000
    MAX_PROCESSING_TIME = 300  # 5 minutes
    
    # ML Configuration
    ML_MODEL_UPDATE_THRESHOLD = 100
    ANOMALY_DETECTION_THRESHOLD = 0.1
    
    # Risk Scoring Weights
    SECURITY_RULE_WEIGHT = 0.3
    RISK_KEYWORD_WEIGHT = 0.2
    ML_SCORE_WEIGHT = 0.25
    ADVANCED_ML_WEIGHT = 0.25
    
    # Case Generation Thresholds
    CASE_GENERATION_THRESHOLD = 8.0
    FLAG_THRESHOLD = 5.0
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = 'logs/email_guardian.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True for SQL query debugging

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# Default risk keywords by category
DEFAULT_RISK_KEYWORDS = {
    'financial': [
        'bitcoin', 'cryptocurrency', 'wire transfer', 'bank account',
        'payment', 'invoice', 'refund', 'tax', 'irs'
    ],
    'phishing': [
        'verify account', 'confirm identity', 'update payment',
        'suspended account', 'click here', 'urgent action'
    ],
    'malware': [
        'download', 'install', 'update required', 'security patch',
        'antivirus', 'scan now'
    ],
    'data_exfiltration': [
        'confidential', 'internal use', 'do not forward',
        'proprietary', 'classified'
    ],
    'social_engineering': [
        'urgent', 'immediate', 'help needed', 'emergency',
        'personal favor', 'keep confidential'
    ]
}

# Default security rules
DEFAULT_SECURITY_RULES = [
    {
        'name': 'External sender to multiple recipients',
        'rule_type': 'pattern',
        'pattern': 'external_multiple_recipients',
        'severity': 'medium',
        'description': 'External sender sending to multiple internal recipients'
    },
    {
        'name': 'Executable attachment',
        'rule_type': 'attachment',
        'pattern': r'\.(exe|scr|bat|com|pif|vbs|js)$',
        'severity': 'high',
        'description': 'Email contains executable attachment'
    },
    {
        'name': 'Suspicious subject patterns',
        'rule_type': 'subject',
        'pattern': r'(urgent|immediate|action required|verify|suspend)',
        'severity': 'medium',
        'description': 'Subject contains urgent or suspicious keywords'
    }
]

# Default whitelist domains
DEFAULT_WHITELIST_DOMAINS = [
    'microsoft.com',
    'google.com',
    'amazon.com',
    'office365.com',
    'github.com'
]
