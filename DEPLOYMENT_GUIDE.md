# Exam Simulator - Complete Deployment Guide for Rocky Linux 8.10 with Virtualmin

This guide walks you through deploying the Flask Exam Simulator application on a Rocky Linux 8.10 VPS with Virtualmin/Webmin.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Local Development Setup (Windows WSL Ubuntu)](#local-development-setup)
3. [VPS Server Setup](#vps-server-setup)
4. [Cloudflare DNS Configuration](#cloudflare-dns-configuration)
5. [Virtualmin Virtual Server Setup](#virtualmin-virtual-server-setup)
6. [Application Deployment](#application-deployment)
7. [Web Server Configuration](#web-server-configuration)
8. [SSL Certificate Setup](#ssl-certificate-setup)
9. [Post-Deployment Configuration](#post-deployment-configuration)
10. [GitHub Workflow](#github-workflow)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Your Windows PC (WSL Ubuntu 24.04):
- Ubuntu 24.04 WSL installed
- Git configured
- GitHub account with repository access
- SSH key set up for GitHub

### On Your VPS (Rocky Linux 8.10):
- Fresh Rocky Linux 8.10 installation
- Webmin/Virtualmin installed and configured
- Root or sudo access
- Public IP address
- Domain name (examsimulator.afrozahmad.com)

### On Cloudflare:
- Domain registered (afrozahmad.com)
- Cloudflare account with domain added

---

## Local Development Setup (Windows WSL Ubuntu)

### 1. Install Required Tools

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ and development tools
sudo apt install -y python3.11 python3.11-venv python3-pip git

# Install additional dependencies
sudo apt install -y build-essential libssl-dev libffi-dev python3-dev
```

### 2. Clone or Navigate to Your Project

```bash
# Navigate to your project directory
cd /home/afroz/Exam-Simulator

# Initialize git if not already done
git init

# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/exam-simulator.git

# Or if using SSH
git remote add origin git@github.com:YOUR_USERNAME/exam-simulator.git
```

### 3. Set Up Local Development Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.production .env

# Edit .env with your local settings
nano .env
```

### 4. Test Locally

```bash
# Initialize database
python init_db.py

# Create superadmin (optional for local testing)
python create_superadmin.py

# Run development server
python app.py
```

Visit http://localhost:5000 to test the application.

---

## VPS Server Setup

### 1. Connect to Your VPS

```bash
# From your Windows PC (PowerShell or WSL)
ssh root@YOUR_VPS_IP
```

### 2. Initial Server Configuration

```bash
# Update system
dnf update -y

# Install EPEL repository
dnf install -y epel-release

# Install basic tools
dnf install -y git wget curl vim nano htop
```

### 3. Verify Virtualmin Installation

```bash
# Check if Virtualmin is installed
systemctl status webmin

# Access Webmin at: https://YOUR_VPS_IP:10000
```

If Virtualmin is not installed, follow the official installation guide:
```bash
# Download and run Virtualmin install script
wget https://software.virtualmin.com/gpl/scripts/virtualmin-install.sh
chmod +x virtualmin-install.sh
./virtualmin-install.sh
```

### 4. Configure Firewall

```bash
# Allow HTTP, HTTPS, and Webmin
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --permanent --add-port=10000/tcp
firewall-cmd --reload

# Verify firewall rules
firewall-cmd --list-all
```

---

## Cloudflare DNS Configuration

### 1. Log in to Cloudflare Dashboard
- Go to https://dash.cloudflare.com
- Select your domain: afrozahmad.com

### 2. Add DNS Record

1. Click on **DNS** tab
2. Click **Add record**
3. Configure:
   - **Type**: A
   - **Name**: examsimulator
   - **IPv4 address**: YOUR_VPS_PUBLIC_IP
   - **Proxy status**: DNS only (gray cloud) - Initially disable proxy
   - **TTL**: Auto

4. Click **Save**

### 3. Verify DNS Propagation

```bash
# From your local machine
nslookup examsimulator.afrozahmad.com

# Or use online tool: https://dnschecker.org
```

**Note**: DNS propagation can take 5 minutes to 48 hours, but usually completes within 15 minutes.

---

## Virtualmin Virtual Server Setup

### 1. Access Virtualmin
- Navigate to: https://YOUR_VPS_IP:10000
- Login with root credentials

### 2. Create Virtual Server

1. Click **Create Virtual Server** (top left)
2. Fill in the form:
   - **Domain name**: examsimulator.afrozahmad.com
   - **Description**: Exam Simulator Application
   - **Administration username**: examsim
   - **Administration password**: [Choose a strong password]
   - **MySQL database**: No (we'll use SQLite for now)
   - **Password storage mode**: Store encrypted

3. Click **Create Server**

Virtualmin will:
- Create user `examsim`
- Create home directory `/home/examsim`
- Configure Apache or Nginx
- Set up DNS
- Create email accounts (optional)

### 3. Note the Virtual Server Settings

After creation, note:
- **Home directory**: `/home/examsim`
- **Username**: `examsim`
- **Web server**: Apache or Nginx (check in System Settings)

---

## Application Deployment

### 1. SSH as Domain User

From your local machine:

```bash
# SSH as the virtualmin user (not root)
ssh examsim@YOUR_VPS_IP

# Or if you have root access
ssh root@YOUR_VPS_IP
su - examsim
```

### 2. Clone Repository from GitHub

```bash
# Navigate to home directory
cd ~

# Clone your repository
git clone https://github.com/YOUR_USERNAME/exam-simulator.git
cd exam-simulator

# Or if using SSH
git clone git@github.com:YOUR_USERNAME/exam-simulator.git
cd exam-simulator
```

**Note**: If the repository is private, you'll need to set up SSH keys or use a personal access token.

### 3. Run Deployment Script

```bash
# Make scripts executable (if not already)
chmod +x deploy.sh setup-systemd.sh update-from-github.sh

# Run deployment script
./deploy.sh
```

The script will:
- Install Python 3.11
- Create virtual environment
- Install dependencies
- Create necessary directories
- Set up environment file
- Initialize database

### 4. Configure Environment Variables

```bash
# Edit .env file
nano .env
```

Set these critical variables:

```env
# Generate a secure secret key
SECRET_KEY=your_secure_random_secret_key_here

# Set Flask environment
FLASK_ENV=production
FLASK_DEBUG=False

# Database (SQLite for start, PostgreSQL recommended for production)
DATABASE_URL=sqlite:///exam_simulator.db

# API Keys (optional, can be set per organization)
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here

# Security
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True

# Domain
DOMAIN=examsimulator.afrozahmad.com
```

To generate a secure SECRET_KEY:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 5. Set Up Systemd Service

```bash
# Switch to root or use sudo
sudo ./setup-systemd.sh
```

**Important**: Edit the script first to verify the paths match your setup:

```bash
nano setup-systemd.sh
```

Verify:
- `APP_USER="examsim"`
- `APP_DIR="/home/examsim/exam-simulator"`

### 6. Start the Application

```bash
# Start the service
sudo systemctl start exam_simulator

# Check status
sudo systemctl status exam_simulator

# Enable auto-start on boot
sudo systemctl enable exam_simulator

# View logs
sudo journalctl -u exam_simulator -f
```

### 7. Create Superadmin User

```bash
# Navigate to app directory
cd ~/exam-simulator

# Activate virtual environment
source venv/bin/activate

# Run superadmin creation script
python create_superadmin.py
```

Follow the prompts to create your superadmin account.

---

## Web Server Configuration

The application runs on Gunicorn at `http://127.0.0.1:8000`. Now we need to configure the web server (Nginx or Apache) to proxy requests to it.

### Option A: Nginx Configuration

1. **Access Virtualmin** → **Servers** → **examsimulator.afrozahmad.com**
2. Click **Services** → **Configure Website**
3. Or go to **Server Configuration** → **Edit Directives**

4. Open the Nginx configuration reference file:

```bash
cat ~/exam-simulator/nginx-virtualmin-config.conf
```

5. In Virtualmin's **Edit Directives**, add the configuration from `nginx-virtualmin-config.conf`

6. Test Nginx configuration:

```bash
sudo nginx -t
```

7. Reload Nginx:

```bash
sudo systemctl reload nginx
```

### Option B: Apache Configuration

1. **Access Virtualmin** → **Servers** → **examsimulator.afrozahmad.com**
2. Go to **Server Configuration** → **Edit Directives**

3. Open the Apache configuration reference file:

```bash
cat ~/exam-simulator/apache-virtualmin-config.conf
```

4. Add the configuration to your VirtualHost

5. Enable required Apache modules:

```bash
sudo dnf install mod_proxy_html -y
sudo systemctl restart httpd
```

6. Test Apache configuration:

```bash
sudo apachectl configtest
```

7. Reload Apache:

```bash
sudo systemctl reload httpd
```

---

## SSL Certificate Setup

### 1. Using Let's Encrypt (Recommended - Free)

Virtualmin makes this easy:

1. **Access Virtualmin** → **Servers** → **examsimulator.afrozahmad.com**
2. Click **Server Configuration** → **SSL Certificate**
3. Click **Let's Encrypt** tab
4. Click **Request Certificate**
5. Wait for certificate to be issued

Or via command line:

```bash
# Install certbot
sudo dnf install certbot python3-certbot-nginx -y

# Or for Apache
sudo dnf install certbot python3-certbot-apache -y

# Request certificate
sudo certbot --nginx -d examsimulator.afrozahmad.com

# Or for Apache
sudo certbot --apache -d examsimulator.afrozahmad.com
```

### 2. Enable HTTPS Redirect

After SSL is set up:

**For Nginx**, add to your configuration:

```nginx
server {
    listen 80;
    server_name examsimulator.afrozahmad.com;
    return 301 https://$server_name$request_uri;
}
```

**For Apache**, uncomment the redirect section in the config or add:

```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}$1 [R=301,L]
```

### 3. Test SSL

Visit: https://examsimulator.afrozahmad.com

Check SSL rating: https://www.ssllabs.com/ssltest/

---

## Post-Deployment Configuration

### 1. Verify Application is Running

```bash
# Check service status
sudo systemctl status exam_simulator

# Check if Gunicorn is listening
sudo ss -tlnp | grep 8000

# Test locally on VPS
curl http://127.0.0.1:8000
```

### 2. Test External Access

From your browser:
- HTTP: http://examsimulator.afrozahmad.com
- HTTPS: https://examsimulator.afrozahmad.com

### 3. Configure Application Settings

1. Log in as superadmin
2. Navigate to `/admin`
3. Configure:
   - Organization settings
   - API keys (if not set in .env)
   - User roles
   - White-label branding

### 4. Set Up Backups

Create a backup script:

```bash
nano ~/backup-exam-simulator.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/examsim/backups"
DATE=$(date +%Y%m%d_%H%M%S)
APP_DIR="/home/examsim/exam-simulator"

mkdir -p ${BACKUP_DIR}

# Backup database
cp ${APP_DIR}/exam_simulator.db ${BACKUP_DIR}/exam_simulator_${DATE}.db

# Backup uploads
tar -czf ${BACKUP_DIR}/uploads_${DATE}.tar.gz ${APP_DIR}/uploads

# Keep only last 7 backups
find ${BACKUP_DIR} -name "exam_simulator_*.db" -mtime +7 -delete
find ${BACKUP_DIR} -name "uploads_*.tar.gz" -mtime +7 -delete

echo "Backup completed: ${DATE}"
```

Make executable and add to crontab:

```bash
chmod +x ~/backup-exam-simulator.sh

# Add to crontab (daily at 2 AM)
crontab -e
```

Add:
```
0 2 * * * /home/examsim/backup-exam-simulator.sh >> /home/examsim/backup.log 2>&1
```

---

## GitHub Workflow

### On Your Local Machine (WSL Ubuntu):

#### 1. Make Changes Locally

```bash
cd /home/afroz/Exam-Simulator

# Activate virtual environment
source venv/bin/activate

# Make your changes
nano app.py

# Test locally
python app.py
```

#### 2. Commit and Push to GitHub

```bash
# Stage changes
git add .

# Commit changes
git commit -m "Description of changes"

# Push to GitHub
git push origin main
```

### On Your VPS:

#### 3. Pull Changes and Update

```bash
# SSH to VPS
ssh examsim@YOUR_VPS_IP

# Navigate to app directory
cd ~/exam-simulator

# Run update script
./update-from-github.sh
```

The script will:
- Backup database
- Stash local changes
- Pull from GitHub
- Update dependencies
- Run migrations
- Restart service

### Alternative: Manual Update

```bash
# Pull changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies
pip install -r requirements-production.txt --upgrade

# Restart service
sudo systemctl restart exam_simulator

# Check status
sudo systemctl status exam_simulator
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check service status
sudo systemctl status exam_simulator

# View full logs
sudo journalctl -u exam_simulator -n 100 --no-pager

# Check if port 8000 is in use
sudo ss -tlnp | grep 8000

# Test Gunicorn manually
cd /home/examsim/exam-simulator
source venv/bin/activate
gunicorn -c gunicorn_config.py wsgi:app
```

### 502 Bad Gateway

This usually means Gunicorn isn't running or web server can't connect to it.

```bash
# Check if Gunicorn is running
sudo systemctl status exam_simulator

# Check if port 8000 is accessible
curl http://127.0.0.1:8000

# Check web server error logs
# For Nginx:
sudo tail -f /var/log/nginx/error.log

# For Apache:
sudo tail -f /var/log/httpd/error_log
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R examsim:examsim /home/examsim/exam-simulator

# Fix permissions
chmod -R 755 /home/examsim/exam-simulator
chmod 600 /home/examsim/exam-simulator/.env
```

### Database Errors

```bash
# Reinitialize database
cd ~/exam-simulator
source venv/bin/activate
python init_db.py

# Or restore from backup
cp ~/backups/exam_simulator_YYYYMMDD_HHMMSS.db ~/exam-simulator/exam_simulator.db
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Check certificate expiry
sudo certbot certificates

# Test automatic renewal
sudo certbot renew --dry-run
```

### View Application Logs

```bash
# Systemd logs
sudo journalctl -u exam_simulator -f

# Application logs (if configured)
tail -f /var/log/exam_simulator/error.log

# Web server logs
# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Apache
sudo tail -f /var/log/httpd/access_log
sudo tail -f /var/log/httpd/error_log
```

### Restart Everything

```bash
# Restart application
sudo systemctl restart exam_simulator

# Restart web server
# For Nginx:
sudo systemctl restart nginx

# For Apache:
sudo systemctl restart httpd
```

---

## Useful Commands Reference

### Application Management
```bash
sudo systemctl start exam_simulator      # Start
sudo systemctl stop exam_simulator       # Stop
sudo systemctl restart exam_simulator    # Restart
sudo systemctl status exam_simulator     # Status
sudo systemctl enable exam_simulator     # Enable auto-start
sudo journalctl -u exam_simulator -f     # View live logs
```

### Update from GitHub
```bash
cd ~/exam-simulator
./update-from-github.sh
```

### Create Superadmin
```bash
cd ~/exam-simulator
source venv/bin/activate
python create_superadmin.py
```

### Database Operations
```bash
cd ~/exam-simulator
source venv/bin/activate
python init_db.py          # Initialize
python migrate_db.py       # Migrate
```

---

## Security Recommendations

1. **Use strong passwords** for all accounts
2. **Enable firewall** and only allow necessary ports
3. **Keep system updated**: `sudo dnf update -y`
4. **Use HTTPS** with valid SSL certificate
5. **Set secure SECRET_KEY** in .env
6. **Restrict SSH access** (key-based auth, disable root login)
7. **Enable fail2ban** for brute-force protection
8. **Regular backups** of database and uploads
9. **Monitor logs** for suspicious activity
10. **Use PostgreSQL or MySQL** instead of SQLite for production

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs
3. Check GitHub repository issues
4. Contact system administrator

---

**Last Updated**: October 2025
**Version**: 1.0
