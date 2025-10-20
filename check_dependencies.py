#!/usr/bin/env python3
"""
Diagnostic script to check if all required dependencies are installed
Run this on the server inside the virtual environment
"""

import sys
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print("\n" + "="*60)

dependencies = [
    ('Flask', 'flask'),
    ('SQLAlchemy', 'sqlalchemy'),
    ('Flask-Login', 'flask_login'),
    ('openai', 'openai'),
    ('PyPDF2', 'PyPDF2'),
    ('python-docx', 'docx'),
    ('python-dotenv', 'dotenv'),
    ('Werkzeug', 'werkzeug'),
    ('google-generativeai', 'google.generativeai'),
    ('pymysql', 'pymysql'),
    ('xhtml2pdf', 'xhtml2pdf'),
    ('Pillow', 'PIL'),
    ('html5lib', 'html5lib'),
    ('reportlab', 'reportlab'),
]

print("\nChecking dependencies:\n")

all_good = True
for package_name, import_name in dependencies:
    try:
        __import__(import_name)
        print(f"✅ {package_name:25s} - INSTALLED")
    except ImportError as e:
        print(f"❌ {package_name:25s} - MISSING ({str(e)})")
        all_good = False

print("\n" + "="*60)

if all_good:
    print("✅ All dependencies are installed correctly!")
else:
    print("❌ Some dependencies are missing. Run: pip install -r requirements.txt")

print("\nSpecifically testing xhtml2pdf import:")
try:
    from xhtml2pdf import pisa
    print("✅ xhtml2pdf.pisa imported successfully")
    print(f"   Version: {pisa.__version__ if hasattr(pisa, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"❌ Failed to import xhtml2pdf.pisa: {e}")
except Exception as e:
    print(f"⚠️  Import succeeded but got error: {e}")
