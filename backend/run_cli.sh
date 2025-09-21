#!/bin/bash
# Run the Python Terminal CLI interface

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

# Install dependencies (best effort for offline environments)
echo "Installing dependencies..."
if ! pip install --timeout 5 --retries 1 -r requirements.txt; then
    echo "Warning: Failed to install dependencies (continuing anyway)." >&2
fi

# Run the terminal
echo "Starting Python Terminal..."
python terminal.py "$@"
