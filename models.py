from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()


class User(Base, UserMixin):
    """User model for authentication and user management"""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    role = Column(String(50), default='student')  # student, teacher, admin, superadmin
    remember_token = Column(String(255), nullable=True)  # For remember me functionality

    # AI Settings (for teachers and admins)
    ai_provider = Column(String(50), default='gemini')  # 'openai' or 'gemini'
    ai_model = Column(String(100), default='gemini-2.5-flash')  # Specific model name

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship('Document', back_populates='uploader', cascade='all, delete-orphan')
    exams = relationship('Exam', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user's password"""
        return check_password_hash(self.password_hash, password)

    def is_superadmin(self):
        """Check if user is a superadmin"""
        return self.role == 'superadmin' or self.email == 'admin@example.com'

    def is_org_admin(self):
        """Check if user is an organization admin (but not superadmin)"""
        return self.role == 'admin' and not self.is_superadmin()

    def __repr__(self):
        return f'<User {self.email}>'


class Document(Base):
    """Document model for storing uploaded study materials"""
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Extracted text content
    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    organization = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    uploader = relationship('User', back_populates='documents')
    questions = relationship('Question', back_populates='document', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Document {self.filename}>'


class Question(Base):
    """Question model for storing generated exam questions"""
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), default='mcq')  # mcq, true_false, short_answer
    options_json = Column(JSON, nullable=True)  # Store as JSON: {"A": "...", "B": "...", "C": "...", "D": "..."} for MCQ
    correct_answer = Column(String(10), nullable=True)  # A, B, C, D for MCQ, "true"/"false" for T/F
    model_answer = Column(Text, nullable=True)  # For short answer questions
    key_points = Column(JSON, nullable=True)  # Array of key points for short answer
    explanation = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    difficulty = Column(String(20), default='medium')  # easy, medium, hard
    status = Column(String(20), default='pending')  # pending, approved, rejected
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # User who created/approved it
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship('Document', back_populates='questions')
    exam_questions = relationship('ExamQuestion', back_populates='question', cascade='all, delete-orphan')
    creator = relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:50]}...>'


class Exam(Base):
    """Exam model for storing exam sessions and results"""
    __tablename__ = 'exams'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    score = Column(Float, nullable=True)  # Percentage score (0-100)
    total_questions = Column(Integer, nullable=False)
    completed_at = Column(DateTime, nullable=True)  # Null if exam is in progress
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship('User', back_populates='exams')
    exam_questions = relationship('ExamQuestion', back_populates='exam', cascade='all, delete-orphan')

    def calculate_score(self):
        """Calculate the exam score based on correct answers"""
        if self.total_questions == 0:
            return 0.0

        correct_answers = sum(1 for eq in self.exam_questions if eq.is_correct)
        self.score = (correct_answers / self.total_questions) * 100
        return self.score

    def is_completed(self):
        """Check if the exam is completed"""
        return self.completed_at is not None

    def __repr__(self):
        return f'<Exam {self.id} - User {self.user_id} - Score: {self.score}%>'


class ExamQuestion(Base):
    """ExamQuestion model for linking questions to exams with user responses"""
    __tablename__ = 'exam_questions'

    id = Column(Integer, primary_key=True)
    exam_id = Column(Integer, ForeignKey('exams.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    user_answer = Column(Text, nullable=True)  # A, B, C, D for MCQ/T/F, or full text for short answer
    is_correct = Column(Boolean, nullable=True)  # True/False or null if not answered
    time_spent = Column(Integer, nullable=True)  # Time spent in seconds
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    exam = relationship('Exam', back_populates='exam_questions')
    question = relationship('Question', back_populates='exam_questions')

    def check_answer(self):
        """Check if the user's answer is correct"""
        if self.user_answer is None:
            self.is_correct = False
        else:
            self.is_correct = (self.user_answer == self.question.correct_answer)
        return self.is_correct

    def __repr__(self):
        return f'<ExamQuestion {self.id} - Exam {self.exam_id} - Question {self.question_id}>'


class OrganizationSettings(Base):
    """Organization white-label settings for customization"""
    __tablename__ = 'organization_settings'

    id = Column(Integer, primary_key=True)
    organization_name = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)  # Display name for branding
    subdomain = Column(String(100), unique=True, nullable=True, index=True)  # Optional subdomain
    url_path = Column(String(100), nullable=True, index=True)  # Optional URL path like /org-name (unique constraint handled at app level)

    # Branding
    logo_filename = Column(String(255), nullable=True)  # Uploaded logo file
    favicon_filename = Column(String(255), nullable=True)  # Custom favicon

    # Color Scheme
    primary_color = Column(String(7), default='#0d6efd')  # Hex color for primary brand color
    secondary_color = Column(String(7), default='#6c757d')  # Hex color for secondary color
    success_color = Column(String(7), default='#198754')  # Success/positive actions
    danger_color = Column(String(7), default='#dc3545')  # Danger/negative actions

    # Custom Styling
    custom_css = Column(Text, nullable=True)  # Custom CSS injection
    custom_footer_html = Column(Text, nullable=True)  # Custom footer content

    # Features
    enable_analytics = Column(Boolean, default=True)
    enable_csv_export = Column(Boolean, default=True)
    enable_pdf_export = Column(Boolean, default=True)

    # Contact Info
    contact_email = Column(String(255), nullable=True)
    support_url = Column(String(500), nullable=True)

    # API Keys (stored securely, encrypted at rest recommended for production)
    openai_api_key = Column(String(500), nullable=True)  # Organization's OpenAI API key
    gemini_api_key = Column(String(500), nullable=True)  # Organization's Gemini API key

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f'<OrganizationSettings {self.organization_name}>'

    def get_masked_openai_key(self):
        """Get masked OpenAI API key for display (shows last 4 characters only)"""
        if not self.openai_api_key:
            return None
        if len(self.openai_api_key) <= 4:
            return '****'
        return '*' * (len(self.openai_api_key) - 4) + self.openai_api_key[-4:]

    def get_masked_gemini_key(self):
        """Get masked Gemini API key for display (shows last 4 characters only)"""
        if not self.gemini_api_key:
            return None
        if len(self.gemini_api_key) <= 4:
            return '****'
        return '*' * (len(self.gemini_api_key) - 4) + self.gemini_api_key[-4:]

    def has_openai_key(self):
        """Check if OpenAI API key is configured"""
        return self.openai_api_key is not None and len(self.openai_api_key) > 0

    def has_gemini_key(self):
        """Check if Gemini API key is configured"""
        return self.gemini_api_key is not None and len(self.gemini_api_key) > 0

    def get_logo_url(self):
        """Get the URL for the organization logo"""
        if self.logo_filename:
            return f'/static/logos/{self.logo_filename}'
        return None

    def get_theme_css(self):
        """Generate CSS for the organization theme"""
        return f"""
        :root {{
            --bs-primary: {self.primary_color};
            --bs-primary-rgb: {self._hex_to_rgb(self.primary_color)};
            --bs-secondary: {self.secondary_color};
            --bs-secondary-rgb: {self._hex_to_rgb(self.secondary_color)};
            --bs-success: {self.success_color};
            --bs-success-rgb: {self._hex_to_rgb(self.success_color)};
            --bs-danger: {self.danger_color};
            --bs-danger-rgb: {self._hex_to_rgb(self.danger_color)};
        }}
        .navbar {{
            background-color: {self.primary_color} !important;
        }}
        .btn-primary {{
            background-color: {self.primary_color};
            border-color: {self.primary_color};
        }}
        .btn-primary:hover {{
            background-color: {self._darken_color(self.primary_color, 10)};
            border-color: {self._darken_color(self.primary_color, 10)};
        }}
        """

    @staticmethod
    def _hex_to_rgb(hex_color):
        """Convert hex color to RGB string"""
        hex_color = hex_color.lstrip('#')
        return ', '.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))

    @staticmethod
    def _darken_color(hex_color, percent):
        """Darken a hex color by a percentage"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        darker = tuple(int(c * (1 - percent / 100)) for c in rgb)
        return f"#{darker[0]:02x}{darker[1]:02x}{darker[2]:02x}"


# Database initialization helper
def get_engine(database_url='sqlite:///exam_simulator.db'):
    """Create and return a database engine"""
    return create_engine(database_url, echo=False)


def get_session(engine):
    """Create and return a database session"""
    Session = sessionmaker(bind=engine)
    return Session()


def create_all_tables(engine):
    """Create all tables in the database"""
    Base.metadata.create_all(engine)


def drop_all_tables(engine):
    """Drop all tables from the database"""
    Base.metadata.drop_all(engine)
