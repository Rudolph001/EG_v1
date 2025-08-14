# Database Troubleshooting Guide

If you see "Dashboard data temporarily unavailable" error, this guide will help you fix it.

## Quick Fix (Try This First)

Run one of these commands in your project directory:

**Windows:**
```cmd
python fix_local_setup.py
```

**Mac/Linux:**
```bash
python3 fix_local_setup.py
```

## Alternative Setup Commands

If the quick fix doesn't work, try these in order:

**Windows:**
```cmd
python inline_db_setup.py
python setup_local_db.py
python fix_local_setup.py
```

**Mac/Linux:**
```bash
python3 inline_db_setup.py
python3 setup_local_db.py
python3 fix_local_setup.py
```

## Check If Database Exists

Look for this file in your project:
- `instance/email_guardian.db`

If this file doesn't exist, the database setup didn't work.

## Manual Database Creation

If none of the scripts work, create the database manually:

**Windows:**
```cmd
mkdir instance
python -c "import os; os.environ['DATABASE_URL']='sqlite:///./instance/email_guardian.db'; from app import app, db; app.app_context().push(); db.create_all(); print('Database created')"
```

**Mac/Linux:**
```bash
mkdir -p instance
python3 -c "import os; os.environ['DATABASE_URL']='sqlite:///./instance/email_guardian.db'; from app import app, db; with app.app_context(): db.create_all(); print('Database created')"
```

## Verify Database Setup

To check if your database has the required data:

**Windows:**
```cmd
python -c "import os; os.environ['DATABASE_URL']='sqlite:///./instance/email_guardian.db'; from app import app, db; from models import SecurityRule; app.app_context().push(); print(f'Security rules: {SecurityRule.query.count()}')"
```

**Mac/Linux:**
```bash
python3 -c "import os; os.environ['DATABASE_URL']='sqlite:///./instance/email_guardian.db'; from app import app, db; from models import SecurityRule; with app.app_context(): print(f'Security rules: {SecurityRule.query.count()}')"
```

This should show at least 2 security rules if setup was successful.

## Still Having Issues?

1. Make sure you're in the correct project directory
2. Check that all Python packages are installed
3. Try deleting the `instance` folder and running the setup again
4. Ensure you have Python 3.11 or higher

## Contact Information

If you continue having database issues after trying all these steps, the problem might be with your Python installation or missing dependencies.