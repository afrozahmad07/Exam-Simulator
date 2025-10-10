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
    role = Column(String(50), default='student')  # student, teacher, admin
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
    options_json = Column(JSON, nullable=False)  # Store as JSON: {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String(10), nullable=False)  # A, B, C, or D
    explanation = Column(Text, nullable=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    difficulty = Column(String(20), default='medium')  # easy, medium, hard
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship('Document', back_populates='questions')
    exam_questions = relationship('ExamQuestion', back_populates='question', cascade='all, delete-orphan')

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
    user_answer = Column(String(10), nullable=True)  # A, B, C, D or null if not answered
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
