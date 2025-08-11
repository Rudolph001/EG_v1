# Email Guardian

## Overview

Email Guardian is a Flask-based web application designed for email security analysis and threat detection. The system processes CSV files containing email data through an 11-stage pipeline, employing machine learning algorithms, security rules, and risk assessment to identify potentially malicious emails and generate security cases. It provides a comprehensive dashboard for security teams to monitor email threats, manage whitelists, configure security rules, and track investigation cases.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Web Framework**: Bootstrap 5 with responsive design
- **JavaScript Libraries**: Chart.js for analytics visualization, DataTables for tabular data
- **Template Engine**: Jinja2 with Flask's template inheritance
- **Styling**: Custom CSS with CSS variables for theming, Font Awesome icons

### Backend Architecture
- **Web Framework**: Flask with SQLAlchemy ORM
- **Database Layer**: SQLAlchemy with declarative base model structure
- **Processing Pipeline**: 11-stage email analysis pipeline including data ingestion, normalization, security analysis, and case generation
- **Machine Learning**: Dual ML engine architecture with BasicMLEngine (Isolation Forest) and AdvancedMLEngine for risk scoring and anomaly detection
- **Security Features**: Proxy fix middleware, session management, file upload validation

### Data Storage Solutions
- **Primary Database**: SQLite (development) with PostgreSQL support via environment configuration
- **Connection Management**: Connection pooling with pre-ping validation and 300-second recycle timer
- **Schema Design**: Normalized structure with EmailRecord and RecipientRecord entities, supporting case management and audit trails

### Core Processing Components
- **Pipeline Architecture**: Multi-stage processing including data ingestion, email normalization, security rule application, ML scoring, and case generation
- **Risk Assessment**: Weighted scoring system combining security rules (30%), risk keywords (20%), basic ML (25%), and advanced ML (25%)
- **Threshold Management**: Configurable thresholds for case generation (8.0) and flagging (5.0)

### Security and Rules Engine
- **Security Rules**: Pattern-based rule engine supporting multiple rule types with configurable severity levels
- **Whitelisting**: Domain and sender whitelisting with bypass capabilities
- **Risk Keywords**: Category-based keyword detection for financial, phishing, malware, data exfiltration, and social engineering threats

## External Dependencies

### Python Libraries
- **Flask**: Web framework with SQLAlchemy integration
- **scikit-learn**: Machine learning library for Isolation Forest and Random Forest algorithms
- **pandas**: Data processing and CSV handling
- **numpy**: Numerical computations for ML features
- **networkx**: Graph analysis for advanced threat detection

### Frontend Dependencies
- **Bootstrap 5**: CSS framework via CDN
- **Chart.js**: Charting library for dashboard analytics
- **DataTables**: Table enhancement with sorting, filtering, and pagination
- **Font Awesome**: Icon library for UI elements

### Infrastructure Services
- **Database**: Configurable database backend (SQLite default, PostgreSQL production-ready)
- **File Storage**: Local filesystem storage for CSV uploads with 16MB limit
- **Logging**: Python logging framework with configurable levels and file output

### Configuration Management
- **Environment Variables**: DATABASE_URL, SESSION_SECRET, LOG_LEVEL
- **Upload Handling**: Secure filename generation, file type validation, size restrictions
- **Deployment**: WSGI-compatible with ProxyFix for production reverse proxy setups