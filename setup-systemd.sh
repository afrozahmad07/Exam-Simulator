#!/bin/bash
################################################################################
# Systemd Service Setup Script for Flask Exam Simulator
# Must be run with sudo privileges
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration - CUSTOMIZE THESE
APP_NAME="exam_simulator"
APP_USER="examsim"  # The user Virtualmin created for your domain
APP_DIR="/home/${APP_USER}/exam-simulator"
DOMAIN="examsimulator.afrozahmad.com"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}ERROR:${NC} This script must be run with sudo"
    exit 1
fi

echo -e "${GREEN}Setting up systemd service for ${APP_NAME}${NC}"

# Create systemd service file
cat > /etc/systemd/system/${APP_NAME}.service << EOF
[Unit]
Description=Exam Simulator Flask Application
After=network.target

[Service]
Type=notify
User=${APP_USER}
Group=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/gunicorn -c ${APP_DIR}/gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateDevices=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${APP_DIR}/uploads ${APP_DIR}/logs /var/log/${APP_NAME} /var/run/${APP_NAME} ${APP_DIR}

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}Systemd service file created${NC}"

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable ${APP_NAME}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Systemd service setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Available commands:"
echo "  sudo systemctl start ${APP_NAME}     - Start the application"
echo "  sudo systemctl stop ${APP_NAME}      - Stop the application"
echo "  sudo systemctl restart ${APP_NAME}   - Restart the application"
echo "  sudo systemctl status ${APP_NAME}    - Check application status"
echo "  sudo systemctl enable ${APP_NAME}    - Enable auto-start on boot"
echo "  sudo systemctl disable ${APP_NAME}   - Disable auto-start on boot"
echo "  sudo journalctl -u ${APP_NAME} -f   - View live logs"
echo ""
