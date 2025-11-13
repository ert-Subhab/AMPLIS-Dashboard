@echo off
echo Starting HeyReach Performance Dashboard...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

REM Check if config.yaml exists
if not exist config.yaml (
    echo ERROR: config.yaml not found!
    echo Please create config.yaml with your HeyReach API key
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Starting Flask server...
echo Dashboard will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
