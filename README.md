# Exam Simulator

AI-powered exam generation from your study materials.

## Quick Start

### First Time Setup

Run the setup script (recommended):
```bash
./setup.sh
```

This will:
- Create virtual environment
- Install all dependencies
- Initialize database with sample data
- Generate secure keys in .env file

### Starting the Application

```bash
./run.sh
```

Then visit: **http://localhost:5000**

### Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python3 init_db.py --reset --seed

# 5. Run the application
python3 app.py
```

**Important**: Always activate the virtual environment before running Python scripts:
```bash
source venv/bin/activate
```

## Demo Credentials

After running `python init_db.py --reset --seed`, you can login with:

- **Student**: `student@example.com` / `student123`
- **Teacher**: `teacher@example.com` / `teacher123`
- **Admin**: `admin@example.com` / `admin123`

## Project Structure

```
Exam-Simulator/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── init_db.py            # Database initialization script
├── requirements.txt       # Python dependencies
├── run.sh                # Startup script
├── .env                  # Environment variables
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── upload.html
│   ├── exam.html
│   └── results.html
├── static/               # Static files
│   ├── style.css
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/              # Uploaded documents
└── utils/                # Utility functions
```

## Features

- ✅ User authentication (login/register)
- ✅ Material upload (PDF, DOCX, TXT)
- 🚧 AI-powered question generation (coming soon)
- 🚧 Exam taking interface (coming soon)
- 🚧 Results tracking (coming soon)

## Environment Variables

Create a `.env` file with:

```bash
# OpenAI API Key for AI-powered exam generation
OPENAI_API_KEY=your_openai_api_key_here

# Flask Secret Key for session management
SECRET_KEY=your_secret_key_here

# Optional: Database URL (defaults to SQLite)
DATABASE_URL=sqlite:///exam_simulator.db
```

To generate a secure secret key:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

## Troubleshooting

### Templates Not Found Error

If you see `TemplateNotFound: index.html`, make sure you:

1. Are in the correct directory:
   ```bash
   cd /home/afroz/Exam-Simulator
   pwd  # Should show /home/afroz/Exam-Simulator
   ```

2. Templates folder exists:
   ```bash
   ls -la templates/
   ```

3. Restart the Flask server after any changes

### Port Already in Use

If port 5000 is already in use:
```bash
# Find and kill the process
lsof -ti:5000 | xargs kill -9

# Or run on a different port
python app.py  # Then edit app.py to change port
```

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: Bootstrap 5, Alpine.js
- **AI**: OpenAI GPT (for question generation)
- **Database**: SQLite (default) or PostgreSQL
- **Document Processing**: PyPDF2, python-docx

## License

MIT License
