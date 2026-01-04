#!/bin/bash

echo "Starting DoubleSub.io locally..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed"
    exit 1
fi

python3 --version

# Check FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "WARNING: FFmpeg is not installed"
    echo "Video extraction will not work."
    echo ""
fi

# Create virtual environment if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "========================================"
echo " DoubleSub.io - Development Server"
echo "========================================"
echo ""
echo "Site accessible at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
