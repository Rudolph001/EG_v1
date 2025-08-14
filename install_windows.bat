
@echo off
echo ========================================
echo Email Guardian - Windows Installation
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking Python version...
python -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if %errorlevel% neq 0 (
    echo ERROR: Python 3.11 or higher is required
    echo Please upgrade your Python installation
    pause
    exit /b 1
)

echo Python version OK
echo.

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing required packages...
python -m pip install email-validator==2.2.0
python -m pip install flask==3.1.1
python -m pip install flask-sqlalchemy==3.1.1
python -m pip install gunicorn==23.0.0
python -m pip install networkx==3.5
python -m pip install numpy==2.3.2
python -m pip install pandas==2.3.1
python -m pip install psycopg2-binary==2.9.10
python -m pip install scikit-learn==1.7.1
python -m pip install sqlalchemy==2.0.42
python -m pip install werkzeug==3.1.3
python -m pip install textblob==0.19.0
python -m pip install xgboost==3.0.4
python -m pip install imbalanced-learn==0.12.4

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Creating required directories...
if not exist "uploads" mkdir uploads
if not exist "logs" mkdir logs
if not exist "instance" mkdir instance

echo.
echo ========================================
echo Setting up SQLite database...
echo ========================================
set FLASK_ENV=development

echo Running primary database setup...
python inline_db_setup.py
set DB_SETUP_RESULT=%errorlevel%

if %DB_SETUP_RESULT% neq 0 (
    echo.
    echo WARNING: Primary setup failed, trying setup_local_db.py...
    python setup_local_db.py
    set DB_SETUP_RESULT2=%errorlevel%
    
    if %DB_SETUP_RESULT2% neq 0 (
        echo.
        echo WARNING: setup_local_db.py also failed, trying fix_local_setup.py...
        python -c "import os; os.makedirs('instance', exist_ok=True); print('Created instance directory')"
        python fix_local_setup.py
        
        if %errorlevel% neq 0 (
            echo.
            echo ERROR: All database setup methods failed
            echo Please manually run one of these:
            echo   python inline_db_setup.py
            echo   python setup_local_db.py
            echo   python fix_local_setup.py
            pause
            exit /b 1
        )
    )
)

echo.
echo Verifying database setup...
python -c "import os; os.environ.setdefault('DATABASE_URL', 'sqlite:///./instance/email_guardian.db'); from app import app, db; from models import SecurityRule; app.app_context().push(); print(f'Database has {SecurityRule.query.count()} security rules')"

if %errorlevel% neq 0 (
    echo WARNING: Database verification failed
    echo You may need to run: python fix_local_setup.py
) else (
    echo ✓ Database setup verified successfully
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Database location: %cd%\instance\email_guardian.db
echo Default security rules and configuration have been added
echo.
echo To run the application:
echo   python run_local.py
echo.
echo Then open your browser to: http://localhost:5000
echo.
echo If you see "Dashboard data temporarily unavailable":
echo   python fix_local_setup.py
echo   OR see: DATABASE_TROUBLESHOOTING.md
echo.
echo Press any key to start the application now...
pause

echo Starting Email Guardian...
python run_local.py
