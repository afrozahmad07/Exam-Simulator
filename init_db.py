#!/usr/bin/env python3
"""
Database initialization script for Exam Simulator
Creates all database tables and optionally seeds with sample data
"""

import os
import sys
from models import (
    Base, User, Document, Question, Exam, ExamQuestion,
    get_engine, get_session, create_all_tables, drop_all_tables
)


def init_database(reset=False):
    """
    Initialize the database with all tables

    Args:
        reset (bool): If True, drop all existing tables before creating new ones
    """
    # Get database engine
    database_url = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')
    engine = get_engine(database_url)

    print(f"Initializing database at: {database_url}")

    # Drop existing tables if reset is True
    if reset:
        print("⚠️  Dropping all existing tables...")
        drop_all_tables(engine)
        print("✓ All tables dropped")

    # Create all tables
    print("Creating database tables...")
    create_all_tables(engine)
    print("✓ All tables created successfully")

    return engine


def seed_sample_data(engine):
    """
    Seed the database with sample data for testing

    Args:
        engine: SQLAlchemy engine instance
    """
    session = get_session(engine)

    try:
        print("\nSeeding sample data...")

        # Create sample users
        admin_user = User(
            email='admin@example.com',
            name='Admin User',
            organization='Example University',
            role='admin'
        )
        admin_user.set_password('admin123')

        teacher_user = User(
            email='teacher@example.com',
            name='John Teacher',
            organization='Example University',
            role='teacher'
        )
        teacher_user.set_password('teacher123')

        student_user = User(
            email='student@example.com',
            name='Jane Student',
            organization='Example University',
            role='student'
        )
        student_user.set_password('student123')

        session.add_all([admin_user, teacher_user, student_user])
        session.commit()
        print("✓ Created 3 sample users (admin, teacher, student)")

        # Create sample document
        sample_document = Document(
            filename='sample_study_material.txt',
            content='Python is a high-level programming language. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python uses dynamic typing and automatic memory management.',
            uploaded_by=teacher_user.id,
            organization='Example University'
        )
        session.add(sample_document)
        session.commit()
        print("✓ Created 1 sample document")

        # Create sample questions
        question1 = Question(
            question_text='What is Python?',
            options_json={
                'A': 'A low-level programming language',
                'B': 'A high-level programming language',
                'C': 'A database management system',
                'D': 'An operating system'
            },
            correct_answer='B',
            explanation='Python is a high-level programming language known for its simplicity and readability.',
            document_id=sample_document.id,
            difficulty='easy'
        )

        question2 = Question(
            question_text='Which programming paradigms does Python support?',
            options_json={
                'A': 'Only procedural programming',
                'B': 'Only object-oriented programming',
                'C': 'Procedural, object-oriented, and functional programming',
                'D': 'Only functional programming'
            },
            correct_answer='C',
            explanation='Python is a multi-paradigm language supporting procedural, object-oriented, and functional programming.',
            document_id=sample_document.id,
            difficulty='medium'
        )

        question3 = Question(
            question_text='What type of typing does Python use?',
            options_json={
                'A': 'Static typing',
                'B': 'Dynamic typing',
                'C': 'No typing',
                'D': 'Weak typing only'
            },
            correct_answer='B',
            explanation='Python uses dynamic typing, meaning variable types are determined at runtime.',
            document_id=sample_document.id,
            difficulty='medium'
        )

        session.add_all([question1, question2, question3])
        session.commit()
        print("✓ Created 3 sample questions")

        print("\n✅ Database seeded successfully!")
        print("\nSample Login Credentials:")
        print("=" * 50)
        print("Admin:    admin@example.com    / admin123")
        print("Teacher:  teacher@example.com  / teacher123")
        print("Student:  student@example.com  / student123")
        print("=" * 50)

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        session.close()


def main():
    """Main function to run database initialization"""
    import argparse

    parser = argparse.ArgumentParser(description='Initialize the Exam Simulator database')
    parser.add_argument('--reset', action='store_true', help='Drop all existing tables before creating new ones')
    parser.add_argument('--seed', action='store_true', help='Seed the database with sample data')
    parser.add_argument('--no-seed', action='store_true', help='Do not seed sample data (default if not specified)')

    args = parser.parse_args()

    # Initialize database
    engine = init_database(reset=args.reset)

    # Seed sample data if requested
    if args.seed:
        seed_sample_data(engine)
    elif not args.no_seed and args.reset:
        # Ask user if they want to seed data after reset
        response = input("\nWould you like to seed the database with sample data? (y/n): ")
        if response.lower() in ['y', 'yes']:
            seed_sample_data(engine)

    print("\n✅ Database initialization complete!")


if __name__ == '__main__':
    main()
