# Quick Fix Guide - Apply Bug Fixes

This is a condensed guide for quickly applying the bug fixes identified during testing.

## Quick Start (SQLite - Development)

```bash
# 1. Backup database
cp exam_simulator.db exam_simulator.db.backup

# 2. Run migrations (press Enter to accept defaults)
python3 migrate_user_answer_column.py
# Select: 1 (SQLite)

python3 migrate_url_path_constraint.py
# Select: 1 (SQLite)

# 3. Restart application
python3 app.py
```

## Quick Start (MariaDB - Production)

```bash
# 1. Backup database
mysqldump -u exam_user -p exam_simulator > backup_$(date +%Y%m%d).sql

# 2. Run migrations
python3 migrate_user_answer_column.py
# Select: 2 (MariaDB)
# Enter: host, port, user, database name, password

python3 migrate_url_path_constraint.py
# Select: 2 (MariaDB)
# Enter: host, port, user, database name, password

# 3. Restart application
sudo systemctl restart exam-simulator
# OR
docker-compose restart
```

## What Was Fixed?

| Issue | Impact | Fix Location |
|-------|--------|-------------|
| SuperAdmin can't generate questions from org docs | High | `app.py:496-502` |
| Short answers truncated at 10 chars | Critical | `models.py:138` + migration |
| Multiple orgs can't have empty url_path | High | `models.py:167` + `app.py:1917-1929` + migration |
| Unclear URL validation errors | Low | `app.py:1949-1958` + template |

## Verify Fixes Work

```bash
# Test 1: SuperAdmin can access all org documents
# - Login as SuperAdmin → Content → Generate Questions on any doc

# Test 2: Short answers save correctly
# - Login as Student → Take exam → Enter 100+ char answer → Submit

# Test 3: Multiple orgs with empty url_path
# - Login as SuperAdmin → Settings → Org Branding → Leave URL Path blank → Save
# - Repeat for another org → Should work

# Test 4: URL validation helpful
# - Settings → Org Branding → Support URL: enter "example.com" → Save
# - Should show: "Must start with http:// or https://"
```

## Rollback (if needed)

### SQLite
```bash
# Restore from automatic backup
cp exam_simulator.db.backup_YYYYMMDD_HHMMSS exam_simulator.db

# OR from manual backup
cp exam_simulator.db.backup exam_simulator.db
```

### MariaDB
```bash
mysql -u exam_user -p exam_simulator < backup_YYYYMMDD.sql
```

## Files Changed

**Core files** (code changes):
- `app.py` - Permission checks, validations
- `models.py` - Database schema
- `templates/organization_settings.html` - Help text

**New files** (migration scripts):
- `migrate_user_answer_column.py`
- `migrate_url_path_constraint.py`

**Documentation**:
- `BUG_FIXES_SUMMARY.md` (detailed)
- `QUICK_FIX_GUIDE.md` (this file)

## Need Help?

See `BUG_FIXES_SUMMARY.md` for detailed information about each fix.
