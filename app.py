import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    # TODO: Implement user loading from database
    return None


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        # TODO: Implement login logic
        flash('Login functionality to be implemented', 'info')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        # TODO: Implement registration logic
        flash('Registration functionality to be implemented', 'info')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload study materials"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded successfully', 'success')
            return redirect(url_for('upload'))
        else:
            flash('Invalid file type. Allowed types: PDF, DOCX, TXT', 'error')

    return render_template('upload.html')


@app.route('/exam')
@login_required
def exam():
    """Take exam"""
    # TODO: Implement exam generation and display
    return render_template('exam.html')


@app.route('/results')
@login_required
def results():
    """View exam results"""
    # TODO: Implement results display
    return render_template('results.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
