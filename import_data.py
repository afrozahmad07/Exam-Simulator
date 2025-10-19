#!/usr/bin/env python3
"""
Data Import Script
Imports data from JSON export file to any database (SQLite or MariaDB).

WARNING: This will add data to the database. Use with caution!
For a clean import, backup and clear the target database first.
"""

import json
import os
from datetime import datetime
from dotenv import load_dotenv
from models import (
    User, Document, Question, Exam, ExamQuestion, OrganizationSettings,
    get_engine, get_session, create_all_tables
)

def parse_datetime(dt_string):
    """Parse ISO datetime string or return None"""
    if not dt_string:
        return None
    try:
        return datetime.fromisoformat(dt_string)
    except:
        return None

def import_data(filename='exam_data_export.json', clear_existing=False):
    """Import data from JSON file to database"""

    # Load environment and connect
    load_dotenv()
    database_url = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')

    print("="*60)
    print("DATA IMPORT SCRIPT")
    print("="*60)
    print(f"Target database: {'MariaDB/MySQL' if 'mysql' in database_url else 'SQLite'}")
    print(f"Import file: {filename}")
    print("="*60)

    # Confirm before proceeding
    if clear_existing:
        print("\n⚠️  WARNING: You chose to clear existing data!")
        confirm = input("Type 'YES' to confirm clearing all data: ")
        if confirm != 'YES':
            print("Import cancelled.")
            return
    else:
        print("\n📝 This will ADD data to the existing database.")
        confirm = input("Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            print("Import cancelled.")
            return

    # Connect to database
    engine = get_engine(database_url)

    # Ensure tables exist
    create_all_tables(engine)

    session = get_session(engine)

    # Clear existing data if requested
    if clear_existing:
        print("\nClearing existing data...")
        session.query(ExamQuestion).delete()
        session.query(Exam).delete()
        session.query(Question).delete()
        session.query(Document).delete()
        session.query(OrganizationSettings).delete()
        session.query(User).delete()
        session.commit()
        print("✓ Existing data cleared")

    # Load JSON data
    print("\nLoading import file...")
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: File '{filename}' not found!")
        return
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON file: {e}")
        return

    # Import users
    print(f"\nImporting {len(data['users'])} users...")
    for user_data in data['users']:
        user = User(
            id=user_data['id'],
            email=user_data['email'],
            password_hash=user_data['password_hash'],
            name=user_data['name'],
            organization=user_data.get('organization'),
            role=user_data.get('role', 'student'),
            remember_token=user_data.get('remember_token'),
            ai_provider=user_data.get('ai_provider', 'gemini'),
            ai_model=user_data.get('ai_model', 'gemini-2.5-flash'),
            created_at=parse_datetime(user_data.get('created_at'))
        )
        session.merge(user)  # merge instead of add to handle duplicates
    session.commit()
    print(f"✓ Imported {len(data['users'])} users")

    # Import organization settings
    if data.get('organization_settings'):
        print(f"\nImporting {len(data['organization_settings'])} organizations...")
        for org_data in data['organization_settings']:
            org = OrganizationSettings(
                id=org_data['id'],
                organization_name=org_data['organization_name'],
                display_name=org_data['display_name'],
                subdomain=org_data.get('subdomain'),
                url_path=org_data.get('url_path'),
                logo_filename=org_data.get('logo_filename'),
                favicon_filename=org_data.get('favicon_filename'),
                primary_color=org_data.get('primary_color', '#0d6efd'),
                secondary_color=org_data.get('secondary_color', '#6c757d'),
                success_color=org_data.get('success_color', '#198754'),
                danger_color=org_data.get('danger_color', '#dc3545'),
                custom_css=org_data.get('custom_css'),
                custom_footer_html=org_data.get('custom_footer_html'),
                enable_analytics=org_data.get('enable_analytics', True),
                enable_csv_export=org_data.get('enable_csv_export', True),
                enable_pdf_export=org_data.get('enable_pdf_export', True),
                contact_email=org_data.get('contact_email'),
                support_url=org_data.get('support_url'),
                openai_api_key=org_data.get('openai_api_key'),
                gemini_api_key=org_data.get('gemini_api_key'),
                created_at=parse_datetime(org_data.get('created_at')),
                updated_at=parse_datetime(org_data.get('updated_at'))
            )
            session.merge(org)
        session.commit()
        print(f"✓ Imported {len(data['organization_settings'])} organizations")

    # Import documents
    print(f"\nImporting {len(data['documents'])} documents...")
    for doc_data in data['documents']:
        doc = Document(
            id=doc_data['id'],
            filename=doc_data['filename'],
            content=doc_data['content'],
            uploaded_by=doc_data['uploaded_by'],
            organization=doc_data.get('organization'),
            created_at=parse_datetime(doc_data.get('created_at'))
        )
        session.merge(doc)
    session.commit()
    print(f"✓ Imported {len(data['documents'])} documents")

    # Import questions
    print(f"\nImporting {len(data['questions'])} questions...")
    for q_data in data['questions']:
        question = Question(
            id=q_data['id'],
            question_text=q_data['question_text'],
            question_type=q_data.get('question_type', 'mcq'),
            options_json=q_data.get('options_json'),
            correct_answer=q_data.get('correct_answer'),
            model_answer=q_data.get('model_answer'),
            key_points=q_data.get('key_points'),
            explanation=q_data.get('explanation'),
            document_id=q_data['document_id'],
            difficulty=q_data.get('difficulty', 'medium'),
            status=q_data.get('status', 'pending'),
            created_by=q_data.get('created_by'),
            created_at=parse_datetime(q_data.get('created_at'))
        )
        session.merge(question)
    session.commit()
    print(f"✓ Imported {len(data['questions'])} questions")

    # Import exams
    print(f"\nImporting {len(data['exams'])} exams...")
    for exam_data in data['exams']:
        exam = Exam(
            id=exam_data['id'],
            user_id=exam_data['user_id'],
            score=exam_data.get('score'),
            total_questions=exam_data['total_questions'],
            completed_at=parse_datetime(exam_data.get('completed_at')),
            created_at=parse_datetime(exam_data.get('created_at'))
        )
        session.merge(exam)
    session.commit()
    print(f"✓ Imported {len(data['exams'])} exams")

    # Import exam questions
    print(f"\nImporting {len(data['exam_questions'])} exam questions...")
    for eq_data in data['exam_questions']:
        exam_question = ExamQuestion(
            id=eq_data['id'],
            exam_id=eq_data['exam_id'],
            question_id=eq_data['question_id'],
            user_answer=eq_data.get('user_answer'),
            is_correct=eq_data.get('is_correct'),
            time_spent=eq_data.get('time_spent'),
            created_at=parse_datetime(eq_data.get('created_at'))
        )
        session.merge(exam_question)
    session.commit()
    print(f"✓ Imported {len(data['exam_questions'])} exam questions")

    session.close()

    print("\n" + "="*60)
    print("✓ IMPORT COMPLETE!")
    print("="*60)
    print(f"Total records imported:")
    print(f"  - Users: {len(data['users'])}")
    print(f"  - Organizations: {len(data.get('organization_settings', []))}")
    print(f"  - Documents: {len(data['documents'])}")
    print(f"  - Questions: {len(data['questions'])}")
    print(f"  - Exams: {len(data['exams'])}")
    print(f"  - Exam Questions: {len(data['exam_questions'])}")
    print("="*60)

if __name__ == '__main__':
    import sys

    # Check for clear flag
    clear_existing = '--clear' in sys.argv or '-c' in sys.argv

    # Check for custom filename
    filename = 'exam_data_export.json'
    for arg in sys.argv[1:]:
        if not arg.startswith('-'):
            filename = arg
            break

    print("\nUsage:")
    print("  python import_data.py [filename] [--clear]")
    print("\nOptions:")
    print("  filename  - JSON export file (default: exam_data_export.json)")
    print("  --clear   - Clear existing data before import")
    print("")

    try:
        import_data(filename, clear_existing)
    except Exception as e:
        print(f"\n✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
