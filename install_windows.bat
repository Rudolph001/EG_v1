
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
echo Setting up SQLite database with default data...
set FLASK_ENV=development
python setup_local_db.py

if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize database
    echo Trying alternative setup method...
    python -c "import sys; sys.path.append('.'); from app import app, db; app.app_context().push(); db.create_all(); print('Basic SQLite database initialized at: instance\\email_guardian.db')"
    if %errorlevel% neq 0 (
        echo ERROR: Database setup completely failed
        pause
        exit /b 1
    )
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
echo.
echo Press any key to start the application now...
pause

echo Starting Email Guardian...
python run_local.py
