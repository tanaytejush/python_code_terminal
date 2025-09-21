@echo off
REM Run the Python Terminal CLI interface on Windows

REM Set up the script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the terminal
echo Starting Python Terminal...
python terminal.py %*

pause