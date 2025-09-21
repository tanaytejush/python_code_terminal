@echo off
REM Run the Python Terminal Web Interface (Streamlit frontend + FastAPI backend together)

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

echo.
echo 🐍 Python Terminal Web Interface
echo ================================
echo Starting integrated frontend and backend...
echo.

REM Start API server in background with minimal window
echo 📡 Starting FastAPI backend (http://localhost:8000)...
start "Python Terminal API" /min cmd /c "uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning"

REM Wait for API to be ready
echo ⏳ Waiting for backend to start...
:wait_loop
timeout /t 2 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    goto wait_loop
) else (
    echo ✅ Backend ready!
)

REM Start Streamlit frontend
echo 🖥️  Starting Streamlit frontend (http://localhost:8501)...
echo.
echo 🎉 Both services are starting...
echo    Frontend: http://localhost:8501
echo    Backend:  http://localhost:8000
echo.
echo 💡 The frontend will open in your browser automatically
echo 🛑 Close this window to stop both services
echo.

cd ..\frontend
streamlit run app.py --server.port 8501 --server.address localhost --browser.serverAddress localhost --browser.gatherUsageStats false

REM When Streamlit exits, try to close the API server window
echo.
echo Stopping services...
taskkill /f /im "uvicorn.exe" >nul 2>&1
echo All services stopped. Goodbye!
pause