# SQLite to MariaDB CI/CD - Complete Solution

## Your Question
> How will I take care of SQLite to MariaDB conversion in my CI/CD pipeline every time I push from laptop to GitHub and pull from GitHub to my VPS?

## The Answer

**You don't need to!** 🎉

Your application uses **SQLAlchemy ORM**, which means the same code works with both SQLite and MariaDB. No conversion is needed - just different database connections.

---

## How It Works

### Development (Laptop)
```env
# .env file on laptop
DATABASE_URL=sqlite:///exam_simulator.db
```
Your code → SQLAlchemy → SQLite database

### Production (VPS)
```env
# .env file on server
DATABASE_URL=mysql+pymysql://exam_user:exam123@localhost/exam_simulator
```
Your code → SQLAlchemy → MariaDB database

**Same code, different database connections!**

---

## Your Complete CI/CD Workflow

### Step 1: Develop on Laptop
```bash
cd ~/Exam-Simulator
source venv/bin/activate
flask run  # Automatically uses SQLite
```

### Step 2: Push to GitHub
```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Step 3: Deploy to Production
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

**That's it!** The deployment script automatically:
1. Pulls latest code from GitHub
2. Installs dependencies
3. Updates database schema (via migrate_db.py)
4. Restarts application
5. Uses MariaDB automatically (via .env)

---

## Files Created for You

### 1. `migrate_db.py` - Universal Database Migration
- Works with both SQLite AND MariaDB
- Safely updates schema without losing data
- Run automatically during deployment

### 2. `deploy-server.sh` - Enhanced Deployment Script
- One-command deployment from laptop
- Includes database migration
- Automatic service restart
- Status verification

### 3. `export_data.py` - Export Data from Any Database
- Exports all data to JSON
- Use when you need to move data between environments

### 4. `import_data.py` - Import Data to Any Database
- Imports JSON data to any database
- Works with both SQLite and MariaDB
- Optional: clear existing data first

### 5. `CI_CD_GUIDE.md` - Comprehensive Guide
- Complete workflow documentation
- All commands and examples
- Troubleshooting tips

### 6. `QUICK_START.md` - Quick Reference
- Simple 3-step workflow
- Common questions answered
- Quick troubleshooting

---

## What Gets Synced?

### ✅ Synced via GitHub
- Python code (.py files)
- Templates (.html files)
- Static files (CSS, JS, images)
- Requirements (requirements.txt)
- Scripts (migrate_db.py, etc.)

### ❌ NOT Synced (in .gitignore)
- `.env` files (different per environment)
- `.db` files (SQLite databases)
- Data exports (.json files)

---

## Database Schema Changes

When you modify `models.py` (add tables, columns, etc.):

### On Laptop
```bash
python migrate_db.py  # Updates SQLite schema
```

### On Server
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
# Automatically runs migrate_db.py for MariaDB
```

---

## First-Time Server Setup

Copy the deployment script to your server:

```bash
# From laptop
scp deploy-server.sh root@examsimulator.afrozahmad.com:/home/examsimulator/

# On server
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
mv /home/examsimulator/deploy-server.sh .
chmod +x deploy-server.sh
ln -sf /home/examsimulator/Exam-Simulator/deploy-server.sh /home/examsimulator/deploy.sh
```

---

## Data Sync (Advanced - Rarely Needed)

If you need to copy development data to production:

```bash
# 1. Export from laptop (SQLite)
python export_data.py

# 2. Copy to server
scp exam_data_export.json root@examsimulator.afrozahmad.com:/home/examsimulator/Exam-Simulator/

# 3. Import on server (MariaDB)
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python import_data.py
```

⚠️ **Warning:** This overwrites production data!

---

## Key Concepts

1. **No Conversion Needed**: SQLAlchemy handles database differences
2. **Code is Synced, Data is Not**: Production data stays safe
3. **Schema Changes are Safe**: migrate_db.py only adds, never deletes
4. **Environment Separation**: .env files control which database to use
5. **One-Command Deployment**: Everything automated via deploy.sh

---

## Common Questions

**Q: Do I need to export/import data every time I deploy?**
A: No! Only sync code. Data stays separate.

**Q: What if I add a new table?**
A: Just modify models.py and deploy. Schema updates automatically.

**Q: Will my local test data affect production?**
A: No! They're completely separate databases.

**Q: Do I need to install both databases?**
A: No! Laptop uses SQLite, server uses MariaDB.

---

## Quick Commands Reference

```bash
# Develop locally
cd ~/Exam-Simulator && source venv/bin/activate && flask run

# Push to GitHub
git add . && git commit -m "message" && git push

# Deploy to production (one command!)
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'

# Check production logs
ssh root@examsimulator.afrozahmad.com 'journalctl -u exam-simulator -f'

# Update schema manually on server
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python migrate_db.py
```

---

## What to Do Next

1. **First time setup:**
   ```bash
   scp deploy-server.sh root@examsimulator.afrozahmad.com:/home/examsimulator/
   ssh root@examsimulator.afrozahmad.com
   cd /home/examsimulator/Exam-Simulator
   mv /home/examsimulator/deploy-server.sh .
   chmod +x deploy-server.sh
   ln -sf /home/examsimulator/Exam-Simulator/deploy-server.sh /home/examsimulator/deploy.sh
   ```

2. **Test the deployment:**
   ```bash
   # Make a small change to your code
   git add .
   git commit -m "Test deployment"
   git push
   
   # Deploy
   ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
   ```

3. **Verify it works:**
   Visit https://examsimulator.afrozahmad.com

---

## Documentation Files

- **QUICK_START.md** - Start here for basic workflow
- **CI_CD_GUIDE.md** - Complete CI/CD documentation
- **DEPLOYMENT_GUIDE.md** - Initial server setup guide
- **SUMMARY.md** - This file (overview)

---

**Created:** October 19, 2025
**Status:** ✅ Ready to Use

The CI/CD pipeline is now set up and ready to use!
