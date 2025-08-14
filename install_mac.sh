
#!/bin/bash

echo "========================================"
echo "Email Guardian - Mac/Linux Installation"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11 or higher:"
    echo "  Mac: brew install python@3.11"
    echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-pip python3.11-venv"
    echo "  CentOS/RHEL: sudo yum install python3.11 python3.11-pip"
    exit 1
fi

# Check Python version
python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"
if [ $? -ne 0 ]; then
    echo "ERROR: Python 3.11 or higher is required"
    echo "Please upgrade your Python installation"
    exit 1
fi

echo "Python version OK"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "Installing pip..."
    python3 -m ensurepip --upgrade
fi

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing required packages..."
python3 -m pip install email-validator==2.2.0
python3 -m pip install flask==3.1.1
python3 -m pip install flask-sqlalchemy==3.1.1
python3 -m pip install gunicorn==23.0.0
python3 -m pip install networkx==3.5
python3 -m pip install numpy==2.3.2
python3 -m pip install pandas==2.3.1
python3 -m pip install psycopg2-binary==2.9.10
python3 -m pip install scikit-learn==1.7.1
python3 -m pip install sqlalchemy==2.0.42
python3 -m pip install werkzeug==3.1.3
python3 -m pip install textblob==0.19.0
python3 -m pip install xgboost==3.0.4
python3 -m pip install imbalanced-learn==0.12.4

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Creating required directories..."
mkdir -p uploads
mkdir -p logs
mkdir -p instance

echo ""
echo "Setting up SQLite database with default data..."
export FLASK_ENV=development
python3 setup_local_db.py

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize database with setup script"
    echo "Trying alternative setup method..."
    python3 -c "
import sys
sys.path.append('.')
try:
    from app import app, db
    with app.app_context():
        db.create_all()
        print('Basic SQLite database initialized at: instance/email_guardian.db')
except Exception as e:
    print(f'ERROR: Failed to initialize database: {e}')
    sys.exit(1)
"
    if [ $? -ne 0 ]; then
        echo "ERROR: Database setup completely failed"
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo ""
echo "Database location: $(pwd)/instance/email_guardian.db"
echo "Default security rules and configuration have been added"
echo ""
echo "To run the application:"
echo "  python3 run_local.py"
echo ""
echo "Then open your browser to: http://localhost:5000"
echo ""
echo "If you see 'Dashboard data temporarily unavailable':"
echo "  python3 fix_local_setup.py"
echo ""
echo "Press Enter to start the application now..."
read

echo "Starting Email Guardian..."
python3 run_local.py
