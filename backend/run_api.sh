#!/bin/bash
# Run the Python Terminal web API interface

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

# Run the API server
echo "Starting Python Terminal API on http://0.0.0.0:8000"
echo "Web interface will be available at http://localhost:8000"
echo "API documentation available at http://localhost:8000/docs"
echo ""

uvicorn app:app --reload --host 0.0.0.0 --port 8000