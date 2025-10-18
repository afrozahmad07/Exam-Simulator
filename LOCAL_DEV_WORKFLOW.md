# Local Development Workflow Guide
## Windows PC with WSL Ubuntu 24.04 → GitHub → VPS Deployment

This guide explains the complete workflow for developing your Flask Exam Simulator application locally on your Windows PC using WSL Ubuntu 24.04, version controlling with GitHub, and deploying to your VPS.

---

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Daily Development Workflow](#daily-development-workflow)
3. [Git Workflow](#git-workflow)
4. [Deploying to VPS](#deploying-to-vps)
5. [Best Practices](#best-practices)
6. [Common Tasks](#common-tasks)
7. [Troubleshooting](#troubleshooting)

---

## Initial Setup

### 1. Set Up WSL Ubuntu (One-time)

Open PowerShell as Administrator:

```powershell
# Install WSL if not already installed
wsl --install

# Or install Ubuntu 24.04 specifically
wsl --install -d Ubuntu-24.04

# Set Ubuntu as default
wsl --set-default Ubuntu-24.04
```

Launch Ubuntu from Start Menu or:

```powershell
wsl
```

### 2. Configure Ubuntu Environment

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install development tools
sudo apt install -y git build-essential libssl-dev libffi-dev python3-dev

# Install optional tools
sudo apt install -y curl wget vim nano htop
```

### 3. Configure Git

```bash
# Set your Git identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch name
git config --global init.defaultBranch main

# Configure Git to handle line endings (Windows/Linux compatibility)
git config --global core.autocrlf input

# Optional: Set default editor
git config --global core.editor "nano"
```

### 4. Set Up SSH Key for GitHub

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"

# Press Enter to accept default location (~/.ssh/id_ed25519)
# Enter a passphrase (or leave empty)

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key to clipboard (for adding to GitHub)
cat ~/.ssh/id_ed25519.pub
```

Add the SSH key to GitHub:
1. Go to https://github.com/settings/keys
2. Click "New SSH key"
3. Paste the key and give it a title
4. Click "Add SSH key"

Test connection:

```bash
ssh -T git@github.com
# Should see: "Hi username! You've successfully authenticated..."
```

### 5. Set Up Project Directory

```bash
# Navigate to your project
cd /home/afroz/Exam-Simulator

# If starting fresh, initialize Git
git init

# Add GitHub remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin git@github.com:YOUR_USERNAME/exam-simulator.git

# If repository already exists on GitHub with files
git pull origin main

# Or if starting completely fresh
git branch -M main
git push -u origin main
```

### 6. Create Python Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# You should see (venv) in your prompt

# Install dependencies
pip install -r requirements.txt

# Or for production dependencies
pip install -r requirements-production.txt
```

### 7. Set Up Local Environment File

```bash
# Copy production template
cp .env.production .env

# Edit with your local settings
nano .env
```

Example local `.env`:

```env
# Local Development Settings
SECRET_KEY=dev-secret-key-for-local-use-only
FLASK_ENV=development
FLASK_DEBUG=True

# Local Database (SQLite is fine for development)
DATABASE_URL=sqlite:///exam_simulator.db

# API Keys (get your own for testing)
OPENAI_API_KEY=your_openai_test_key
GEMINI_API_KEY=your_gemini_test_key

# Local Settings
SESSION_COOKIE_SECURE=False
REMEMBER_COOKIE_SECURE=False
```

### 8. Initialize Local Database

```bash
# Make sure venv is activated
source venv/bin/activate

# Initialize database
python init_db.py

# Create a test superadmin
python create_superadmin.py
```

### 9. Test Local Setup

```bash
# Run the application
python app.py

# Should see:
# * Running on http://0.0.0.0:5000
```

Open browser to: http://localhost:5000

---

## Daily Development Workflow

### Morning: Start Development Session

```bash
# Open WSL Ubuntu terminal
wsl

# Navigate to project
cd /home/afroz/Exam-Simulator

# Activate virtual environment
source venv/bin/activate

# Pull latest changes from GitHub (if working on multiple machines)
git pull origin main

# Start development server
python app.py
```

### During Development

1. **Make code changes** in your preferred editor:
   - VS Code (recommended)
   - Vim/Nano in WSL
   - Windows editors (files are accessible via `\\wsl$\Ubuntu\home\afroz\Exam-Simulator`)

2. **Test changes immediately**:
   - Flask auto-reloads on file changes (in debug mode)
   - Refresh browser to see changes
   - Check terminal for errors

3. **Test features thoroughly**:
   ```bash
   # Run tests if you have them
   pytest

   # Or test manually in browser
   # Check different user roles
   # Test file uploads
   # Generate questions
   # Take exams
   ```

### Evening: Commit and Push Changes

```bash
# Check what files changed
git status

# View changes
git diff

# Stage all changes
git add .

# Or stage specific files
git add app.py templates/index.html

# Commit with descriptive message
git commit -m "Add feature: CSV question import validation"

# Push to GitHub
git push origin main

# Deactivate virtual environment
deactivate
```

---

## Git Workflow

### Basic Git Commands

```bash
# Check status
git status

# View changes
git diff                    # Unstaged changes
git diff --staged          # Staged changes

# Stage changes
git add .                  # All files
git add file.py            # Specific file
git add *.py               # All Python files

# Commit changes
git commit -m "Your message"

# Push to GitHub
git push origin main

# Pull from GitHub
git pull origin main

# View commit history
git log
git log --oneline         # Compact view
git log --graph --oneline # Visual graph
```

### Feature Branch Workflow (Recommended)

When working on a new feature:

```bash
# Create and switch to new branch
git checkout -b feature/csv-import

# Make your changes
# ...edit files...

# Stage and commit
git add .
git commit -m "Add CSV import feature"

# Push branch to GitHub
git push origin feature/csv-import

# Switch back to main
git checkout main

# Merge feature (after testing)
git merge feature/csv-import

# Push merged changes
git push origin main

# Delete feature branch
git branch -d feature/csv-import
git push origin --delete feature/csv-import
```

### Handling Conflicts

If you get a merge conflict:

```bash
# Pull with conflicts
git pull origin main

# Git will show conflicted files
# Edit files and resolve conflicts (look for <<<<<<, ======, >>>>>>)

# After resolving
git add .
git commit -m "Resolve merge conflicts"
git push origin main
```

### Useful Git Aliases

Add to `~/.gitconfig`:

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.cm commit
git config --global alias.lg "log --oneline --graph --all"
```

Now you can use:
```bash
git st      # Instead of git status
git co main # Instead of git checkout main
git lg      # Pretty log view
```

---

## Deploying to VPS

### Option 1: Using the Update Script (Recommended)

On your VPS:

```bash
# SSH to VPS
ssh examsim@YOUR_VPS_IP

# Navigate to app directory
cd ~/exam-simulator

# Run update script
./update-from-github.sh
```

That's it! The script handles everything:
- Backs up database
- Pulls latest changes
- Updates dependencies
- Restarts service
- Shows logs

### Option 2: Manual Deployment

```bash
# SSH to VPS
ssh examsim@YOUR_VPS_IP

# Navigate to app
cd ~/exam-simulator

# Pull changes
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Update dependencies (if requirements changed)
pip install -r requirements-production.txt --upgrade

# Run migrations (if database schema changed)
python migrate_db.py

# Restart service
sudo systemctl restart exam_simulator

# Check status
sudo systemctl status exam_simulator

# View logs
sudo journalctl -u exam_simulator -f
```

### Deployment Checklist

Before deploying major changes:

- [ ] Test thoroughly on local machine
- [ ] Commit all changes to git
- [ ] Push to GitHub
- [ ] Backup VPS database
- [ ] Deploy to VPS
- [ ] Test on production
- [ ] Monitor logs for errors
- [ ] Verify all features work

---

## Best Practices

### Code Organization

```
Exam-Simulator/
├── app.py                 # Main application
├── models.py              # Database models
├── utils.py               # Utility functions
├── question_generator.py  # AI question generation
├── wsgi.py               # Production WSGI entry point
├── requirements.txt       # Development dependencies
├── requirements-production.txt  # Production dependencies
├── .env                   # Local environment (not in git)
├── .env.production        # Production template (in git)
├── .gitignore            # Git ignore rules
├── templates/            # HTML templates
├── static/               # CSS, JS, images
├── uploads/              # Uploaded files (not in git)
└── venv/                 # Virtual environment (not in git)
```

### .gitignore File

Ensure these are in your `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local

# Uploads
uploads/*
!uploads/.gitkeep

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
*.swp
*.swo
```

### Environment Files

**Never commit `.env` to Git!**

Instead:
1. Commit `.env.production` as a template
2. Each environment has its own `.env` (local, staging, production)
3. Add `.env` to `.gitignore`

### Commit Messages

Use clear, descriptive commit messages:

**Good:**
```
git commit -m "Add CSV import validation for question upload"
git commit -m "Fix: Exam timer not resetting on submission"
git commit -m "Update: Improve organization settings UI"
```

**Bad:**
```
git commit -m "updates"
git commit -m "fix bug"
git commit -m "wip"
```

Format: `[Type]: [Description]`

Types:
- **Add**: New feature
- **Update**: Improve existing feature
- **Fix**: Bug fix
- **Refactor**: Code restructuring
- **Docs**: Documentation changes
- **Style**: Formatting changes
- **Test**: Add or update tests

### Testing Before Deployment

Always test locally before deploying:

```bash
# Test different scenarios
1. User registration/login
2. Document upload
3. Question generation
4. Exam taking
5. Admin panel
6. Different user roles
7. File uploads
8. PDF exports
```

---

## Common Tasks

### Adding a New Python Package

```bash
# Activate venv
source venv/bin/activate

# Install package
pip install package-name

# Update requirements file
pip freeze > requirements.txt

# Or manually add to requirements-production.txt
nano requirements-production.txt

# Commit changes
git add requirements.txt requirements-production.txt
git commit -m "Add package-name for new feature"
git push origin main
```

### Adding a New Template

```bash
# Create template
nano templates/new_page.html

# Add route in app.py
nano app.py

# Test locally
python app.py

# Commit
git add templates/new_page.html app.py
git commit -m "Add new page template"
git push origin main
```

### Updating Static Files

```bash
# Edit static files
nano static/style.css
nano static/js/app.js

# Test changes
# Refresh browser (may need hard refresh: Ctrl+Shift+R)

# Commit
git add static/
git commit -m "Update: Improve UI styling"
git push origin main
```

### Database Schema Changes

```bash
# 1. Update models.py
nano models.py

# 2. Create migration script
nano migrate_db.py

# 3. Test locally
python migrate_db.py

# 4. Test application
python app.py

# 5. Commit changes
git add models.py migrate_db.py
git commit -m "Update: Add new field to User model"
git push origin main

# 6. Deploy to VPS
ssh examsim@YOUR_VPS_IP
cd ~/exam-simulator
./update-from-github.sh
```

### Viewing Application Logs

**Local:**
```bash
# Flask outputs to terminal
python app.py
```

**Production (VPS):**
```bash
# Real-time logs
sudo journalctl -u exam_simulator -f

# Last 100 lines
sudo journalctl -u exam_simulator -n 100

# Errors only
sudo journalctl -u exam_simulator -p err

# Today's logs
sudo journalctl -u exam_simulator --since today
```

---

## Troubleshooting

### "Virtual environment not found"

```bash
# Recreate virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "Permission denied" when accessing files

```bash
# Fix permissions
chmod -R 755 /home/afroz/Exam-Simulator
```

### "Port 5000 already in use"

```bash
# Find process using port
lsof -i :5000

# Kill process
kill -9 PID

# Or use different port
python app.py --port 5001
```

### Git: "fatal: refusing to merge unrelated histories"

```bash
# Force merge (use carefully)
git pull origin main --allow-unrelated-histories
```

### Git: "Your branch has diverged"

```bash
# Option 1: Rebase (cleaner history)
git pull --rebase origin main

# Option 2: Merge
git pull origin main

# Option 3: Force push (dangerous!)
git push -f origin main  # Only if you're sure!
```

### Can't access WSL files from Windows

Access WSL files in Windows Explorer:
```
\\wsl$\Ubuntu\home\afroz\Exam-Simulator
```

Or in Command Prompt/PowerShell:
```bash
cd \\wsl$\Ubuntu\home\afroz\Exam-Simulator
```

### Python package installation fails

```bash
# Update pip
pip install --upgrade pip

# Install with --user flag
pip install --user package-name

# Install system dependencies (for some packages)
sudo apt install -y python3-dev libpq-dev
```

---

## Quick Reference

### Start Development Session
```bash
wsl
cd /home/afroz/Exam-Simulator
source venv/bin/activate
python app.py
```

### Commit and Push Changes
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

### Deploy to VPS
```bash
ssh examsim@YOUR_VPS_IP
cd ~/exam-simulator
./update-from-github.sh
```

### Check Production Logs
```bash
sudo journalctl -u exam_simulator -f
```

---

## Additional Resources

### VS Code Setup (Recommended)

1. Install VS Code on Windows
2. Install "Remote - WSL" extension
3. Open WSL folder in VS Code:
   ```bash
   # From WSL terminal
   code .
   ```
4. Install Python extension in VS Code
5. Select Python interpreter: `./venv/bin/python`

### Useful VS Code Extensions

- Python
- Pylance
- GitLens
- Remote - WSL
- SQLite Viewer
- Jinja (for templates)

### Learning Resources

- **Git**: https://git-scm.com/doc
- **Flask**: https://flask.palletsprojects.com/
- **Python**: https://docs.python.org/3/
- **WSL**: https://learn.microsoft.com/en-us/windows/wsl/

---

**Happy Coding!** 🚀

For questions or issues, refer to the main DEPLOYMENT_GUIDE.md or check the troubleshooting sections.
