@echo off
REM Run the Python Terminal with Streamlit frontend

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

REM Start API server in background
echo Starting FastAPI backend...
start "API Server" cmd /k "uvicorn app:app --host 127.0.0.1 --port 8000"

REM Wait a moment for API to start
timeout /t 3 /nobreak >nul

REM Start Streamlit frontend
echo Starting Streamlit frontend...
echo Frontend will be available at http://localhost:8501
echo API backend running at http://localhost:8000
echo.
echo Close this window or press Ctrl+C to stop the frontend

cd ..\frontend
streamlit run app.py --server.port 8501 --server.address localhost

pause