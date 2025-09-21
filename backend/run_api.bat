@echo off
REM Run the Python Terminal web API interface on Windows

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

REM Run the API server
echo Starting Python Terminal API on http://0.0.0.0:8000
echo Web interface will be available at http://localhost:8000
echo API documentation available at http://localhost:8000/docs
echo.

uvicorn app:app --reload --host 0.0.0.0 --port 8000

pause