# CI/CD Guide: SQLite to MariaDB Workflow

## Overview

This guide explains how to manage your development-to-production workflow with different databases.

**Development (Laptop):** SQLite
**Production (VPS):** MariaDB

## Database Strategy

Your application uses SQLAlchemy ORM, which means the **same code works with both databases**. The database type is controlled by the `DATABASE_URL` in your `.env` file.

---

## Standard Workflow (Code Changes Only)

This is the **recommended workflow** for daily development:

### 1. Develop on Laptop

```bash
cd ~/Exam-Simulator
source venv/bin/activate

# Make your code changes
# Test locally: flask run

# Your laptop uses SQLite automatically via .env:
# DATABASE_URL=sqlite:///exam_simulator.db
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### 3. Deploy to Production

```bash
# Option A: SSH and run deployment script
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'

# Option B: Run updated deployment script with migration
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy-with-migration.sh'
```

---

## Server Deployment Scripts

### Setup Enhanced Deployment Script on Server

**Step 1:** Copy the deployment script to your server:

```bash
# From your laptop, copy the script to server
scp deploy-server.sh root@examsimulator.afrozahmad.com:/home/examsimulator/
```

**Step 2:** On the server, move it to the app directory:

```bash
ssh root@examsimulator.afrozahmad.com
mv /home/examsimulator/deploy-server.sh /home/examsimulator/Exam-Simulator/
chmod +x /home/examsimulator/Exam-Simulator/deploy-server.sh
```

**Step 3:** Create a convenient shortcut (optional):

```bash
# Create a symlink in home directory for easy access
ln -sf /home/examsimulator/Exam-Simulator/deploy-server.sh /home/examsimulator/deploy.sh
```

Now you can deploy with just:
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

---

## Understanding Database Files

### Files That Are NOT Synced (in .gitignore)

```
.env                    # Environment config (different per environment)
*.db                    # SQLite database files (dev only)
*.sqlite               # SQLite database files (dev only)
exam_data_export.json  # Data export files (manual sync only)
```

### What This Means

- **Code changes** (Python files, templates, etc.) → Synced via GitHub
- **Database schema** → Applied via `migrate_db.py`
- **Database data** → Stays separate (production data protected)
- **Environment variables** → Manually configured per environment

---

## When Schema Changes Happen

If you modify `models.py` (add new tables, columns, etc.):

### On Laptop (Development)

```bash
# SQLAlchemy will auto-create new tables/columns on first run
cd ~/Exam-Simulator
source venv/bin/activate
python migrate_db.py  # Updates your local SQLite database
```

### On Server (Production)

```bash
# After pushing to GitHub and pulling on server:
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python migrate_db.py  # Updates MariaDB schema safely
systemctl restart exam-simulator
```

Or use the enhanced deployment script:
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy-with-migration.sh'
```

---

## Bug Fix Migrations (October 2025)

⚠️ **IMPORTANT:** Apply these one-time migrations to fix critical bugs identified during testing.

See `BUG_FIXES_SUMMARY.md` and `QUICK_FIX_GUIDE.md` for detailed information.

### Apply Bug Fixes

**Development (Laptop):**
```bash
cd ~/Exam-Simulator
source venv/bin/activate

# Backup first
cp exam_simulator.db exam_simulator.db.backup

# Run migrations (select option 1 for SQLite)
python3 migrate_user_answer_column.py
python3 migrate_url_path_constraint.py

# Restart app
flask run
```

**Production (Server):**
```bash
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate

# Backup first
mysqldump -u exam_user -p exam_simulator > backup_$(date +%Y%m%d).sql

# Run migrations (select option 2 for MariaDB)
python3 migrate_user_answer_column.py
python3 migrate_url_path_constraint.py

# Restart app
systemctl restart exam-simulator
```

**What These Fix:**
- SuperAdmins can now generate questions from all org documents
- Short answer responses no longer truncated at 10 characters
- Multiple organizations can have empty URL paths
- Clearer error messages for URL validation

---

## Advanced: Syncing Data Between Environments

⚠️ **WARNING:** Only do this if you need to copy development data to production!

### Export Data from Development (Laptop)

```bash
cd ~/Exam-Simulator
source venv/bin/activate
python export_data.py
# Creates: exam_data_export.json
```

### Transfer to Server

```bash
# Copy export file to server
scp exam_data_export.json root@examsimulator.afrozahmad.com:/home/examsimulator/Exam-Simulator/
```

### Import to Production (Server)

```bash
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python import_data.py  # You'll need to create this script
```

**Note:** This will overwrite production data! Use with extreme caution.

---

## Automated CI/CD with GitHub Actions (Optional)

If you want full automation, you can set up GitHub Actions:

### Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to VPS
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /home/examsimulator/Exam-Simulator
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python migrate_db.py
            systemctl restart exam-simulator
```

Setup secrets in GitHub:
- `VPS_HOST`: examsimulator.afrozahmad.com
- `VPS_USER`: root
- `SSH_PRIVATE_KEY`: Your SSH private key

---

## Quick Reference Commands

### Development (Laptop)
```bash
# Run development server
flask run

# Update database schema
python migrate_db.py

# Export data (optional)
python export_data.py

# Push to GitHub
git add . && git commit -m "message" && git push
```

### Production (Server)
```bash
# Deploy from laptop (one command!)
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'

# Check logs
ssh root@examsimulator.afrozahmad.com 'journalctl -u exam-simulator -f'

# Check database
ssh root@examsimulator.afrozahmad.com 'mysql -u exam_user -pexam123 exam_simulator -e "SHOW TABLES;"'

# Manual operations on server
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python migrate_db.py  # Run migrations manually
```

---

## Important Notes

1. **Never commit `.env` files** - They contain secrets and are environment-specific
2. **Never commit `.db` files** - Development data should stay local
3. **Always test locally first** before deploying to production
4. **Database migrations are safe** - They only add, never delete
5. **Production data is sacred** - Never overwrite without backup

---

## Troubleshooting

### Schema not updating on server?
```bash
# Check if migration ran
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python migrate_db.py
```

### Different data on dev vs production?
This is **normal and expected**! They're separate databases:
- Development: Your test data in SQLite
- Production: Real user data in MariaDB

### Need to sync specific data?
Export from source → Transfer file → Import to destination
(Use with caution!)

---

## Best Practices

✅ **DO:**
- Push code changes to GitHub regularly
- Run `migrate_db.py` after schema changes
- Test locally before deploying
- Keep production and development data separate

❌ **DON'T:**
- Commit `.env` or `.db` files
- Directly edit production database
- Overwrite production data without backup
- Skip testing in development

---

**Last Updated:** October 19, 2025
