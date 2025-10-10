#!/bin/bash

# Exam Simulator - Start Script

echo "=========================================="
echo "   Starting Exam Simulator"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first to set up the application"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if database exists
if [ ! -f "exam_simulator.db" ]; then
    echo "⚠️  Database not found!"
    echo ""
    read -p "Would you like to initialize the database now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Creating database with sample data..."
        python3 init_db.py --reset --seed
        echo ""
    else
        echo "Warning: Running without database may cause errors"
        echo ""
    fi
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Some features may not work without API keys"
    echo ""
fi

# Run the Flask application
echo "🚀 Starting Flask application..."
echo "Visit: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

python3 app.py
