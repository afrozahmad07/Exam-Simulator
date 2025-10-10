# Quick Start Guide

## Fix for "ModuleNotFoundError: No module named 'flask_login'"

This error occurs when you try to run `init_db.py` without activating the virtual environment first.

## Solution: Use the Correct Commands

### ❌ WRONG (This causes the error):
```bash
python init_db.py --reset --seed
# or
python3 init_db.py --reset --seed
```

### ✅ CORRECT (Use one of these methods):

#### Method 1: Run setup.sh (Recommended for first-time setup)
```bash
./setup.sh
```
This will:
- Create virtual environment
- Install all dependencies
- Initialize database with sample data
- Set up .env file

#### Method 2: Activate virtual environment first
```bash
source venv/bin/activate
python init_db.py --reset --seed
```

#### Method 3: Use run.sh
```bash
./run.sh
```
This will automatically:
- Activate virtual environment
- Check if database exists
- Prompt to create database if needed
- Start the Flask app

## Why This Happens

The `init_db.py` script needs Flask and other dependencies to run. These are installed in the virtual environment (`venv` folder), not globally. You must activate the virtual environment before running Python scripts that use these dependencies.

## Complete Setup Instructions

### First Time Setup:
```bash
cd /home/afroz/Exam-Simulator
./setup.sh
```

### Running the App:
```bash
./run.sh
```

### Reinitialize Database (if needed):
```bash
source venv/bin/activate
python3 init_db.py --reset --seed
```

### Or manually:
```bash
# Activate virtual environment
source venv/bin/activate

# Verify it's activated (you should see (venv) in your prompt)

# Now you can run any Python script
python3 init_db.py --reset --seed
python3 app.py
```

## Demo Credentials

After running setup or initializing the database with `--seed`:

- **Admin**: admin@example.com / admin123
- **Teacher**: teacher@example.com / teacher123
- **Student**: student@example.com / student123

## Access the Application

Once running, visit: **http://localhost:5000**
