#!/bin/bash
################################################################################
# Enhanced Server Deployment Script
# Run this on your VPS server to deploy latest changes from GitHub
################################################################################

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/home/examsimulator/Exam-Simulator"
SERVICE_NAME="exam-simulator"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Exam Simulator - Server Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to print status messages
print_status() {
    echo -e "${GREEN}→${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Navigate to app directory
cd ${APP_DIR} || {
    print_error "Could not change to ${APP_DIR}"
    exit 1
}

# Step 1: Pull latest code from GitHub
print_status "Pulling latest code from GitHub..."
git fetch origin
git pull origin main || {
    print_error "Failed to pull from GitHub"
    exit 1
}

# Step 2: Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate || {
    print_error "Failed to activate virtual environment"
    exit 1
}

# Step 3: Install/update dependencies
print_status "Installing/updating Python dependencies..."
pip install -r requirements.txt || {
    print_warning "Some dependencies may have failed to install"
}

# Step 4: Run database migrations
print_status "Running database migrations..."
python migrate_db.py || {
    print_error "Database migration failed"
    exit 1
}

# Step 4.5: Run bug fix migrations (one-time migrations for specific bugs)
print_status "Running bug fix migrations (if needed)..."

# Check if migrations have been applied by looking for marker files
if [ ! -f ".migration_user_answer_done" ]; then
    print_status "Applying user_answer column migration..."
    echo "2" | python3 migrate_user_answer_column.py && touch .migration_user_answer_done || print_warning "User answer migration failed or already applied"
else
    print_status "User answer migration already applied (skipping)"
fi

if [ ! -f ".migration_url_path_done" ]; then
    print_status "Applying url_path constraint migration..."
    echo "2" | python3 migrate_url_path_constraint.py && touch .migration_url_path_done || print_warning "URL path migration failed or already applied"
else
    print_status "URL path migration already applied (skipping)"
fi

# Step 5: Restart the application service
print_status "Restarting application service..."
systemctl restart ${SERVICE_NAME} || {
    print_error "Failed to restart service"
    exit 1
}

# Step 6: Wait a moment for service to start
sleep 2

# Step 7: Check service status
print_status "Checking service status..."
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo -e "${GREEN}✓${NC} Service is running"
else
    print_error "Service failed to start!"
    echo "Recent logs:"
    journalctl -u ${SERVICE_NAME} -n 20 --no-pager
    exit 1
fi

# Step 8: Show recent logs
print_status "Recent logs (last 10 lines):"
journalctl -u ${SERVICE_NAME} -n 10 --no-pager

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Visit: ${GREEN}https://examsimulator.afrozahmad.com${NC}"
echo ""
echo "Useful commands:"
echo "  View logs: journalctl -u ${SERVICE_NAME} -f"
echo "  Restart:   systemctl restart ${SERVICE_NAME}"
echo "  Status:    systemctl status ${SERVICE_NAME}"
echo ""
