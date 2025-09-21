#!/bin/bash
# Simple launcher for Python Terminal Web Interface

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the Python launcher
python3 launcher.py