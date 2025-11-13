#!/bin/bash

echo "Starting HeyReach Performance Dashboard..."
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.7+ and try again"
    exit 1
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "ERROR: config.yaml not found!"
    echo "Please create config.yaml with your HeyReach API key"
    exit 1
fi

# Install dependencies if needed
echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Starting Flask server..."
echo "Dashboard will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
