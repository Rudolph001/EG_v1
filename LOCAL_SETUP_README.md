# Email Guardian - Complete Local Installation Guide

## Fresh Installation (Recommended)

For a clean installation from scratch, follow these steps:

### Windows Installation

1. **Install Python 3.11+** from [python.org](https://python.org)
   - ✅ Check "Add Python to PATH" during installation

2. **Download the Email Guardian files** and extract to a new folder (e.g., `C:\EmailGuardian\`)

3. **Run the automated installer:**
   ```cmd
   install_windows.bat
   ```

4. **Start the application:**
   ```cmd
   python start_local_fixed.py
   ```
   
   **If you get permission errors, try:**
   ```cmd
   run_as_admin.bat
   ```

### Mac/Linux Installation

1. **Install Python 3.11+:**
   ```bash
   # Mac (with Homebrew)
   brew install python@3.11
   
   # Ubuntu/Debian
   sudo apt install python3.11 python3.11-pip
   
   # CentOS/RHEL
   sudo yum install python3.11 python3.11-pip
   ```

2. **Download and extract Email Guardian files**

3. **Run the automated installer:**
   ```bash
   chmod +x install_mac.sh
   ./install_mac.sh
   ```

4. **Start the application:**
   ```bash
   python3 start_local.py
   ```

## Manual Installation (If Scripts Fail)

If the automated scripts don't work, follow these manual steps:

### Step 1: Install Dependencies
```bash
pip install email-validator flask flask-sqlalchemy networkx numpy pandas scikit-learn sqlalchemy werkzeug xgboost textblob imbalanced-learn
```

### Step 2: Create Directories
```bash
mkdir uploads
mkdir instance
mkdir logs
```

### Step 3: Initialize Database
```bash
python setup_local_db.py
```

### Step 4: Start Application
```bash
python start_local.py
```

## What Gets Installed

The installation process will:

✅ **Check Python version** (requires 3.11+)
✅ **Install required packages:**
   - Flask web framework
   - SQLAlchemy database toolkit
   - Machine learning libraries (scikit-learn, xgboost)
   - Data processing (pandas, numpy)
   - Natural language processing (textblob)

✅ **Create directories:**
   - `uploads/` - For CSV file uploads
   - `instance/` - For SQLite database
   - `logs/` - For application logs

✅ **Set up database** with default configuration:
   - Email records table
   - Security rules
   - Whitelisted domains
   - Risk keywords

✅ **Configure local development** environment

## Using the Application

1. **Access the web interface:** http://localhost:5000

2. **Key features available:**
   - Email upload and analysis
   - Security dashboard
   - Risk assessment
   - Case management
   - Security rules configuration

## Troubleshooting

### Common Issues

**"Python not found" error:**
- Install Python 3.11+ and make sure it's in your PATH
- Windows: Reinstall Python with "Add to PATH" checked

**"Permission denied" errors:**
- Windows: Run Command Prompt as Administrator
- Mac/Linux: Use `sudo` or install packages with `--user` flag

**"Module not found" errors:**
- Run: `pip install -r requirements.txt` (if available)
- Or install packages individually as shown above

**Database initialization fails:**
- Check you're in the project root directory
- Ensure the `instance/` directory exists and is writable
- Try: `python setup_local_db.py` manually

**Application won't start:**
- Verify all files are present: `models.py`, `routes.py`, `templates/`, `static/`
- Check the database was created: `instance/email_guardian.db`
- Look for error messages in the console

### Getting Help

If you encounter issues:

1. Check you have all required files in the project directory
2. Verify Python 3.11+ is installed: `python --version`
3. Ensure all packages installed successfully
4. Check the database file exists: `instance/email_guardian.db`
5. Look at console output for specific error messages

### Clean Reinstall

To start completely fresh:

1. Delete the project folder
2. Download/extract files to a new location
3. Run the installation script again

## Files Overview

- `install_windows.bat` / `install_mac.sh` - Automated installers
- `setup_local_db.py` - Database initialization
- `start_local.py` - Application launcher
- `models.py` - Database models
- `routes.py` - Web routes and handlers
- `templates/` - HTML templates
- `static/` - CSS, JavaScript, images
- `uploads/` - User uploaded files
- `instance/` - SQLite database storage