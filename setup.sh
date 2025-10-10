#!/bin/bash

# Exam Simulator - Setup Script
# This script sets up the application for first-time use

set -e  # Exit on error

echo "=========================================="
echo "   Exam Simulator - Initial Setup"
echo "=========================================="
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3 and try again"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip -q
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "Creating .env file with default values..."

    # Generate a random secret key
    SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

    cat > .env << EOF
# OpenAI API Key for AI-powered exam generation
OPENAI_API_KEY=your_openai_api_key_here

# Flask Secret Key for session management
SECRET_KEY=$SECRET_KEY

# Database URL (defaults to SQLite)
DATABASE_URL=sqlite:///exam_simulator.db
EOF
    echo "✓ .env file created with generated SECRET_KEY"
    echo "⚠️  Please add your OPENAI_API_KEY to .env file"
else
    echo "✓ .env file already exists"
fi
echo ""

# Initialize database
echo "🗄️  Initializing database..."
read -p "Do you want to initialize the database with sample data? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating database with sample data..."
    python3 init_db.py --reset --seed
    echo ""
    echo "✓ Database initialized with sample data"
    echo ""
    echo "📝 Sample Login Credentials:"
    echo "   Admin:    admin@example.com    / admin123"
    echo "   Teacher:  teacher@example.com  / teacher123"
    echo "   Student:  student@example.com  / student123"
else
    echo "Creating empty database..."
    python3 init_db.py --reset --no-seed
    echo "✓ Database initialized (empty)"
fi
echo ""

# Create uploads directory if it doesn't exist
mkdir -p uploads
echo "✓ Uploads directory ready"
echo ""

echo "=========================================="
echo "   ✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 app.py"
echo ""
echo "Then visit: http://localhost:5000"
echo ""
