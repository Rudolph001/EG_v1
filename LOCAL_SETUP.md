# Email Guardian - Local Setup Guide

This guide will help you set up Email Guardian on your local machine using SQLite.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Installation Steps

### 1. Clone or Download the Project
```bash
# Download the project files to your local machine
```

### 2. Install Dependencies
```bash
# Install required Python packages
pip install -r requirements.txt
```

If you don't have a requirements.txt file, install the packages manually:
```bash
pip install flask flask-sqlalchemy sqlalchemy pandas numpy scikit-learn xgboost textblob gunicorn werkzeug
```

### 3. Set Up Local Database
Run the database setup script to create your SQLite database:
```bash
python setup_local_db.py
```

This will:
- Create the `instance/email_guardian.db` SQLite database
- Set up all required tables
- Add default security rules and configuration data

### 4. Run the Application
Start the application locally:
```bash
python run_local.py
```

The application will be available at: `http://localhost:5000`

## Database Compatibility

The application is designed to work seamlessly with both:
- **Replit Environment**: PostgreSQL database
- **Local Development**: SQLite database

The database models automatically handle the differences between PostgreSQL and SQLite, ensuring you won't encounter schema compatibility issues.

## Project Structure

```
email_guardian/
├── app.py                  # Main Flask application
├── models.py              # Database models  
├── routes.py              # Application routes
├── config.py              # Configuration settings
├── pipeline.py            # Email processing pipeline
├── ml_engines.py          # Machine learning engines
├── utils.py               # Utility functions
├── setup_local_db.py      # Local database setup script
├── run_local.py           # Local development server
├── instance/              # SQLite database directory
│   └── email_guardian.db  # SQLite database file
├── templates/             # HTML templates
├── static/                # CSS, JS, and static files
└── uploads/               # File upload directory
```

## Environment Variables

For local development, the application uses these defaults:
- `DATABASE_URL`: Automatically set to SQLite database
- `SESSION_SECRET`: Uses development secret key
- `LOG_LEVEL`: Set to INFO

## Features Available Locally

All features work the same locally as they do on Replit:

- 📧 Email CSV upload and processing
- 🔍 11-stage security analysis pipeline
- 🤖 Machine learning threat detection
- 📊 Dashboard and analytics
- ⚙️ Security rules configuration
- 📝 Case management
- 🛡️ Whitelist management

## Troubleshooting

### "Dashboard data temporarily unavailable" Error
If you see this message when accessing the dashboard:

**Quick Fix:**
```bash
python fix_local_setup.py
```

**Manual Fix:**
1. Delete the `instance/email_guardian.db` file
2. Run `python setup_local_db.py` again
3. Restart the application with `python run_local.py`

### Database Issues
If you encounter any database-related errors:
1. Run the database fix tool: `python fix_local_setup.py`
2. If that doesn't work, try:
   ```bash
   # Remove the database and start fresh
   rm instance/email_guardian.db
   python setup_local_db.py
   python run_local.py
   ```

### Missing Packages
If you get import errors:
```bash
pip install [missing-package-name]
```

Common packages you might need:
```bash
pip install flask flask-sqlalchemy pandas numpy scikit-learn xgboost textblob
```

### Port Already in Use
If port 5000 is already in use, edit `run_local.py` and change the port:
```python
app.run(host="127.0.0.1", port=5001, debug=True)  # Change to port 5001
```

### SQLite vs PostgreSQL Compatibility
The application automatically handles differences between SQLite (local) and PostgreSQL (Replit). If you see JSON-related errors:
- The app will use Text fields for SQLite and JSON fields for PostgreSQL
- No manual intervention needed - this is handled automatically

## Data Synchronization

The database schema is automatically synchronized between Replit and local environments. Any changes made to the database structure in Replit will be compatible with your local SQLite setup.

## Development Tips

- Use SQLite Browser or similar tools to view your local database
- Log files are stored in the `logs/` directory
- Uploaded CSV files are stored in the `uploads/` directory
- The application runs in debug mode locally for easier development

## Need Help?

If you encounter any issues with the local setup, check the application logs or run the database setup script again.