#!/bin/bash
################################################################################
# Update Application from GitHub
# Run this script on your VPS to pull latest changes from GitHub
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
APP_NAME="exam_simulator"
APP_DIR="$(pwd)"  # Current directory

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Updating Exam Simulator from GitHub${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}ERROR:${NC} Not a git repository. Please initialize git first."
    exit 1
fi

# Backup database before update
echo -e "${YELLOW}Backing up database...${NC}"
if [ -f "exam_simulator.db" ]; then
    cp exam_simulator.db "exam_simulator.db.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}Database backed up${NC}"
fi

# Stash any local changes
echo -e "${YELLOW}Stashing local changes (if any)...${NC}"
git stash

# Pull latest changes
echo -e "${GREEN}Pulling latest changes from GitHub...${NC}"
git pull origin main

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Update dependencies
echo -e "${GREEN}Updating Python dependencies...${NC}"
if [ -f "requirements-production.txt" ]; then
    pip install -r requirements-production.txt --upgrade
elif [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --upgrade
fi

# Run database migrations if needed
if [ -f "migrate_db.py" ]; then
    echo -e "${GREEN}Running database migrations...${NC}"
    python migrate_db.py || echo -e "${YELLOW}No migrations needed or migration failed${NC}"
fi

# Restart the service
echo -e "${GREEN}Restarting application service...${NC}"
sudo systemctl restart ${APP_NAME}

# Check status
sleep 2
if sudo systemctl is-active --quiet ${APP_NAME}; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Update completed successfully!${NC}"
    echo -e "${GREEN}Application is running${NC}"
    echo -e "${GREEN}========================================${NC}"
else
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}Update completed but service failed to start${NC}"
    echo -e "${RED}Check logs: sudo journalctl -u ${APP_NAME} -n 50${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi

# Show recent logs
echo ""
echo -e "${GREEN}Recent logs:${NC}"
sudo journalctl -u ${APP_NAME} -n 20 --no-pager

echo ""
echo -e "${GREEN}Update complete!${NC}"
