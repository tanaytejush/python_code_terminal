#!/bin/bash
# Run the Python Terminal with Streamlit frontend

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

# Start API server in background
echo "Starting FastAPI backend..."
uvicorn app:app --host 127.0.0.1 --port 8000 &
API_PID=$!

# Wait a moment for API to start
sleep 3

# Start Streamlit frontend
echo "Starting Streamlit frontend..."
echo "Frontend will be available at http://localhost:8501"
echo "API backend running at http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both services"

# Function to cleanup background processes
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $API_PID 2>/dev/null
    pkill -f "streamlit run" 2>/dev/null
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Run Streamlit
cd ../frontend
streamlit run app.py --server.port 8501 --server.address localhost

# If streamlit exits, cleanup
cleanup