import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai

# Import database models
from models import User, Document, Question, Exam, ExamQuestion, get_engine, get_session

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize database
db_engine = get_engine(app.config['DATABASE_URL'])

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
    db_session = get_session(db_engine)
    try:
        user = db_session.query(User).get(int(user_id))
        return user
    except:
        return None
    finally:
        db_session.close()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Please provide both email and password', 'error')
            return redirect(url_for('login'))

        db_session = get_session(db_engine)
        try:
            user = db_session.query(User).filter_by(email=email).first()

            if user and user.check_password(password):
                login_user(user)
                flash(f'Welcome back, {user.name}!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid email or password', 'error')
        finally:
            db_session.close()

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        name = request.form.get('name')
        organization = request.form.get('organization', '')
        role = request.form.get('role', 'student')

        if not email or not password or not name:
            flash('Please provide email, password, and name', 'error')
            return redirect(url_for('register'))

        db_session = get_session(db_engine)
        try:
            # Check if user already exists
            existing_user = db_session.query(User).filter_by(email=email).first()
            if existing_user:
                flash('Email already registered. Please login.', 'error')
                return redirect(url_for('login'))

            # Create new user
            new_user = User(
                email=email,
                name=name,
                organization=organization,
                role=role
            )
            new_user.set_password(password)

            db_session.add(new_user)
            db_session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db_session.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            db_session.close()

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
