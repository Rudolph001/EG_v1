
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
    echo "  Ubuntu/Debian: sudo apt install python3.11 python3.11-pip"
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

echo "Installing required packages..."
pip3 install --upgrade pip
pip3 install email-validator==2.2.0
pip3 install flask==3.1.1
pip3 install flask-sqlalchemy==3.1.1
pip3 install gunicorn==23.0.0
pip3 install networkx==3.5
pip3 install numpy==2.3.2
pip3 install pandas==2.3.1
pip3 install psycopg2-binary==2.9.10
pip3 install scikit-learn==1.7.1
pip3 install sqlalchemy==2.0.42
pip3 install werkzeug==3.1.3

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "Creating required directories..."
mkdir -p uploads
mkdir -p instance

echo ""
echo "Setting up database..."
# Create database using the application's built-in fallback mechanism
python3 -c "from app import app, db; app.app_context().push(); db.create_all(); print('Database initialized successfully')"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to initialize database"
    exit 1
fi

echo ""
echo "========================================"
echo "Installation completed successfully!"
echo "========================================"
echo ""
echo "To run the application:"
echo "  python3 main.py"
echo ""
echo "Then open your browser to: http://localhost:5000"
echo ""
echo "Press Enter to start the application now..."
read

echo "Starting Email Guardian..."
python3 main.py
