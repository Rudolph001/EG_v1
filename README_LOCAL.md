
# Email Guardian - Local Installation Guide

## Windows Installation

1. **Download Python 3.11+** from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

2. **Run the installation script:**
   ```cmd
   install_windows.bat
   ```

3. **Start the application:**
   ```cmd
   python run_local.py
   ```

## Mac/Linux Installation

1. **Install Python 3.11+:**
   ```bash
   # Mac (with Homebrew)
   brew install python@3.11
   
   # Ubuntu/Debian
   sudo apt install python3.11 python3.11-pip
   
   # CentOS/RHEL
   sudo yum install python3.11 python3.11-pip
   ```

2. **Run the installation script:**
   ```bash
   chmod +x install_mac.sh
   ./install_mac.sh
   ```

3. **Start the application:**
   ```bash
   python3 run_local.py
   ```

## Manual Installation (if scripts fail)

1. **Install dependencies:**
   ```bash
   pip install email-validator flask flask-sqlalchemy gunicorn networkx numpy pandas psycopg2-binary scikit-learn sqlalchemy werkzeug
   ```

2. **Create uploads directory:**
   ```bash
   mkdir uploads
   ```

3. **Initialize database:**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

4. **Run the application:**
   ```bash
   python run_local.py
   ```

## Accessing the Application

Once started, open your browser to: **http://localhost:5000**

## Database

The application uses SQLite by default for local development. The database file (`email_guardian.db`) will be created automatically in the project directory.

## Troubleshooting

- **Python not found:** Make sure Python is installed and added to your system PATH
- **Permission errors:** Try running as administrator (Windows) or with sudo (Mac/Linux)
- **Port 5000 in use:** Close other applications using port 5000, or modify the port in `run_local.py`
- **Missing dependencies:** Run the installation script again or install packages manually

## Features

- Upload and analyze email data from CSV files
- Security rule engine with customizable rules
- ML-powered risk scoring and anomaly detection
- Case management for security incidents
- Comprehensive dashboard and reporting
