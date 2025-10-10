#!/bin/bash

# Exam Simulator - Start Script

echo "Starting Exam Simulator..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one with your API keys."
fi

# Run the Flask application
echo "Starting Flask application..."
python app.py
