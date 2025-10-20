import os
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import openai

# Import database models
from models import User, Document, Question, Exam, ExamQuestion, OrganizationSettings, get_engine, get_session

# Import utility functions
from utils import (
    generate_unique_filename,
    extract_text_from_file,
    get_file_size_mb,
    validate_file_content,
    validate_question_complete,
    auto_fix_question_formatting,
    auto_fix_option_formatting,
    calculate_difficulty_score
)

# Import question generator
from question_generator import (
    generate_mcq_questions,
    generate_true_false_questions,
    generate_short_answer_questions,
    generate_questions_mixed,
    AI_MODELS
)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'txt'}
app.config['DATABASE_URL'] = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')

# Session configuration for remember me functionality
app.config['REMEMBER_COOKIE_DURATION'] = 60 * 60 * 24 * 30  # 30 days
app.config['REMEMBER_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 60 * 60 * 24 * 7  # 7 days for permanent sessions

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

# Ensure logos folder exists for organization branding
os.makedirs(os.path.join('static', 'logos'), exist_ok=True)


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def grade_short_answer(user_answer, model_answer, key_points, provider='gemini', api_key=None):
    """
    Grade a short answer using AI semantic comparison

    Args:
        user_answer: Student's answer text
        model_answer: Correct answer text
        key_points: List of key points that should be covered
        provider: AI provider ('openai' or 'gemini')
        api_key: API key for the provider

    Returns:
        tuple: (is_correct: bool, similarity_score: float, feedback: str)
    """
    if not user_answer or not user_answer.strip():
        return False, 0.0, "No answer provided"

    # Construct grading prompt
    prompt = f"""You are an exam grader. Grade the following short answer question.

Model Answer: {model_answer}

Key Points to Cover:
{chr(10).join(f'- {point}' for point in key_points) if key_points else 'N/A'}

Student's Answer: {user_answer}

Evaluate the student's answer based on:
1. Semantic similarity to the model answer
2. Coverage of key points
3. Accuracy of information
4. Completeness

Provide your response in this exact format:
SCORE: [0-100]
PASS: [YES/NO]
FEEDBACK: [Brief feedback about what was good or missing]"""

    try:
        if provider == 'gemini':
            import google.generativeai as genai
            if api_key:
                genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            result_text = response.text
        else:  # openai
            if api_key:
                client = openai.OpenAI(api_key=api_key)
            else:
                client = openai.OpenAI()

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            result_text = response.choices[0].message.content

        # Parse response
        lines = result_text.strip().split('\n')
        score = 0
        is_correct = False
        feedback = "Graded by AI"

        for line in lines:
            if line.startswith('SCORE:'):
                score = float(line.split(':')[1].strip())
            elif line.startswith('PASS:'):
                is_correct = 'YES' in line.upper()
            elif line.startswith('FEEDBACK:'):
                feedback = line.split(':', 1)[1].strip()

        # If score >= 60%, consider it correct
        if score >= 60:
            is_correct = True

        return is_correct, score, feedback

    except Exception as e:
        # Fallback: simple keyword matching
        user_lower = user_answer.lower()
        model_lower = model_answer.lower() if model_answer else ""

        # Count how many key points are mentioned
        if key_points:
            points_covered = sum(1 for point in key_points if point.lower() in user_lower)
            coverage = (points_covered / len(key_points)) * 100

            if coverage >= 50:
                return True, coverage, f"Covered {points_covered}/{len(key_points)} key points"
            else:
                return False, coverage, f"Only covered {points_covered}/{len(key_points)} key points"

        # Simple word overlap if no key points
        model_words = set(model_lower.split())
        user_words = set(user_lower.split())
        overlap = len(model_words & user_words) / len(model_words) if model_words else 0

        if overlap >= 0.3:
            return True, overlap * 100, "Partial match with model answer"
        else:
            return False, overlap * 100, "Low similarity to model answer"


# Custom decorators for role-based access control
def role_required(*roles):
    """
    Decorator to require specific roles for accessing a route
    Usage: @role_required('admin', 'teacher')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page', 'error')
                return redirect(url_for('login', next=request.url))

            if current_user.role not in roles:
                flash('You do not have permission to access this page', 'error')
                abort(403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require admin role for accessing a route
    Usage: @admin_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))

        if current_user.role not in ['admin', 'superadmin']:
            flash('Admin access required', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


def superadmin_required(f):
    """
    Decorator to require superadmin role for accessing a route
    Usage: @superadmin_required
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('login', next=request.url))

        if not current_user.is_superadmin():
            flash('Superadmin access required', 'error')
            abort(403)

        return f(*args, **kwargs)
    return decorated_function


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


@app.context_processor
def inject_org_settings():
    """Make organization settings available to all templates"""
    db_session = get_session(db_engine)
    try:
        org_settings = None

        # Try to get organization from current user
        if current_user.is_authenticated and current_user.organization:
            org_settings = db_session.query(OrganizationSettings)\
                .filter_by(organization_name=current_user.organization)\
                .first()

        # If no org settings found, try to get from subdomain or path
        if not org_settings:
            # Check subdomain
            host = request.host.split(':')[0]
            subdomain = host.split('.')[0] if '.' in host else None
            if subdomain and subdomain not in ['www', 'localhost', '127']:
                org_settings = db_session.query(OrganizationSettings)\
                    .filter_by(subdomain=subdomain)\
                    .first()

            # Check URL path
            if not org_settings and request.path.startswith('/org/'):
                path_parts = request.path.split('/')
                if len(path_parts) > 2:
                    org_path = path_parts[2]
                    org_settings = db_session.query(OrganizationSettings)\
                        .filter_by(url_path=org_path)\
                        .first()

        return {'org_settings': org_settings}
    except:
        return {'org_settings': None}
    finally:
        db_session.close()


@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login with session management and remember me functionality"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)  # Remember me checkbox

        if not email or not password:
            flash('Please provide both email and password', 'error')
            return redirect(url_for('login'))

        db_session = get_session(db_engine)
        try:
            user = db_session.query(User).filter_by(email=email).first()

            if user and user.check_password(password):
                # Login user with remember me option
                login_user(user, remember=bool(remember))

                # Make session permanent if remember me is checked
                if remember:
                    session.permanent = True

                flash(f'Welcome back, {user.name}!', 'success')

                # Redirect to next page or index
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
    """Upload study materials with text extraction and database storage"""
    if request.method == 'POST':
        print("=== UPLOAD STARTED ===")

        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not file or not allowed_file(file.filename):
            flash('Invalid file type. Allowed types: PDF, DOCX, TXT', 'error')
            return redirect(request.url)

        # Generate unique filename and save file
        original_filename = secure_filename(file.filename)
        unique_filename = generate_unique_filename(original_filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        print(f"Processing file: {original_filename}")

        try:
            # Save the file
            print("Saving file...")
            file.save(file_path)
            print(f"✓ File saved to: {file_path}")

            # Get file size for logging
            file_size_mb = get_file_size_mb(file_path)
            print(f"File size: {file_size_mb} MB")

            # Extract text content from the file (with timeout protection)
            print("Extracting text...")
            try:
                text_content = extract_text_from_file(file_path)
                print(f"✓ Extracted {len(text_content)} characters")
            except Exception as extract_error:
                print(f"✗ Extraction error: {extract_error}")
                os.remove(file_path)
                flash(f'Error extracting text from file: {str(extract_error)}. Please ensure the file is not corrupted.', 'error')
                return redirect(request.url)

            # Validate extracted content
            print("Validating content...")
            if not validate_file_content(text_content):
                print("✗ Content validation failed")
                os.remove(file_path)  # Remove file if content is invalid
                flash('File appears to be empty or unreadable. Please upload a valid document with text content.', 'error')
                return redirect(request.url)
            print("✓ Content validated")

            # Store document in database
            print("Saving to database...")
            db_session = get_session(db_engine)
            try:
                new_document = Document(
                    filename=original_filename,
                    content=text_content,
                    uploaded_by=current_user.id,
                    organization=current_user.organization
                )
                db_session.add(new_document)
                db_session.commit()
                print("✓ Document saved to database")

                flash(f'File "{original_filename}" uploaded and processed successfully!', 'success')
                print("=== UPLOAD COMPLETE ===")
                return redirect(url_for('documents'))
            except Exception as e:
                print(f"✗ Database error: {e}")
                db_session.rollback()
                os.remove(file_path)  # Remove file if database insert fails
                flash(f'Error saving document: {str(e)}', 'error')
            finally:
                db_session.close()

        except Exception as e:
            # Clean up file if anything goes wrong
            print(f"✗ General error: {e}")
            if os.path.exists(file_path):
                os.remove(file_path)
            flash(f'Error processing file: {str(e)}', 'error')

    return render_template('upload.html')


@app.route('/documents')
@login_required
def documents():
    """Display list of uploaded documents (organization-wide for students/teachers)"""
    db_session = get_session(db_engine)
    try:
        # Students and teachers can see all documents in their organization
        # This allows them to access study materials uploaded by teachers
        if current_user.organization:
            user_documents = db_session.query(Document)\
                .filter_by(organization=current_user.organization)\
                .order_by(Document.created_at.desc())\
                .all()
        else:
            # Users without organization see only their own documents
            user_documents = db_session.query(Document)\
                .filter_by(uploaded_by=current_user.id)\
                .order_by(Document.created_at.desc())\
                .all()

        return render_template('documents.html', documents=user_documents)
    finally:
        db_session.close()


@app.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View document content and details (accessible to organization members)"""
    db_session = get_session(db_engine)
    try:
        # Get document and verify ownership
        document = db_session.query(Document).get(document_id)

        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('documents'))

        # Check if user has access to this document
        # Users can access documents in their organization or their own documents
        has_access = (
            document.uploaded_by == current_user.id or
            (current_user.organization and document.organization == current_user.organization) or
            current_user.is_superadmin()
        )

        if not has_access:
            flash('You do not have permission to view this document', 'error')
            return redirect(url_for('documents'))

        # Get questions generated from this document (if any)
        questions = db_session.query(Question)\
            .filter_by(document_id=document_id)\
            .all()

        return render_template('view_document.html',
                               document=document,
                               questions=questions,
                               question_count=len(questions))
    finally:
        db_session.close()


@app.route('/document/<int:document_id>/delete', methods=['POST'])
@login_required
def delete_document(document_id):
    """Delete a document and its associated data"""
    db_session = get_session(db_engine)
    try:
        # Get document and verify ownership
        document = db_session.query(Document).get(document_id)

        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('documents'))

        # Check if user owns this document
        if document.uploaded_by != current_user.id:
            flash('You do not have permission to delete this document', 'error')
            return redirect(url_for('documents'))

        # Store filename for success message
        filename = document.filename

        # Delete the document (cascade will handle related questions)
        db_session.delete(document)
        db_session.commit()

        flash(f'Document "{filename}" deleted successfully', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error deleting document: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('documents'))


@app.route('/generate-questions/<int:document_id>', methods=['GET', 'POST'])
@login_required
def generate_questions(document_id):
    """Generate questions from a document using AI"""
    db_session = get_session(db_engine)
    try:
        # Get document and verify ownership
        document = db_session.query(Document).get(document_id)

        if not document:
            flash('Document not found', 'error')
            return redirect(url_for('documents'))

        # Check if user owns this document or is a superadmin/admin with org access
        is_superadmin = current_user.is_superadmin()
        is_org_admin = current_user.is_org_admin() and current_user.organization == document.organization

        if not (document.uploaded_by == current_user.id or is_superadmin or is_org_admin):
            flash('You do not have permission to access this document', 'error')
            return redirect(url_for('documents'))

        if request.method == 'POST':
            num_mcq = request.form.get('num_mcq', 0, type=int)
            num_true_false = request.form.get('num_true_false', 0, type=int)
            num_short_answer = request.form.get('num_short_answer', 0, type=int)

            total_questions = num_mcq + num_true_false + num_short_answer

            if total_questions == 0:
                flash('Please specify at least one question to generate', 'error')
                return redirect(url_for('generate_questions', document_id=document_id))

            if total_questions > 50:
                flash('Maximum 50 questions can be generated at once', 'error')
                return redirect(url_for('generate_questions', document_id=document_id))

            try:
                # Get user's AI preferences (teachers/admins can customize, students use default)
                provider = current_user.ai_provider or 'gemini'
                model = current_user.ai_model or 'gemini-2.5-flash'

                # Get organization's API keys if available
                openai_key = None
                gemini_key = None

                if current_user.organization:
                    org_settings = db_session.query(OrganizationSettings)\
                        .filter_by(organization_name=current_user.organization)\
                        .first()

                    if org_settings:
                        openai_key = org_settings.openai_api_key
                        gemini_key = org_settings.gemini_api_key

                # Generate mixed questions using user's preferred AI with organization API keys
                results = generate_questions_mixed(
                    text=document.content,
                    num_mcq=num_mcq,
                    num_true_false=num_true_false,
                    num_short_answer=num_short_answer,
                    model=model,
                    provider=provider,
                    openai_api_key=openai_key,
                    gemini_api_key=gemini_key
                )

                # Store generated questions in session for review
                session['generated_questions'] = {
                    'mcq': results.get('mcq', []),
                    'true_false': results.get('true_false', []),
                    'short_answer': results.get('short_answer', []),
                    'document_id': document_id
                }

                if results.get('errors'):
                    for error in results['errors']:
                        flash(error, 'warning')

                total_generated = len(results.get('mcq', [])) + len(results.get('true_false', [])) + len(results.get('short_answer', []))

                if total_generated > 0:
                    flash(f'Successfully generated {total_generated} questions! Please review and approve.', 'success')
                    return redirect(url_for('review_questions'))
                else:
                    flash('No questions were generated. Please try again.', 'error')

            except Exception as e:
                flash(f'Error generating questions: {str(e)}', 'error')

        return render_template('generate_questions.html', document=document)
    finally:
        db_session.close()


@app.route('/review-questions', methods=['GET', 'POST'])
@login_required
def review_questions():
    """Review and edit generated questions before saving"""
    if 'generated_questions' not in session:
        flash('No questions to review. Please generate questions first.', 'warning')
        return redirect(url_for('documents'))

    generated_data = session['generated_questions']

    db_session = get_session(db_engine)
    try:
        document = db_session.query(Document).get(generated_data['document_id'])

        if not document or document.uploaded_by != current_user.id:
            flash('Invalid document access', 'error')
            return redirect(url_for('documents'))

        return render_template('review_questions.html',
                             questions=generated_data,
                             document=document)
    finally:
        db_session.close()


@app.route('/save-questions', methods=['POST'])
@login_required
def save_questions():
    """Save approved questions to database"""
    if 'generated_questions' not in session:
        flash('No questions to save', 'error')
        return redirect(url_for('documents'))

    db_session = get_session(db_engine)
    try:
        generated_data = session['generated_questions']
        document_id = generated_data['document_id']

        # Verify document ownership
        document = db_session.query(Document).get(document_id)
        if not document or document.uploaded_by != current_user.id:
            flash('Invalid document access', 'error')
            return redirect(url_for('documents'))

        # Get approved question IDs from form
        approved_ids = request.form.getlist('approved')

        if not approved_ids:
            flash('No questions selected for approval', 'warning')
            return redirect(url_for('review_questions'))

        saved_count = 0
        validation_errors = []

        # Get existing questions for duplicate detection
        existing_questions_obj = db_session.query(Question).filter_by(document_id=document_id).all()
        existing_question_texts = [q.question_text for q in existing_questions_obj]

        # Process MCQ questions
        for idx, q in enumerate(generated_data.get('mcq', [])):
            question_id = f'mcq_{idx}'
            if question_id in approved_ids:
                # Get edited values from form
                question_text = request.form.get(f'{question_id}_question', q['question'])
                option_a = request.form.get(f'{question_id}_option_A', q['options'].get('A', ''))
                option_b = request.form.get(f'{question_id}_option_B', q['options'].get('B', ''))
                option_c = request.form.get(f'{question_id}_option_C', q['options'].get('C', ''))
                option_d = request.form.get(f'{question_id}_option_D', q['options'].get('D', ''))
                correct_answer = request.form.get(f'{question_id}_correct', q['correct_answer'])
                explanation = request.form.get(f'{question_id}_explanation', q.get('explanation', ''))

                # Build options dict
                options = {'A': option_a, 'B': option_b, 'C': option_c, 'D': option_d}

                # Validate and auto-fix
                is_valid, errors, fixed_data = validate_question_complete(
                    question_text=question_text,
                    question_type='mcq',
                    correct_answer=correct_answer,
                    options=options,
                    existing_questions=existing_question_texts,
                    auto_fix=True
                )

                if not is_valid:
                    validation_errors.append(f"MCQ Question {idx + 1}: {', '.join(errors)}")
                    continue

                # Use fixed data
                new_question = Question(
                    question_text=fixed_data['question_text'],
                    question_type='mcq',
                    options_json=fixed_data['options'],
                    correct_answer=correct_answer,
                    explanation=explanation,
                    document_id=document_id,
                    difficulty=fixed_data['difficulty'],
                    status='approved',
                    created_by=current_user.id
                )
                db_session.add(new_question)
                existing_question_texts.append(fixed_data['question_text'])
                saved_count += 1

        # Process True/False questions
        for idx, q in enumerate(generated_data.get('true_false', [])):
            question_id = f'tf_{idx}'
            if question_id in approved_ids:
                question_text = request.form.get(f'{question_id}_question', q['question'])
                correct_answer = request.form.get(f'{question_id}_correct', str(q['correct_answer']).lower())
                explanation = request.form.get(f'{question_id}_explanation', q.get('explanation', ''))

                # Validate and auto-fix
                is_valid, errors, fixed_data = validate_question_complete(
                    question_text=question_text,
                    question_type='true_false',
                    correct_answer=correct_answer,
                    existing_questions=existing_question_texts,
                    auto_fix=True
                )

                if not is_valid:
                    validation_errors.append(f"True/False Question {idx + 1}: {', '.join(errors)}")
                    continue

                new_question = Question(
                    question_text=fixed_data['question_text'],
                    question_type='true_false',
                    options_json=None,  # True/False questions don't have options
                    correct_answer=correct_answer,
                    model_answer=None,
                    key_points=None,
                    explanation=explanation,
                    document_id=document_id,
                    difficulty=fixed_data['difficulty'],
                    status='approved',
                    created_by=current_user.id
                )
                db_session.add(new_question)
                existing_question_texts.append(fixed_data['question_text'])
                saved_count += 1

        # Process Short Answer questions
        for idx, q in enumerate(generated_data.get('short_answer', [])):
            question_id = f'sa_{idx}'
            if question_id in approved_ids:
                question_text = request.form.get(f'{question_id}_question', q['question'])
                model_answer = request.form.get(f'{question_id}_model_answer', q.get('model_answer', ''))

                # Get key points (assuming they're submitted as a textarea with newlines)
                key_points_text = request.form.get(f'{question_id}_key_points', '')
                if key_points_text:
                    key_points = [kp.strip() for kp in key_points_text.split('\n') if kp.strip()]
                else:
                    key_points = q.get('key_points', [])

                # Validate and auto-fix
                is_valid, errors, fixed_data = validate_question_complete(
                    question_text=question_text,
                    question_type='short_answer',
                    existing_questions=existing_question_texts,
                    auto_fix=True
                )

                if not is_valid:
                    validation_errors.append(f"Short Answer Question {idx + 1}: {', '.join(errors)}")
                    continue

                new_question = Question(
                    question_text=fixed_data['question_text'],
                    question_type='short_answer',
                    model_answer=model_answer,
                    key_points=key_points,
                    document_id=document_id,
                    difficulty=fixed_data['difficulty'],
                    status='approved',
                    created_by=current_user.id
                )
                db_session.add(new_question)
                existing_question_texts.append(fixed_data['question_text'])
                saved_count += 1

        # Show validation errors if any
        if validation_errors:
            for error in validation_errors:
                flash(error, 'warning')

        if saved_count == 0:
            flash('No questions were saved due to validation errors. Please fix the issues and try again.', 'error')
            return redirect(url_for('review_questions'))

        db_session.commit()

        # Clear session data
        session.pop('generated_questions', None)

        flash(f'Successfully saved {saved_count} approved questions!', 'success')
        if validation_errors:
            flash(f'{len(validation_errors)} questions were skipped due to validation errors.', 'warning')

        return redirect(url_for('question_bank'))

    except Exception as e:
        db_session.rollback()
        flash(f'Error saving questions: {str(e)}', 'error')
        return redirect(url_for('review_questions'))
    finally:
        db_session.close()


@app.route('/question-bank')
@login_required
def question_bank():
    """Display all approved questions (organization-wide)"""
    db_session = get_session(db_engine)
    try:
        # Get filter parameters
        document_id = request.args.get('document_id', type=int)
        question_type = request.args.get('type')
        status = request.args.get('status', 'approved')

        # Build query - show all questions from organization's documents
        if current_user.organization:
            # Users with organization see all questions from their organization
            query = db_session.query(Question).join(Document).filter(
                Document.organization == current_user.organization
            )
        else:
            # Users without organization see only their own questions
            query = db_session.query(Question).join(Document).filter(
                Document.uploaded_by == current_user.id
            )

        if document_id:
            query = query.filter(Question.document_id == document_id)

        if question_type:
            query = query.filter(Question.question_type == question_type)

        if status:
            query = query.filter(Question.status == status)

        questions = query.order_by(Question.created_at.desc()).all()

        # Get organization's documents for filter dropdown
        if current_user.organization:
            documents = db_session.query(Document).filter_by(
                organization=current_user.organization
            ).all()
        else:
            documents = db_session.query(Document).filter_by(
                uploaded_by=current_user.id
            ).all()

        # Count by type
        total_mcq = db_session.query(Question).join(Document).filter(
            Document.uploaded_by == current_user.id,
            Question.question_type == 'mcq',
            Question.status == 'approved'
        ).count()

        total_tf = db_session.query(Question).join(Document).filter(
            Document.uploaded_by == current_user.id,
            Question.question_type == 'true_false',
            Question.status == 'approved'
        ).count()

        total_sa = db_session.query(Question).join(Document).filter(
            Document.uploaded_by == current_user.id,
            Question.question_type == 'short_answer',
            Question.status == 'approved'
        ).count()

        return render_template('question_bank.html',
                             questions=questions,
                             documents=documents,
                             total_mcq=total_mcq,
                             total_tf=total_tf,
                             total_sa=total_sa,
                             selected_document=document_id,
                             selected_type=question_type,
                             selected_status=status)
    finally:
        db_session.close()


@app.route('/question/<int:question_id>/delete', methods=['POST'])
@login_required
def delete_question(question_id):
    """Delete a question"""
    db_session = get_session(db_engine)
    try:
        question = db_session.query(Question).get(question_id)

        if not question:
            flash('Question not found', 'error')
            return redirect(url_for('question_bank'))

        # Verify ownership through document
        if question.document.uploaded_by != current_user.id:
            flash('You do not have permission to delete this question', 'error')
            return redirect(url_for('question_bank'))

        db_session.delete(question)
        db_session.commit()

        flash('Question deleted successfully', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error deleting question: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('question_bank'))


@app.route('/exam', methods=['GET', 'POST'])
@login_required
def exam():
    """Take exam - select document and generate questions"""
    db_session = get_session(db_engine)
    try:
        # Check if there's an active exam session
        if 'exam_id' in session and 'exam_questions' in session:
            exam_id = session.get('exam_id')
            exam = db_session.query(Exam).get(exam_id)

            # If exam exists and is not completed, redirect to continue it
            if exam and not exam.is_completed():
                flash('You have an exam in progress. Continue where you left off.', 'info')
                return redirect(url_for('start_exam'))

        # Get user's documents
        user_documents = db_session.query(Document)\
            .filter_by(uploaded_by=current_user.id)\
            .order_by(Document.created_at.desc())\
            .all()

        # Count questions for each document
        for doc in user_documents:
            doc.question_count = db_session.query(Question)\
                .filter_by(document_id=doc.id, status='approved')\
                .count()

        if request.method == 'POST':
            document_id = request.form.get('document_id')
            num_questions = request.form.get('num_questions', 10, type=int)
            difficulty = request.form.get('difficulty', 'all')

            if not document_id:
                flash('Please select a document', 'error')
                return redirect(url_for('exam'))

            # Get questions from selected document
            query = db_session.query(Question)\
                .filter_by(document_id=document_id, status='approved')

            if difficulty != 'all':
                query = query.filter_by(difficulty=difficulty)

            # Get all matching questions
            all_questions = query.all()

            if not all_questions:
                flash('No questions available for this document. Please generate questions first.', 'warning')
                return redirect(url_for('exam'))

            # Random selection using a seed for reproducibility
            import random
            num_questions = min(num_questions, len(all_questions))

            # Create a seed based on user ID and timestamp for uniqueness
            random_seed = int(current_user.id * 1000 + datetime.utcnow().timestamp() % 1000)
            random.seed(random_seed)
            selected_questions = random.sample(all_questions, num_questions)
            random.seed()  # Reset to system time

            # Create exam record in database (in progress)
            new_exam = Exam(
                user_id=current_user.id,
                total_questions=num_questions,
                completed_at=None  # Not completed yet
            )
            db_session.add(new_exam)
            db_session.flush()  # Get exam ID

            # Store exam session data
            session['exam_id'] = new_exam.id
            session['exam_questions'] = [q.id for q in selected_questions]
            session['exam_document_id'] = int(document_id)
            session['exam_start_time'] = datetime.utcnow().isoformat()
            session['exam_duration'] = 30  # 30 minutes default
            session['exam_answers'] = {}  # Store user answers
            session['question_times'] = {}  # Track time per question
            session['question_start_time'] = None  # Track current question start time

            db_session.commit()

            return redirect(url_for('start_exam'))

        return render_template('exam.html', documents=user_documents)
    finally:
        db_session.close()


@app.route('/start-exam')
@login_required
def start_exam():
    """Start taking the exam (handles browser refresh)"""
    # Check if exam session exists
    if 'exam_questions' not in session or 'exam_id' not in session:
        flash('No active exam session. Please start a new exam.', 'warning')
        return redirect(url_for('exam'))

    db_session = get_session(db_engine)
    try:
        exam_id = session.get('exam_id')
        exam = db_session.query(Exam).get(exam_id)

        # Check if exam is already completed
        if exam and exam.is_completed():
            flash('This exam has already been completed.', 'warning')
            session.pop('exam_id', None)
            session.pop('exam_questions', None)
            session.pop('exam_answers', None)
            session.pop('exam_start_time', None)
            session.pop('exam_duration', None)
            session.pop('question_times', None)
            session.pop('submission_failed', None)
            session.pop('submission_error', None)
            return redirect(url_for('exam_results', exam_id=exam.id))

        # Check if submission has failed previously (infinite loop prevention)
        if session.get('submission_failed'):
            submission_error = session.get('submission_error', 'Unknown error')
            session.pop('submission_failed', None)
            session.pop('submission_error', None)

            # Show helpful error message
            if 'Data too long' in submission_error or '1406' in submission_error:
                flash('Database migration required: Your answer is too long. Please contact support to run: python3 migrate_user_answer_column.py', 'error')
            else:
                flash(f'Previous submission failed: {submission_error}. Please try again or contact support.', 'error')

        # Get questions for the exam
        question_ids = session.get('exam_questions', [])
        questions = db_session.query(Question).filter(Question.id.in_(question_ids)).all()

        if not questions:
            flash('No questions found. Please start a new exam.', 'error')
            return redirect(url_for('exam'))

        # Sort questions by their order in session
        questions_dict = {q.id: q for q in questions}
        ordered_questions = [questions_dict[qid] for qid in question_ids if qid in questions_dict]

        # Get exam metadata
        start_time = session.get('exam_start_time')
        duration = session.get('exam_duration', 30)
        user_answers = session.get('exam_answers', {})
        question_times = session.get('question_times', {})

        return render_template('take_exam.html',
                             questions=ordered_questions,
                             start_time=start_time,
                             duration=duration,
                             user_answers=user_answers,
                             question_times=question_times,
                             total_questions=len(ordered_questions),
                             exam_id=exam_id)
    finally:
        db_session.close()


@app.route('/save-answer', methods=['POST'])
@login_required
def save_answer():
    """Save user answer via AJAX with time tracking"""
    question_id = request.json.get('question_id')
    answer = request.json.get('answer')
    time_spent = request.json.get('time_spent', 0)  # Time in seconds

    if not question_id:
        return jsonify({'success': False, 'message': 'Question ID required'}), 400

    # Initialize exam_answers if not exists
    if 'exam_answers' not in session:
        session['exam_answers'] = {}

    if 'question_times' not in session:
        session['question_times'] = {}

    # Save answer and time to session
    session['exam_answers'][str(question_id)] = answer
    session['question_times'][str(question_id)] = time_spent
    session.modified = True

    return jsonify({'success': True, 'message': 'Answer saved', 'time_spent': time_spent})


@app.route('/submit-exam', methods=['POST'])
@login_required
def submit_exam():
    """Submit exam and calculate results with detailed statistics"""
    # Check if exam session exists
    if 'exam_questions' not in session or 'exam_id' not in session:
        flash('No active exam session.', 'error')
        return redirect(url_for('exam'))

    db_session = get_session(db_engine)
    try:
        exam_id = session.get('exam_id')
        question_ids = session.get('exam_questions', [])
        user_answers = session.get('exam_answers', {})
        question_times = session.get('question_times', {})
        start_time = datetime.fromisoformat(session.get('exam_start_time'))

        # Get the existing exam record
        exam = db_session.query(Exam).get(exam_id)

        if not exam:
            flash('Exam record not found.', 'error')
            return redirect(url_for('exam'))

        # Check if already completed (prevent double submission)
        if exam.is_completed():
            flash('This exam has already been submitted.', 'warning')
            return redirect(url_for('exam_results', exam_id=exam.id))

        # Get questions
        questions = db_session.query(Question).filter(Question.id.in_(question_ids)).all()
        questions_dict = {q.id: q for q in questions}

        # Process each question and save results
        correct_count = 0
        unanswered_count = 0

        for question_id in question_ids:
            question = questions_dict.get(question_id)
            if not question:
                continue

            user_answer = user_answers.get(str(question_id))
            time_spent = question_times.get(str(question_id), 0)

            # Check if answer is correct
            is_correct = False
            if user_answer:
                if question.question_type == 'true_false':
                    is_correct = user_answer.lower() == question.correct_answer.lower()
                elif question.question_type == 'short_answer':
                    # Use AI-based grading for short answers
                    try:
                        # Get organization's API key if available
                        org_api_key = None
                        provider = current_user.ai_provider or 'gemini'

                        if current_user.organization:
                            org_settings = db_session.query(OrganizationSettings)\
                                .filter_by(organization_name=current_user.organization)\
                                .first()
                            if org_settings:
                                org_api_key = org_settings.gemini_api_key if provider == 'gemini' else org_settings.openai_api_key

                        is_correct, score, feedback = grade_short_answer(
                            user_answer=user_answer,
                            model_answer=question.model_answer,
                            key_points=question.key_points,
                            provider=provider,
                            api_key=org_api_key
                        )
                    except Exception as e:
                        # Fallback to marking as incorrect if AI grading fails
                        is_correct = False
                else:  # MCQ
                    is_correct = user_answer == question.correct_answer
            else:
                unanswered_count += 1

            if is_correct:
                correct_count += 1

            # Create exam question record with time tracking
            exam_question = ExamQuestion(
                exam_id=exam.id,
                question_id=question_id,
                user_answer=user_answer,
                is_correct=is_correct,
                time_spent=time_spent
            )
            db_session.add(exam_question)

        # Calculate score and update exam
        exam.score = (correct_count / len(question_ids) * 100) if question_ids else 0
        exam.completed_at = datetime.utcnow()

        db_session.commit()

        # Clear exam session
        session.pop('exam_id', None)
        session.pop('exam_questions', None)
        session.pop('exam_document_id', None)
        session.pop('exam_start_time', None)
        session.pop('exam_duration', None)
        session.pop('exam_answers', None)
        session.pop('question_times', None)
        session.pop('question_start_time', None)

        # Success message with statistics
        message = f'Exam submitted! Score: {exam.score:.1f}% ({correct_count}/{len(question_ids)} correct'
        if unanswered_count > 0:
            message += f', {unanswered_count} unanswered'
        message += ')'

        flash(message, 'success')
        return redirect(url_for('exam_results', exam_id=exam.id))

    except Exception as e:
        db_session.rollback()

        # Check if this is a database schema error (data too long, etc.)
        error_msg = str(e)
        if 'Data too long' in error_msg or '1406' in error_msg:
            flash('Database error: Please contact support. Your answers may be too long for the database schema. Run database migrations to fix this issue.', 'error')
        elif 'IntegrityError' in error_msg or 'Duplicate entry' in error_msg:
            flash('Database integrity error: Please contact support to resolve database constraint issues.', 'error')
        else:
            flash(f'Error submitting exam: {error_msg}', 'error')

        # Store submission attempt flag to prevent infinite loops
        session['submission_failed'] = True
        session['submission_error'] = error_msg

        # If time has expired and submission is failing, mark exam as completed anyway
        # to prevent infinite loop, but with a note
        try:
            exam = db_session.query(Exam).get(exam_id)
            if exam and not exam.is_completed():
                # Check if time has truly expired
                start_time_dt = datetime.fromisoformat(session.get('exam_start_time'))
                exam_duration = session.get('exam_duration', 30)
                time_elapsed = (datetime.utcnow() - start_time_dt).total_seconds() / 60

                if time_elapsed >= exam_duration:
                    # Time expired - mark as completed with error state
                    exam.completed_at = datetime.utcnow()
                    exam.score = 0.0  # Mark as 0 due to submission error
                    db_session.commit()

                    # Clear session to prevent reloading
                    session.pop('exam_id', None)
                    session.pop('exam_questions', None)
                    session.pop('exam_document_id', None)
                    session.pop('exam_start_time', None)
                    session.pop('exam_duration', None)
                    session.pop('exam_answers', None)
                    session.pop('question_times', None)
                    session.pop('question_start_time', None)

                    flash('Your exam time has expired. Due to a technical error, your answers could not be saved. Please contact support.', 'warning')
                    return redirect(url_for('exam'))
        except:
            pass  # If this fails, fall through to normal error handling

        return redirect(url_for('start_exam'))
    finally:
        db_session.close()


@app.route('/exam-results/<int:exam_id>')
@login_required
def exam_results(exam_id):
    """View detailed exam results"""
    db_session = get_session(db_engine)
    try:
        # Get exam and verify ownership
        exam = db_session.query(Exam).get(exam_id)

        if not exam:
            flash('Exam not found', 'error')
            return redirect(url_for('results'))

        if exam.user_id != current_user.id:
            flash('You do not have permission to view this exam', 'error')
            return redirect(url_for('results'))

        # Get exam questions with details
        exam_questions = db_session.query(ExamQuestion)\
            .filter_by(exam_id=exam_id)\
            .all()

        return render_template('exam_results.html',
                             exam=exam,
                             exam_questions=exam_questions)
    finally:
        db_session.close()


@app.route('/exam/<int:exam_id>/download-pdf')
@login_required
def download_exam_pdf(exam_id):
    """Download exam results as PDF"""
    from io import BytesIO
    try:
        from xhtml2pdf import pisa
    except ImportError:
        flash('PDF generation not available. Please install xhtml2pdf: pip install xhtml2pdf', 'error')
        return redirect(url_for('exam_results', exam_id=exam_id))

    db_session = get_session(db_engine)
    try:
        # Get exam and verify ownership
        exam = db_session.query(Exam).get(exam_id)

        if not exam:
            flash('Exam not found', 'error')
            return redirect(url_for('results'))

        if exam.user_id != current_user.id:
            flash('You do not have permission to download this exam', 'error')
            return redirect(url_for('results'))

        # Get exam questions with details
        exam_questions = db_session.query(ExamQuestion)\
            .filter_by(exam_id=exam_id)\
            .all()

        # Calculate statistics
        correct_count = sum(1 for eq in exam_questions if eq.is_correct)
        wrong_count = len(exam_questions) - correct_count
        total_time = sum(eq.time_spent or 0 for eq in exam_questions)
        avg_time = total_time / len(exam_questions) if exam_questions else 0

        # Render HTML template for PDF
        html_content = render_template('exam_results_pdf.html',
                                     exam=exam,
                                     exam_questions=exam_questions,
                                     user=current_user,
                                     correct_count=correct_count,
                                     wrong_count=wrong_count,
                                     total_time=total_time,
                                     avg_time=avg_time)

        # Generate PDF
        pdf_buffer = BytesIO()
        pisa_status = pisa.CreatePDF(BytesIO(html_content.encode('utf-8')), dest=pdf_buffer)

        if pisa_status.err:
            flash('Error generating PDF', 'error')
            return redirect(url_for('exam_results', exam_id=exam_id))

        # Prepare response
        pdf_buffer.seek(0)
        from flask import send_file
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'exam_results_{exam_id}_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('exam_results', exam_id=exam_id))
    finally:
        db_session.close()


@app.route('/results')
@login_required
def results():
    """View all exam results"""
    db_session = get_session(db_engine)
    try:
        # Get all exams for current user
        user_exams = db_session.query(Exam)\
            .filter_by(user_id=current_user.id)\
            .filter(Exam.completed_at.isnot(None))\
            .order_by(Exam.completed_at.desc())\
            .all()

        # Calculate statistics
        total_exams = len(user_exams)
        avg_score = sum(exam.score for exam in user_exams) / total_exams if total_exams > 0 else 0
        best_score = max((exam.score for exam in user_exams), default=0)
        recent_exams = user_exams[:10]  # Last 10 exams

        return render_template('results.html',
                             exams=recent_exams,
                             total_exams=total_exams,
                             avg_score=avg_score,
                             best_score=best_score)
    finally:
        db_session.close()


@app.route('/analytics')
@login_required
def analytics():
    """Analytics dashboard with exam history and statistics"""
    db_session = get_session(db_engine)
    try:
        # Get all completed exams for current user
        user_exams = db_session.query(Exam)\
            .filter_by(user_id=current_user.id)\
            .filter(Exam.completed_at.isnot(None))\
            .order_by(Exam.completed_at.desc())\
            .all()

        # Calculate basic statistics
        total_exams = len(user_exams)
        avg_score = sum(exam.score for exam in user_exams) / total_exams if total_exams > 0 else 0

        # Calculate total questions attempted
        total_questions = sum(exam.total_questions for exam in user_exams)

        # Get all exam questions for the user to calculate success rate by difficulty
        exam_ids = [exam.id for exam in user_exams]
        all_exam_questions = db_session.query(ExamQuestion)\
            .filter(ExamQuestion.exam_id.in_(exam_ids))\
            .all() if exam_ids else []

        # Calculate success rate by difficulty
        difficulty_stats = {'easy': {'correct': 0, 'total': 0},
                           'medium': {'correct': 0, 'total': 0},
                           'hard': {'correct': 0, 'total': 0}}

        for eq in all_exam_questions:
            difficulty = eq.question.difficulty
            if difficulty in difficulty_stats:
                difficulty_stats[difficulty]['total'] += 1
                if eq.is_correct:
                    difficulty_stats[difficulty]['correct'] += 1

        # Calculate success rates
        difficulty_rates = {}
        for diff, stats in difficulty_stats.items():
            if stats['total'] > 0:
                difficulty_rates[diff] = {
                    'rate': (stats['correct'] / stats['total']) * 100,
                    'correct': stats['correct'],
                    'total': stats['total']
                }
            else:
                difficulty_rates[diff] = {'rate': 0, 'correct': 0, 'total': 0}

        # Prepare data for Chart.js (last 10 exams in chronological order)
        chart_exams = user_exams[:10][::-1]  # Reverse to get chronological order
        chart_data = {
            'labels': [exam.completed_at.strftime('%b %d') for exam in chart_exams],
            'scores': [exam.score for exam in chart_exams]
        }

        return render_template('analytics.html',
                             exams=user_exams,
                             total_exams=total_exams,
                             avg_score=avg_score,
                             total_questions=total_questions,
                             difficulty_rates=difficulty_rates,
                             chart_data=chart_data)
    finally:
        db_session.close()


@app.route('/analytics/export-csv')
@login_required
def export_analytics_csv():
    """Export analytics data as CSV"""
    import csv
    from io import StringIO
    from flask import make_response

    db_session = get_session(db_engine)
    try:
        # Get all completed exams for current user
        user_exams = db_session.query(Exam)\
            .filter_by(user_id=current_user.id)\
            .filter(Exam.completed_at.isnot(None))\
            .order_by(Exam.completed_at.desc())\
            .all()

        # Create CSV
        output = StringIO()
        fieldnames = ['Exam ID', 'Date', 'Total Questions', 'Score (%)', 'Correct', 'Wrong', 'Duration (min)']
        writer = csv.DictWriter(output, fieldnames=fieldnames)

        writer.writeheader()
        for exam in user_exams:
            correct_count = sum(1 for eq in exam.exam_questions if eq.is_correct)
            wrong_count = exam.total_questions - correct_count
            duration = (exam.completed_at - exam.created_at).total_seconds() / 60 if exam.completed_at else 0

            writer.writerow({
                'Exam ID': exam.id,
                'Date': exam.completed_at.strftime('%Y-%m-%d %H:%M:%S') if exam.completed_at else 'N/A',
                'Total Questions': exam.total_questions,
                'Score (%)': f'{exam.score:.2f}',
                'Correct': correct_count,
                'Wrong': wrong_count,
                'Duration (min)': f'{duration:.1f}'
            })

        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=exam_analytics_{datetime.now().strftime("%Y%m%d")}.csv'
        response.headers['Content-Type'] = 'text/csv'

        return response
    finally:
        db_session.close()


@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard with comprehensive statistics and management tools"""
    db_session = get_session(db_engine)
    try:
        # Check if user is superadmin or org admin
        is_superadmin = current_user.is_superadmin()

        # Build base queries with organization filter
        if is_superadmin:
            # Superadmin sees everything
            users_query = db_session.query(User)
            documents_query = db_session.query(Document)
            questions_query = db_session.query(Question)
            exams_query = db_session.query(Exam)
        else:
            # Org admin sees only their organization
            users_query = db_session.query(User).filter_by(organization=current_user.organization)
            documents_query = db_session.query(Document).filter_by(organization=current_user.organization)
            questions_query = db_session.query(Question).join(Document).filter(
                Document.organization == current_user.organization
            )
            exams_query = db_session.query(Exam).join(User).filter(
                User.organization == current_user.organization
            )

        # Get comprehensive statistics
        total_users = users_query.count()
        total_documents = documents_query.count()
        total_questions = questions_query.count()
        total_exams = exams_query.count()

        # Count users by role
        admin_count = users_query.filter_by(role='admin').count()
        teacher_count = users_query.filter_by(role='teacher').count()
        student_count = users_query.filter_by(role='student').count()

        # Get unique organizations (superadmin only)
        if is_superadmin:
            organizations = db_session.query(User.organization).distinct().all()
            organization_list = [org[0] for org in organizations if org[0]]
            organization_count = len(organization_list)
        else:
            organization_count = 1  # Current organization only

        # Get recent users (last 5)
        recent_users = users_query\
            .order_by(User.created_at.desc())\
            .limit(5)\
            .all()

        # Get recent documents (last 5)
        recent_documents = documents_query\
            .order_by(Document.created_at.desc())\
            .limit(5)\
            .all()

        return render_template('admin_dashboard.html',
                               total_users=total_users,
                               total_documents=total_documents,
                               total_questions=total_questions,
                               total_exams=total_exams,
                               admin_count=admin_count,
                               teacher_count=teacher_count,
                               student_count=student_count,
                               organization_count=organization_count,
                               recent_users=recent_users,
                               recent_documents=recent_documents,
                               is_superadmin=is_superadmin)
    finally:
        db_session.close()


@app.route('/admin/users')
@admin_required
def admin_users():
    """View all users in the system (filtered by organization for org admins)"""
    db_session = get_session(db_engine)
    try:
        # Check if user is superadmin or org admin
        is_superadmin = current_user.is_superadmin()

        # Build query with organization filter
        if is_superadmin:
            # Superadmin sees all users
            users_query = db_session.query(User)
        else:
            # Org admin sees only their organization's users
            users_query = db_session.query(User).filter_by(organization=current_user.organization)

        # Get all users
        users = users_query.order_by(User.created_at.desc()).all()

        # Add document count for each user
        for user in users:
            user.document_count = db_session.query(Document)\
                .filter_by(uploaded_by=user.id)\
                .count()
            user.exam_count = db_session.query(Exam)\
                .filter_by(user_id=user.id)\
                .count()

        return render_template('admin_users.html', users=users, is_superadmin=is_superadmin)
    finally:
        db_session.close()


@app.route('/admin/documents')
@admin_required
def admin_documents():
    """View all documents in the system (filtered by organization for org admins)"""
    db_session = get_session(db_engine)
    try:
        # Check if user is superadmin or org admin
        is_superadmin = current_user.is_superadmin()

        # Build query with organization filter
        if is_superadmin:
            # Superadmin sees all documents
            documents_query = db_session.query(Document)
        else:
            # Org admin sees only their organization's documents
            documents_query = db_session.query(Document).filter_by(organization=current_user.organization)

        # Get all documents with uploader information
        documents = documents_query.order_by(Document.created_at.desc()).all()

        # Add question count for each document
        for doc in documents:
            doc.question_count = db_session.query(Question)\
                .filter_by(document_id=doc.id)\
                .count()

        return render_template('admin_documents.html', documents=documents, is_superadmin=is_superadmin)
    finally:
        db_session.close()


@app.route('/admin/user/<int:user_id>/role', methods=['POST'])
@admin_required
def admin_change_role(user_id):
    """Change a user's role (org admins can only change roles within their organization)"""
    new_role = request.form.get('role')

    # Superadmins can create superadmins, org admins cannot
    allowed_roles = ['student', 'teacher', 'admin', 'superadmin'] if current_user.is_superadmin() else ['student', 'teacher', 'admin']

    if new_role not in allowed_roles:
        flash('Invalid role specified', 'error')
        return redirect(url_for('admin_users'))

    db_session = get_session(db_engine)
    try:
        user = db_session.query(User).get(user_id)

        if not user:
            flash('User not found', 'error')
            return redirect(url_for('admin_users'))

        # Org admins can only modify users in their organization
        if not current_user.is_superadmin():
            if user.organization != current_user.organization:
                flash('You can only modify users in your organization', 'error')
                return redirect(url_for('admin_users'))

        # Prevent changing your own role
        if user.id == current_user.id:
            flash('You cannot change your own role', 'error')
            return redirect(url_for('admin_users'))

        # Org admins cannot modify superadmins
        if user.is_superadmin() and not current_user.is_superadmin():
            flash('You do not have permission to modify this user', 'error')
            return redirect(url_for('admin_users'))

        old_role = user.role
        user.role = new_role
        db_session.commit()

        flash(f'User "{user.name}" role changed from {old_role} to {new_role}', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error changing user role: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('admin_users'))


@app.route('/admin/demo-organizations', methods=['POST'])
@admin_required
def admin_create_demo_orgs():
    """Create demo organizations with sample users"""
    db_session = get_session(db_engine)
    try:
        demo_orgs = [
            {
                'name': 'Demo University',
                'users': [
                    {'name': 'Prof. John Smith', 'email': 'john.smith@demouniv.edu', 'role': 'teacher'},
                    {'name': 'Alice Johnson', 'email': 'alice.j@demouniv.edu', 'role': 'student'},
                    {'name': 'Bob Williams', 'email': 'bob.w@demouniv.edu', 'role': 'student'},
                ]
            },
            {
                'name': 'Tech Academy',
                'users': [
                    {'name': 'Dr. Sarah Davis', 'email': 'sarah.davis@techacademy.edu', 'role': 'teacher'},
                    {'name': 'Charlie Brown', 'email': 'charlie.b@techacademy.edu', 'role': 'student'},
                    {'name': 'Diana Miller', 'email': 'diana.m@techacademy.edu', 'role': 'student'},
                ]
            },
            {
                'name': 'Learning Institute',
                'users': [
                    {'name': 'Prof. Michael Lee', 'email': 'michael.lee@learninginst.edu', 'role': 'teacher'},
                    {'name': 'Emma Wilson', 'email': 'emma.w@learninginst.edu', 'role': 'student'},
                ]
            }
        ]

        created_count = 0
        default_password = 'demo123'

        for org_data in demo_orgs:
            for user_data in org_data['users']:
                # Check if user already exists
                existing_user = db_session.query(User)\
                    .filter_by(email=user_data['email'])\
                    .first()

                if not existing_user:
                    new_user = User(
                        email=user_data['email'],
                        name=user_data['name'],
                        organization=org_data['name'],
                        role=user_data['role']
                    )
                    new_user.set_password(default_password)
                    db_session.add(new_user)
                    created_count += 1

        db_session.commit()

        if created_count > 0:
            flash(f'Created {created_count} demo users across 3 organizations. Default password: demo123', 'success')
        else:
            flash('All demo users already exist', 'info')

    except Exception as e:
        db_session.rollback()
        flash(f'Error creating demo organizations: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/admin/reset-database', methods=['POST'])
@admin_required
def admin_reset_database():
    """Reset the database (DANGER: Deletes all data except current admin)"""
    confirm = request.form.get('confirm')

    if confirm != 'RESET':
        flash('Database reset cancelled. You must type RESET to confirm.', 'error')
        return redirect(url_for('admin_dashboard'))

    db_session = get_session(db_engine)
    try:
        # Store current admin info
        admin_id = current_user.id

        # Delete all data except current admin
        db_session.query(ExamQuestion).delete()
        db_session.query(Question).delete()
        db_session.query(Exam).delete()
        db_session.query(Document).delete()
        db_session.query(User).filter(User.id != admin_id).delete()

        db_session.commit()

        # Clear uploads folder
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            for filename in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        flash('Database reset successfully! All data deleted except your admin account.', 'success')
    except Exception as e:
        db_session.rollback()
        flash(f'Error resetting database: {str(e)}', 'error')
    finally:
        db_session.close()

    return redirect(url_for('admin_dashboard'))


@app.route('/teacher')
@role_required('teacher', 'admin')
def teacher_dashboard():
    """Teacher dashboard - accessible to teachers and admins"""
    db_session = get_session(db_engine)
    try:
        # Get documents uploaded by current user
        documents = db_session.query(Document).filter_by(uploaded_by=current_user.id).all()

        return render_template('teacher_dashboard.html',
                               documents=documents)
    finally:
        db_session.close()


@app.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('teacher', 'admin', 'superadmin')
def settings():
    """AI Settings page for teachers and admins - includes API key management for admins"""
    db_session = get_session(db_engine)
    try:
        is_superadmin = current_user.is_superadmin()
        is_admin = current_user.role in ['admin', 'superadmin']

        # For superadmin, allow selecting which organization to manage
        target_org = None
        org_settings = None
        all_orgs = []

        if is_admin:
            if is_superadmin:
                target_org = request.args.get('org') or request.form.get('selected_organization')
                if not target_org:
                    # Show org selector for superadmin
                    all_orgs = db_session.query(OrganizationSettings).all()
                    return render_template('settings.html',
                                         ai_models=AI_MODELS,
                                         is_superadmin=is_superadmin,
                                         is_admin=is_admin,
                                         all_organizations=all_orgs,
                                         show_org_selector=True)
            else:
                # Org admin can only manage their own organization
                target_org = current_user.organization
                if not target_org:
                    flash('You must be part of an organization to manage API keys', 'error')
                    return redirect(url_for('admin_dashboard'))

            # Get organization settings for target org
            org_settings = db_session.query(OrganizationSettings)\
                .filter_by(organization_name=target_org)\
                .first()

            # Get all orgs for superadmin dropdown
            if is_superadmin:
                all_orgs = db_session.query(OrganizationSettings).all()

        if request.method == 'POST':
            # Handle user AI preferences (teachers and admins)
            provider = request.form.get('ai_provider')
            model = request.form.get('ai_model')

            if provider and model:
                current_user.ai_provider = provider
                current_user.ai_model = model
                db_session.add(current_user)
                flash(f'AI preferences updated! Now using {AI_MODELS.get(provider, {}).get(model, model)}', 'success')

            # Handle organization API keys (admins only)
            if is_admin and target_org:
                # Create org settings if it doesn't exist
                if not org_settings:
                    org_settings = OrganizationSettings(
                        organization_name=target_org,
                        display_name=target_org
                    )
                    db_session.add(org_settings)
                    db_session.flush()

                # Update API Keys
                openai_key = request.form.get('openai_api_key', '').strip()
                gemini_key = request.form.get('gemini_api_key', '').strip()

                if openai_key:
                    org_settings.openai_api_key = openai_key
                    flash('OpenAI API key updated successfully!', 'success')

                if gemini_key:
                    org_settings.gemini_api_key = gemini_key
                    flash('Gemini API key updated successfully!', 'success')

            db_session.commit()

            # Redirect back with org parameter for superadmin
            if is_superadmin and target_org:
                return redirect(url_for('settings', org=target_org))
            else:
                return redirect(url_for('settings'))

        return render_template('settings.html',
                             ai_models=AI_MODELS,
                             is_superadmin=is_superadmin,
                             is_admin=is_admin,
                             org_settings=org_settings,
                             all_organizations=all_orgs,
                             target_org=target_org)
    except Exception as e:
        db_session.rollback()
        flash(f'Error updating settings: {str(e)}', 'error')
        return redirect(url_for('settings'))
    finally:
        db_session.close()


@app.route('/members')
@login_required
def organization_members():
    """View all members in the user's organization"""
    if not current_user.organization:
        flash('You are not part of an organization', 'warning')
        return redirect(url_for('index'))

    db_session = get_session(db_engine)
    try:
        # Get all users in the same organization
        members = db_session.query(User)\
            .filter_by(organization=current_user.organization)\
            .order_by(User.role.desc(), User.name)\
            .all()

        # Group by role
        admins = [u for u in members if u.role == 'admin']
        teachers = [u for u in members if u.role == 'teacher']
        students = [u for u in members if u.role == 'student']

        # Get statistics for each member
        for member in members:
            member.document_count = db_session.query(Document)\
                .filter_by(uploaded_by=member.id)\
                .count()
            member.exam_count = db_session.query(Exam)\
                .filter_by(user_id=member.id)\
                .filter(Exam.completed_at.isnot(None))\
                .count()

        return render_template('organization_members.html',
                             admins=admins,
                             teachers=teachers,
                             students=students,
                             total_members=len(members),
                             organization_name=current_user.organization)
    finally:
        db_session.close()


@app.route('/organization-settings', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'superadmin')
def organization_settings():
    """Organization branding and white-label settings (admin and superadmin)"""
    db_session = get_session(db_engine)
    try:
        is_superadmin = current_user.is_superadmin()

        # For superadmin, allow selecting which organization to manage
        target_org = None
        if is_superadmin:
            target_org = request.args.get('org') or request.form.get('selected_organization')
            if not target_org:
                # If no org specified, show org selector
                all_orgs = db_session.query(OrganizationSettings).all()
                return render_template('organization_settings.html',
                                     org_settings=None,
                                     is_superadmin=is_superadmin,
                                     all_organizations=all_orgs,
                                     show_org_selector=True)
        else:
            # Org admin can only manage their own organization
            target_org = current_user.organization
            if not target_org:
                flash('You must be part of an organization to access settings', 'error')
                return redirect(url_for('admin_dashboard'))

        # Get or create organization settings for target org
        org_settings = db_session.query(OrganizationSettings)\
            .filter_by(organization_name=target_org)\
            .first()

        # Get all organizations for superadmin dropdown
        all_orgs = db_session.query(OrganizationSettings).all() if is_superadmin else []

        if request.method == 'POST':
            # Get or create org settings for target organization
            if not org_settings:
                org_settings = OrganizationSettings(
                    organization_name=target_org,
                    display_name=target_org
                )
                db_session.add(org_settings)
                db_session.flush()

            # Update basic settings
            org_settings.display_name = request.form.get('display_name', org_settings.display_name)
            org_settings.subdomain = request.form.get('subdomain') or None

            # Validate url_path uniqueness (only when not empty)
            new_url_path = request.form.get('url_path') or None
            if new_url_path and new_url_path != org_settings.url_path:
                # Check if url_path is already in use by another organization
                existing_url_path = db_session.query(OrganizationSettings)\
                    .filter(OrganizationSettings.url_path == new_url_path)\
                    .filter(OrganizationSettings.id != org_settings.id)\
                    .first()
                if existing_url_path:
                    flash(f'URL path "{new_url_path}" is already in use by another organization', 'error')
                    return redirect(url_for('organization_settings', org=target_org) if is_superadmin else url_for('organization_settings'))

            org_settings.url_path = new_url_path

            # Update colors
            org_settings.primary_color = request.form.get('primary_color', org_settings.primary_color)
            org_settings.secondary_color = request.form.get('secondary_color', org_settings.secondary_color)
            org_settings.success_color = request.form.get('success_color', org_settings.success_color)
            org_settings.danger_color = request.form.get('danger_color', org_settings.danger_color)

            # Update custom CSS
            org_settings.custom_css = request.form.get('custom_css') or None
            org_settings.custom_footer_html = request.form.get('custom_footer_html') or None

            # Update features
            org_settings.enable_analytics = 'enable_analytics' in request.form
            org_settings.enable_csv_export = 'enable_csv_export' in request.form
            org_settings.enable_pdf_export = 'enable_pdf_export' in request.form

            # Update contact info
            org_settings.contact_email = request.form.get('contact_email') or None

            # Validate and update support URL
            support_url = request.form.get('support_url', '').strip()
            if support_url:
                # Check if URL has a valid format
                if not (support_url.startswith('http://') or support_url.startswith('https://')):
                    flash('Support URL must start with http:// or https:// (e.g., https://support.yourorg.com)', 'error')
                    return redirect(url_for('organization_settings', org=target_org) if is_superadmin else url_for('organization_settings'))
                org_settings.support_url = support_url
            else:
                org_settings.support_url = None

            # Handle logo upload
            if 'logo' in request.files:
                logo_file = request.files['logo']
                if logo_file and logo_file.filename:
                    # Validate file type
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
                    file_ext = logo_file.filename.rsplit('.', 1)[1].lower()
                    if file_ext in allowed_extensions:
                        # Generate unique filename
                        logo_filename = f"logo_{target_org}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
                        logo_path = os.path.join('static', 'logos', logo_filename)

                        # Remove old logo if exists
                        if org_settings.logo_filename:
                            old_logo_path = os.path.join('static', 'logos', org_settings.logo_filename)
                            if os.path.exists(old_logo_path):
                                os.remove(old_logo_path)

                        # Save new logo
                        logo_file.save(logo_path)
                        org_settings.logo_filename = logo_filename
                    else:
                        flash('Invalid logo file type. Allowed: PNG, JPG, JPEG, GIF, SVG', 'warning')

            db_session.commit()
            flash('Organization settings updated successfully!', 'success')

            # Redirect back to org settings with org parameter for superadmin
            if is_superadmin:
                return redirect(url_for('organization_settings', org=target_org))
            else:
                return redirect(url_for('organization_settings'))

        return render_template('organization_settings.html',
                             org_settings=org_settings,
                             is_superadmin=is_superadmin,
                             all_organizations=all_orgs,
                             target_org=target_org)
    except Exception as e:
        db_session.rollback()
        flash(f'Error updating organization settings: {str(e)}', 'error')
        return redirect(url_for('organization_settings'))
    finally:
        db_session.close()


@app.route('/upload-csv-questions', methods=['GET', 'POST'])
@login_required
@role_required('teacher', 'admin')
def upload_csv_questions():
    """Upload MCQ questions via CSV file"""
    db_session = get_session(db_engine)
    try:
        if request.method == 'POST':
            if 'csv_file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)

            file = request.files['csv_file']

            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)

            # Check file extension
            if not file.filename.endswith('.csv'):
                flash('Invalid file type. Please upload a CSV file.', 'error')
                return redirect(request.url)

            try:
                import csv
                from io import StringIO

                # Read CSV content
                csv_content = file.read().decode('utf-8')
                csv_file = StringIO(csv_content)
                csv_reader = csv.DictReader(csv_file)

                # Validate CSV headers
                required_headers = ['question', 'option_a', 'option_b', 'option_c', 'option_d',
                                  'correct_answer', 'explanation', 'difficulty']

                if not csv_reader.fieldnames:
                    flash('CSV file is empty or invalid', 'error')
                    return redirect(request.url)

                missing_headers = set(required_headers) - set(csv_reader.fieldnames)
                if missing_headers:
                    flash(f'CSV is missing required columns: {", ".join(missing_headers)}', 'error')
                    return redirect(request.url)

                # Create or get "CSV Import" document for this user
                csv_doc = db_session.query(Document)\
                    .filter_by(uploaded_by=current_user.id, filename='CSV Import').first()

                if not csv_doc:
                    csv_doc = Document(
                        filename='CSV Import',
                        content='Questions imported from CSV files',
                        uploaded_by=current_user.id,
                        organization=current_user.organization
                    )
                    db_session.add(csv_doc)
                    db_session.flush()  # Get the document ID

                # Get existing questions for duplicate detection
                existing_questions_obj = db_session.query(Question)\
                    .filter_by(document_id=csv_doc.id).all()
                existing_question_texts = [q.question_text for q in existing_questions_obj]

                # Parse CSV and create questions
                saved_count = 0
                error_count = 0
                validation_errors = []

                for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (accounting for header)
                    try:
                        question_text = row.get('question', '').strip()
                        option_a = row.get('option_a', '').strip()
                        option_b = row.get('option_b', '').strip()
                        option_c = row.get('option_c', '').strip()
                        option_d = row.get('option_d', '').strip()
                        correct_answer = row.get('correct_answer', '').strip().upper()
                        explanation = row.get('explanation', '').strip()
                        difficulty = row.get('difficulty', 'medium').strip().lower()

                        # Validate difficulty
                        if difficulty not in ['easy', 'medium', 'hard']:
                            difficulty = 'medium'

                        # Build options dict
                        options = {
                            'A': option_a,
                            'B': option_b,
                            'C': option_c,
                            'D': option_d
                        }

                        # Validate question
                        is_valid, errors, fixed_data = validate_question_complete(
                            question_text=question_text,
                            question_type='mcq',
                            correct_answer=correct_answer,
                            options=options,
                            existing_questions=existing_question_texts,
                            auto_fix=True
                        )

                        if not is_valid:
                            validation_errors.append(f"Row {row_num}: {', '.join(errors)}")
                            error_count += 1
                            continue

                        # Create question
                        new_question = Question(
                            question_text=fixed_data['question_text'],
                            question_type='mcq',
                            options_json=fixed_data['options'],
                            correct_answer=correct_answer,
                            explanation=explanation,
                            document_id=csv_doc.id,
                            difficulty=fixed_data['difficulty'],
                            status='approved',
                            created_by=current_user.id
                        )
                        db_session.add(new_question)
                        existing_question_texts.append(fixed_data['question_text'])
                        saved_count += 1

                    except Exception as e:
                        validation_errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1

                # Commit if any questions were saved
                if saved_count > 0:
                    db_session.commit()
                    flash(f'Successfully imported {saved_count} MCQ questions from CSV!', 'success')

                if error_count > 0:
                    flash(f'{error_count} rows had errors and were skipped.', 'warning')
                    # Show first 5 errors
                    for error in validation_errors[:5]:
                        flash(error, 'warning')
                    if len(validation_errors) > 5:
                        flash(f'... and {len(validation_errors) - 5} more errors', 'warning')

                if saved_count == 0 and error_count > 0:
                    flash('No questions were imported due to validation errors.', 'error')
                    return redirect(request.url)

                return redirect(url_for('question_bank'))

            except Exception as e:
                db_session.rollback()
                flash(f'Error processing CSV file: {str(e)}', 'error')
                return redirect(request.url)

        return render_template('upload_csv.html')
    finally:
        db_session.close()


@app.route('/download-sample-csv')
@login_required
@role_required('teacher', 'admin')
def download_sample_csv():
    """Download sample CSV template for MCQ questions"""
    import csv
    from io import StringIO
    from flask import make_response

    # Create sample CSV content
    sample_data = [
        {
            'question': 'What is the capital of France?',
            'option_a': 'London',
            'option_b': 'Paris',
            'option_c': 'Berlin',
            'option_d': 'Madrid',
            'correct_answer': 'B',
            'explanation': 'Paris is the capital and largest city of France.',
            'difficulty': 'easy'
        },
        {
            'question': 'Which programming language is known for its use in web development?',
            'option_a': 'C++',
            'option_b': 'Python',
            'option_c': 'JavaScript',
            'option_d': 'Assembly',
            'correct_answer': 'C',
            'explanation': 'JavaScript is primarily used for web development and runs in browsers.',
            'difficulty': 'medium'
        },
        {
            'question': 'What is the time complexity of binary search?',
            'option_a': 'O(n)',
            'option_b': 'O(log n)',
            'option_c': 'O(n^2)',
            'option_d': 'O(1)',
            'correct_answer': 'B',
            'explanation': 'Binary search has a time complexity of O(log n) as it divides the search space in half each iteration.',
            'difficulty': 'hard'
        }
    ]

    # Create CSV string
    output = StringIO()
    fieldnames = ['question', 'option_a', 'option_b', 'option_c', 'option_d',
                  'correct_answer', 'explanation', 'difficulty']
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for row in sample_data:
        writer.writerow(row)

    # Create response
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=mcq_questions_template.csv'
    response.headers['Content-Type'] = 'text/csv'

    return response


# Error handlers
@app.route('/debug-user')
@login_required
def debug_user():
    """Debug route to check current user's status"""
    db_session = get_session(db_engine)
    try:
        user_info = {
            'email': current_user.email,
            'name': current_user.name,
            'role': current_user.role,
            'organization': current_user.organization,
            'is_superadmin': current_user.is_superadmin(),
            'is_org_admin': current_user.is_org_admin(),
            'is_authenticated': current_user.is_authenticated
        }

        # Get org settings if available
        org_settings = None
        if current_user.organization:
            org_settings = db_session.query(OrganizationSettings)\
                .filter_by(organization_name=current_user.organization)\
                .first()

        org_info = None
        if org_settings:
            org_info = {
                'display_name': org_settings.display_name,
                'has_openai_key': org_settings.has_openai_key(),
                'has_gemini_key': org_settings.has_gemini_key()
            }

        return jsonify({
            'user': user_info,
            'organization': org_info,
            'message': 'If is_superadmin is True, you should see superadmin UI in /admin'
        })
    finally:
        db_session.close()


@app.errorhandler(403)
def forbidden(e):
    """Handle 403 Forbidden errors"""
    return render_template('403.html'), 403


@app.errorhandler(404)
def not_found(e):
    """Handle 404 Not Found errors"""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
