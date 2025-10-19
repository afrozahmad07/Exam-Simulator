# Quick Start: Development to Production Workflow

## The Simple Answer

You **DON'T need to worry** about SQLite to MariaDB conversion in your CI/CD pipeline!

### Why?

Your app uses **SQLAlchemy ORM**, which means:
- ✅ Same code works with both SQLite (dev) and MariaDB (prod)
- ✅ Database type is controlled by `.env` file only
- ✅ No conversion needed - just different connections!

---

## Your Daily Workflow (3 Steps)

### 1. Develop & Test on Laptop (SQLite)

```bash
cd ~/Exam-Simulator
source venv/bin/activate
flask run  # Test at http://localhost:5000
```

Your laptop automatically uses SQLite via `.env`:
```env
DATABASE_URL=sqlite:///exam_simulator.db
```

### 2. Push to GitHub

```bash
git add .
git commit -m "Added new feature"
git push origin main
```

### 3. Deploy to Production (MariaDB)

```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

Done! Your changes are live at https://examsimulator.afrozahmad.com

---

## What Happens During Deployment?

The `deploy.sh` script automatically:

1. ✅ Pulls latest code from GitHub
2. ✅ Installs/updates Python dependencies
3. ✅ Runs database migrations (`migrate_db.py`)
4. ✅ Restarts the application
5. ✅ Verifies it's running

The server automatically uses MariaDB via its `.env`:
```env
DATABASE_URL=mysql+pymysql://exam_user:exam123@localhost/exam_simulator
```

---

## Key Points

### Files That Are Synced (via GitHub)
- ✅ Python code (`.py` files)
- ✅ Templates (`.html` files)
- ✅ Static files (CSS, JS)
- ✅ Requirements (`requirements.txt`)
- ✅ Migration script (`migrate_db.py`)

### Files That Are NOT Synced (in `.gitignore`)
- ❌ `.env` (different per environment)
- ❌ `*.db` (SQLite databases)
- ❌ `exam_data_export.json` (data exports)

### What About Database Changes?

When you add/modify database tables in `models.py`:

**Laptop:**
```bash
python migrate_db.py  # Updates local SQLite schema
```

**Server:**
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
# The deploy script automatically runs migrate_db.py for MariaDB
```

**No data conversion needed!** Schema changes apply automatically.

---

## First-Time Setup

If you haven't set up the deployment script on your server yet:

```bash
# Copy deployment script to server
scp deploy-server.sh root@examsimulator.afrozahmad.com:/home/examsimulator/

# SSH to server and set it up
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
mv /home/examsimulator/deploy-server.sh .
chmod +x deploy-server.sh

# Create convenient shortcut
ln -sf /home/examsimulator/Exam-Simulator/deploy-server.sh /home/examsimulator/deploy.sh

exit
```

Now you can deploy anytime with:
```bash
ssh root@examsimulator.afrozahmad.com '/home/examsimulator/deploy.sh'
```

---

## Advanced: When You Need to Sync Data

**Rarely needed!** Production and development data should usually stay separate.

But if you need to copy development data to production:

### Export from Laptop (SQLite)
```bash
cd ~/Exam-Simulator
source venv/bin/activate
python export_data.py
# Creates: exam_data_export.json
```

### Copy to Server
```bash
scp exam_data_export.json root@examsimulator.afrozahmad.com:/home/examsimulator/Exam-Simulator/
```

### Import on Server (MariaDB)
```bash
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python import_data.py  # Adds data to MariaDB
# Or: python import_data.py --clear  # Replaces all data (dangerous!)
```

⚠️ **Warning:** This overwrites production data! Use with extreme caution.

---

## Common Questions

### Q: Do I need to convert SQLite to MariaDB every time I deploy?
**A:** No! Your code works with both. Just push code, pull on server, restart.

### Q: Will my local changes affect production database?
**A:** No! They're completely separate databases. Code is synced, data is not.

### Q: What if I add a new table/column?
**A:** Just modify `models.py` and deploy normally. `migrate_db.py` updates the schema.

### Q: Can I test with MariaDB locally?
**A:** Yes! Just change your laptop's `.env` to point to a local MariaDB instance.

### Q: How do I see what's in production database?
**A:**
```bash
ssh root@examsimulator.afrozahmad.com 'mysql -u exam_user -pexam123 exam_simulator'
```

---

## Troubleshooting

### Deployment not working?
```bash
# Check if deployment script exists and is executable
ssh root@examsimulator.afrozahmad.com 'ls -la /home/examsimulator/deploy.sh'

# Try running it directly on server
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
./deploy-server.sh
```

### Database schema not updating?
```bash
# Manually run migration on server
ssh root@examsimulator.afrozahmad.com
cd /home/examsimulator/Exam-Simulator
source venv/bin/activate
python migrate_db.py
systemctl restart exam-simulator
```

### Service not starting?
```bash
# Check logs
ssh root@examsimulator.afrozahmad.com 'journalctl -u exam-simulator -n 50'
```

---

## Full Documentation

For comprehensive details, see:
- **[CI_CD_GUIDE.md](CI_CD_GUIDE.md)** - Complete CI/CD workflow guide
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Initial server setup guide

---

**Last Updated:** October 19, 2025
