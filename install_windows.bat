
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

echo Installing required packages...
pip install --upgrade pip
pip install email-validator==2.2.0
pip install flask==3.1.1
pip install flask-sqlalchemy==3.1.1
pip install gunicorn==23.0.0
pip install networkx==3.5
pip install numpy==2.3.2
pip install pandas==2.3.1
pip install psycopg2-binary==2.9.10
pip install scikit-learn==1.7.1
pip install sqlalchemy==2.0.42
pip install werkzeug==3.1.3
pip install xgboost==2.1.3
pip install textblob==0.18.0
pip install imbalanced-learn==0.12.4

if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Creating required directories...
if not exist "uploads" mkdir uploads
if not exist "instance" mkdir instance

echo.
echo Setting up database...
REM Use the standalone database setup script
python setup_database.py

if %errorlevel% neq 0 (
    echo ERROR: Failed to initialize database
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo To run the application:
echo   python run_local_fixed.py
echo.
echo Then open your browser to: http://localhost:5000
echo.
echo Press any key to start the application now...
pause

echo Starting Email Guardian...
python run_local_fixed.py
