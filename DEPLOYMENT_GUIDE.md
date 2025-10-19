# Exam Simulator - Deployment Guide

## Deployment Summary (Completed Today)

Successfully deployed Exam Simulator to production server at `https://examsimulator.afrozahmad.com`

**Deployment Date:** October 19, 2025
**Server:** Contabo VPS (vmi545799.contaboserver.net)
**Control Panel:** Virtualmin
**Web Server:** Apache with reverse proxy
**Application Server:** Gunicorn (3 workers)
**Database:** MariaDB
**Domain:** https://examsimulator.afrozahmad.com

---

## Architecture Overview

### Development Environment (Laptop)
- **OS:** Ubuntu on WSL (LAPTOP-QQDCPECN)
- **Python:** 3.x
- **Database:** SQLite (`exam_simulator.db`)
- **Location:** `/home/afroz/Exam-Simulator/`
- **Purpose:** Development, testing, feature creation

### Production Environment (Server)
- **OS:** AlmaLinux/CentOS
- **Python:** 3.11
- **Database:** MariaDB (`exam_simulator` database)
- **Location:** `/home/examsimulator/Exam-Simulator/`
- **Web Server:** Apache (port 80/443) → Gunicorn (port 5000)
- **Domain:** https://examsimulator.afrozahmad.com

---

## Complete Development → Production Workflow

### Daily Development Workflow (Simple 3-Step Process)

#### Step 1: Develop and Test on Laptop
```bash
# On laptop
cd ~/Exam-Simulator
source venv/bin/activate

# Make your changes to code
# Test locally: flask run
# Visit http://localhost:5000 to test
```

#### Step 2: Push to GitHub
```bash
git add .
git commit -m "Describe your changes"
git push origin main
```

#### Step 3: Deploy to Server (One Command!)
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

**That's it! Your changes are live!**

---

## Setup Deployment Script on Server (One Time)

SSH to your server and create this file:

```bash
ssh root@examsimulator.afrozahmad.com
nano /home/examsimulator/deploy.sh
```

**Paste this:**

```bash
#!/bin/bash
set -e
cd /home/examsimulator/Exam-Simulator
echo "→ Pulling latest code..."
git pull origin main
source venv/bin/activate
echo "→ Installing dependencies..."
pip install -r requirements.txt
echo "→ Restarting application..."
systemctl restart exam-simulator
echo "✓ Deployment Complete! Visit: https://examsimulator.afrozahmad.com"
```

**Make executable:**
```bash
chmod +x /home/examsimulator/deploy.sh
exit
```

**Now from your laptop, you can deploy anytime with one command!**

---

## Quick Reference Commands

### On Laptop (Development)
```bash
# Start development server
cd ~/Exam-Simulator && source venv/bin/activate && flask run

# Push to GitHub
git add . && git commit -m "Your message" && git push

# Deploy to production
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

### On Server (If needed)
```bash
# Check application status
systemctl status exam-simulator

# View logs
journalctl -u exam-simulator -f

# Restart application
systemctl restart exam-simulator

# View database
mysql -u exam_user -pexam123 exam_simulator
```

---

## Important Files

### Environment Variables (.env)

**Laptop `.env`:**
```env
DATABASE_URL=sqlite:///exam_simulator.db
FLASK_ENV=development
FLASK_DEBUG=True
GEMINI_API_KEY=your-key
```

**Server `.env`:**
```env
DATABASE_URL=mysql+pymysql://exam_user:exam123@localhost/exam_simulator
FLASK_ENV=production
FLASK_DEBUG=False
GEMINI_API_KEY=your-key
```

**⚠️ Important:** `.env` is in `.gitignore` - never pushed to GitHub!

---

## What Was Done Today

1. ✅ Installed Git, Python 3.11, dependencies on server
2. ✅ Cloned repository to `/home/examsimulator/Exam-Simulator/`
3. ✅ Created MariaDB database: `exam_simulator`
4. ✅ Configured `.env` file with MariaDB connection
5. ✅ Exported data from laptop SQLite (18 users, 101 questions, 34 exams)
6. ✅ Imported all data into server MariaDB
7. ✅ Configured Gunicorn (3 workers on port 5000)
8. ✅ Created systemd service for auto-start
9. ✅ Configured Apache reverse proxy
10. ✅ Tested and verified: https://examsimulator.afrozahmad.com

---

## Troubleshooting

### Changes not showing on website?
```bash
# Did you restart the service?
ssh root@examsimulator.afrozahmad.com 'systemctl restart exam-simulator'

# Clear browser cache (CTRL+SHIFT+R)
```

### Application not starting?
```bash
# Check logs
ssh root@examsimulator.afrozahmad.com 'journalctl -u exam-simulator -n 50'
```

### Database issues?
```bash
# Test connection
ssh root@examsimulator.afrozahmad.com 'mysql -u exam_user -pexam123 exam_simulator -e "SELECT COUNT(*) FROM users;"'
```

---

## Server Details

- **URL:** https://examsimulator.afrozahmad.com
- **SSH:** `ssh root@examsimulator.afrozahmad.com`
- **Project Path:** `/home/examsimulator/Exam-Simulator/`
- **Service:** `exam-simulator.service`
- **Database:** MariaDB `exam_simulator`
- **DB User:** `exam_user` / `exam123`

---

## Backup Database (Recommended)

```bash
# On server
ssh root@examsimulator.afrozahmad.com

# Create backup
mysqldump -u exam_user -pexam123 exam_simulator > backup_$(date +%Y%m%d).sql
```

---

**Created:** October 19, 2025  
**Status:** ✅ Production Ready
