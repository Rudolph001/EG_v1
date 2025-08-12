@echo off
echo ========================================
echo Email Guardian - Run as Administrator
echo ========================================
echo.
echo This will start Email Guardian with administrator privileges
echo to fix any file permission issues.
echo.
pause

cd /d "%~dp0"
python start_local_fixed.py
pause