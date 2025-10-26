@echo off
cls
echo ======================================================
echo            🛡️ CYBER SHIELD PRO            
echo ======================================================
echo.
echo Initializing advanced penetration testing firewall...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python from https://www.python.org/downloads/
    echo During installation, make sure to check "Add Python to PATH"
    echo.
    pause
    exit /b
)

REM Check if required packages are installed
echo Checking required dependencies...
python -c "import psutil" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing psutil...
    pip install psutil
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install psutil
        echo.
        echo Please manually run: pip install psutil
        echo.
        pause
        exit /b
    )
)

python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing requests...
    pip install requests
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install requests
        echo.
        echo Please manually run: pip install requests
        echo.
        pause
        exit /b
    )
)

echo.
echo Starting Cyber Shield Pro Firewall...
echo.
echo Advanced Features:
echo  - Real-time IP filtering with geolocation
echo  - Port management with access control
echo  - DDoS protection with rate limiting
echo  - Process monitoring and control
echo  - Integrated system terminal
echo  - Suspicious activity detection
echo.
echo Press Ctrl+C to exit the application
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start the firewall application
    echo.
    echo Please check that all Python files are in this directory
    echo.
    pause
)