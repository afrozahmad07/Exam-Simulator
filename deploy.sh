#!/bin/bash
################################################################################
# Deployment Script for Flask Exam Simulator on Rocky Linux 8.10
# This script is designed to be run on your VPS server
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="exam_simulator"
APP_USER="examsim"  # Virtualmin will create this user
APP_DIR="/home/${APP_USER}/exam-simulator"
DOMAIN="examsimulator.afrozahmad.com"
PYTHON_VERSION="python3.11"  # Rocky Linux 8.10 default is Python 3.6, we'll need to install 3.11

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Exam Simulator Deployment Script${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root. Run as the domain user created by Virtualmin."
    exit 1
fi

print_status "Starting deployment process..."

# Step 1: Update system packages (requires sudo)
print_status "Updating system packages..."
sudo dnf update -y || print_warning "Could not update packages. Continue anyway..."

# Step 2: Install Python 3.11 if not present
if ! command -v python3.11 &> /dev/null; then
    print_status "Installing Python 3.11..."
    sudo dnf install -y python3.11 python3.11-devel python3.11-pip
else
    print_status "Python 3.11 already installed"
fi

# Step 3: Install required system packages
print_status "Installing required system packages..."
sudo dnf install -y \
    gcc \
    gcc-c++ \
    make \
    git \
    sqlite \
    libffi-devel \
    openssl-devel \
    bzip2-devel \
    readline-devel \
    zlib-devel \
    wget \
    || print_warning "Some packages might already be installed"

# Step 4: Create application directory
print_status "Setting up application directory..."
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# Step 5: Set up Python virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Step 6: Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip wheel setuptools

# Step 7: Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements-production.txt" ]; then
    pip install -r requirements-production.txt
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    pip install gunicorn  # Ensure gunicorn is installed
else
    print_error "No requirements file found!"
    exit 1
fi

# Step 8: Create necessary directories
print_status "Creating necessary directories..."
mkdir -p uploads
mkdir -p static/logos
mkdir -p logs
sudo mkdir -p /var/log/${APP_NAME}
sudo mkdir -p /var/run/${APP_NAME}
sudo chown -R ${USER}:${USER} /var/log/${APP_NAME}
sudo chown -R ${USER}:${USER} /var/run/${APP_NAME}

# Step 9: Set up environment file
print_status "Setting up environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.production ]; then
        cp .env.production .env
        print_warning "Created .env from .env.production template"
        print_warning "Please edit .env and set your SECRET_KEY and API keys!"
    else
        print_error "No .env.production template found!"
        exit 1
    fi
else
    print_status ".env file already exists"
fi

# Step 10: Initialize database
print_status "Initializing database..."
if [ -f init_db.py ]; then
    python init_db.py || print_warning "Database initialization had warnings"
else
    print_warning "No init_db.py found. You may need to initialize the database manually."
fi

# Step 11: Create superadmin user
print_status "You can create a superadmin user after deployment using:"
echo "  cd ${APP_DIR}"
echo "  source venv/bin/activate"
echo "  python create_superadmin.py"

# Step 12: Set proper permissions
print_status "Setting file permissions..."
chmod -R 755 ${APP_DIR}
chmod 600 .env
chmod 664 *.db 2>/dev/null || true

print_status "Basic deployment complete!"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Next Steps:${NC}"
echo -e "${GREEN}========================================${NC}"
echo "1. Edit ${APP_DIR}/.env and set your SECRET_KEY and API keys"
echo "2. Set up systemd service: sudo ./setup-systemd.sh"
echo "3. Configure Nginx/Apache in Virtualmin to proxy to http://127.0.0.1:8000"
echo "4. Create superadmin user: cd ${APP_DIR} && source venv/bin/activate && python create_superadmin.py"
echo "5. Start the service: sudo systemctl start ${APP_NAME}"
echo ""
