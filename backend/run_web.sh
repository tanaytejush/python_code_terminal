#!/bin/bash
# Run the Python Terminal Web Interface (Streamlit frontend + FastAPI backend together)

# Set up the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🐍 Python Terminal Web Interface"
echo "================================"
echo "Starting integrated frontend and backend..."
echo ""

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Stopping all services..."
    jobs -p | xargs -r kill 2>/dev/null
    pkill -f "uvicorn app:app" 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    echo "All services stopped. Goodbye!"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Start API server in background
echo "📡 Starting FastAPI backend (http://localhost:8000)..."
uvicorn app:app --host 127.0.0.1 --port 8000 --log-level warning &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend ready!"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start within 30 seconds"
        kill $API_PID 2>/dev/null
        exit 1
    fi
done

# Start Streamlit frontend
echo "🖥️  Starting Streamlit frontend (http://localhost:8501)..."
echo ""
echo "🎉 Both services are starting..."
echo "   Frontend: http://localhost:8501"
echo "   Backend:  http://localhost:8000"
echo ""
echo "💡 The frontend will open in your browser automatically"
echo "🛑 Press Ctrl+C to stop both services"
echo ""

# Run Streamlit (this will block until Streamlit exits)
cd ../frontend
streamlit run app.py --server.port 8501 --server.address localhost --browser.serverAddress localhost --browser.gatherUsageStats false

# If we get here, Streamlit has exited, so cleanup
cleanup