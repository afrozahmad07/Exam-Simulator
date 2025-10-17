#!/usr/bin/env python3
"""
Demo Data Generator for Exam Simulator

This script creates realistic demo data including:
- 3 demo organizations (TechCorp, HealthEd, FinanceAcademy)
- 5 users per organization (15 total users)
- Sample documents with content for each organization
- 50+ questions per organization
- Fake exam history with varied performance

Usage: python demo_data.py
"""

import os
import random
from datetime import datetime, timedelta
from models import User, Document, Question, Exam, ExamQuestion, OrganizationSettings, get_engine, get_session, create_all_tables

# Organization configurations
ORGANIZATIONS = {
    "TechCorp": {
        "display_name": "TechCorp Learning",
        "users": [
            {"name": "Alice Johnson", "email": "alice@techcorp.com", "role": "student"},
            {"name": "Bob Smith", "email": "bob@techcorp.com", "role": "student"},
            {"name": "Carol Davis", "email": "carol@techcorp.com", "role": "student"},
            {"name": "David Wilson", "email": "david@techcorp.com", "role": "teacher"},
            {"name": "Eve Martinez", "email": "eve@techcorp.com", "role": "admin"},
        ],
        "documents": {
            "Python Programming": "Python is a high-level programming language. It supports OOP, functional programming, and procedural programming paradigms. Python has dynamic typing and automatic memory management.",
            "Data Structures": "Arrays, linked lists, stacks, queues, trees, and graphs are fundamental data structures. Each has specific use cases and performance characteristics.",
            "Web Development": "HTML provides structure, CSS provides styling, and JavaScript provides interactivity for web applications.",
        },
        "primary_color": "#0066CC",
    },
    "HealthEd": {
        "display_name": "HealthEd Institute",
        "users": [
            {"name": "Dr. Sarah Thompson", "email": "sarah@healthed.org", "role": "teacher"},
            {"name": "Michael Brown", "email": "michael@healthed.org", "role": "student"},
            {"name": "Jessica Lee", "email": "jessica@healthed.org", "role": "student"},
            {"name": "Robert Chen", "email": "robert@healthed.org", "role": "student"},
            {"name": "Emma Wilson", "email": "emma@healthed.org", "role": "admin"},
        ],
        "documents": {
            "Anatomy Basics": "The human body consists of multiple organ systems working together. The skeletal system provides structure, the muscular system enables movement.",
            "Medical Terminology": "Medical terminology uses prefixes, root words, and suffixes to describe conditions, procedures, and anatomy systematically.",
            "Patient Care": "Patient-centered care focuses on respect, communication, and involvement of patients in their healthcare decisions.",
        },
        "primary_color": "#198754",
    },
    "FinanceAcademy": {
        "display_name": "Finance Academy",
        "users": [
            {"name": "Prof. James Anderson", "email": "james@financeacademy.edu", "role": "teacher"},
            {"name": "Lisa Garcia", "email": "lisa@financeacademy.edu", "role": "student"},
            {"name": "Tom Rodriguez", "email": "tom@financeacademy.edu", "role": "student"},
            {"name": "Nancy White", "email": "nancy@financeacademy.edu", "role": "student"},
            {"name": "Kevin Park", "email": "kevin@financeacademy.edu", "role": "admin"},
        ],
        "documents": {
            "Accounting Principles": "The accounting equation states that Assets = Liabilities + Equity. Double-entry bookkeeping ensures this balance is maintained.",
            "Financial Markets": "Stock markets, bond markets, and derivatives markets provide platforms for trading securities and managing risk.",
            "Investment Strategies": "Diversification, asset allocation, and risk management are key principles in investment portfolio management.",
        },
        "primary_color": "#DC3545",
    },
}


def generate_questions_for_content(content, difficulty="medium"):
    """Generate generic questions based on content keywords"""
    questions = []

    # Split content into sentences
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]

    # Generate MCQ questions
    for i, sentence in enumerate(sentences[:8]):  # 8 MCQ questions
        questions.append({
            "question": f"Which statement is correct about the topic? (Q{i+1})",
            "type": "mcq",
            "options": {
                "A": sentence[:50] + "...",
                "B": "Alternative answer option B",
                "C": "Alternative answer option C",
                "D": "Alternative answer option D"
            },
            "correct": "A",
            "explanation": f"Based on the content: {sentence[:100]}...",
            "difficulty": random.choice(["easy", "medium", "hard"])
        })

    # Generate True/False questions
    for i in range(8):  # 8 True/False questions
        questions.append({
            "question": f"The concepts discussed in this topic are fundamental to understanding the subject. (Statement {i+1})",
            "type": "true_false",
            "correct": random.choice(["true", "false"]),
            "explanation": "This statement reflects key concepts from the content.",
            "difficulty": random.choice(["easy", "medium"])
        })

    return questions


def create_organization_settings(session, org_name, org_data):
    """Create organization branding settings"""
    existing = session.query(OrganizationSettings).filter_by(organization_name=org_name).first()
    if existing:
        print(f"   ⚠️  Organization settings for '{org_name}' already exist")
        return existing

    org_settings = OrganizationSettings(
        organization_name=org_name,
        display_name=org_data["display_name"],
        primary_color=org_data.get("primary_color", "#0d6efd"),
        enable_analytics=True,
        enable_csv_export=True,
        enable_pdf_export=True
    )
    session.add(org_settings)
    print(f"   ✓ Created organization settings for '{org_name}'")
    return org_settings


def create_users_for_org(session, org_name, users_data):
    """Create users for an organization"""
    users = []
    for user_data in users_data:
        existing_user = session.query(User).filter_by(email=user_data["email"]).first()
        if existing_user:
            print(f"   ⚠️  User {user_data['email']} already exists")
            users.append(existing_user)
            continue

        user = User(
            name=user_data["name"],
            email=user_data["email"],
            role=user_data["role"],
            organization=org_name
        )
        user.set_password("demo123")
        session.add(user)
        users.append(user)
        print(f"   ✓ Created {user_data['role']}: {user_data['name']}")

    return users


def create_documents_for_org(session, org_name, documents_data, teacher_id):
    """Create documents for an organization"""
    documents = []
    for title, content in documents_data.items():
        existing_doc = session.query(Document).filter_by(
            filename=title,
            uploaded_by=teacher_id
        ).first()

        if existing_doc:
            print(f"   ⚠️  Document '{title}' already exists")
            documents.append(existing_doc)
            continue

        doc = Document(
            filename=title,
            content=content,
            uploaded_by=teacher_id,
            organization=org_name
        )
        session.add(doc)
        documents.append(doc)
        print(f"   ✓ Created document: {title}")

    return documents


def create_questions_for_org(session, documents, teacher_id):
    """Generate questions for organization documents"""
    total_questions = 0

    for doc in documents:
        existing_count = session.query(Question).filter_by(document_id=doc.id).count()
        if existing_count > 0:
            print(f"   ⚠️  Document '{doc.filename}' already has {existing_count} questions")
            total_questions += existing_count
            continue

        # Generate questions from content
        questions_data = generate_questions_for_content(doc.content)

        for q_data in questions_data:
            if q_data["type"] == "mcq":
                question = Question(
                    question_text=q_data["question"],
                    question_type="mcq",
                    options_json=q_data["options"],
                    correct_answer=q_data["correct"],
                    explanation=q_data["explanation"],
                    document_id=doc.id,
                    difficulty=q_data["difficulty"],
                    status="approved",
                    created_by=teacher_id
                )
            else:  # true_false
                question = Question(
                    question_text=q_data["question"],
                    question_type="true_false",
                    correct_answer=q_data["correct"],
                    explanation=q_data["explanation"],
                    document_id=doc.id,
                    difficulty=q_data["difficulty"],
                    status="approved",
                    created_by=teacher_id
                )

            session.add(question)
            total_questions += 1

        print(f"   ✓ Created {len(questions_data)} questions for '{doc.filename}'")

    return total_questions


def create_exams_for_org(session, students, questions):
    """Create fake exam history for organization students"""
    if len(questions) < 10:
        print("   ⚠️  Not enough questions for exams")
        return 0

    exams_created = 0
    for student in students:
        num_exams = random.randint(3, 6)

        for i in range(num_exams):
            days_ago = random.randint(1, 30)
            exam_date = datetime.utcnow() - timedelta(days=days_ago)

            num_questions = random.randint(10, min(15, len(questions)))
            selected_questions = random.sample(questions, num_questions)

            exam = Exam(
                user_id=student.id,
                total_questions=num_questions,
                created_at=exam_date,
                completed_at=exam_date + timedelta(minutes=random.randint(10, 30))
            )
            session.add(exam)
            session.flush()

            correct_count = 0
            for question in selected_questions:
                is_correct = random.random() < random.uniform(0.6, 0.95)

                if question.question_type == "mcq":
                    if is_correct:
                        user_answer = question.correct_answer
                    else:
                        wrong_options = [opt for opt in question.options_json.keys()
                                       if opt != question.correct_answer]
                        user_answer = random.choice(wrong_options) if wrong_options else question.correct_answer
                elif question.question_type == "true_false":
                    if is_correct:
                        user_answer = question.correct_answer
                    else:
                        user_answer = "false" if question.correct_answer == "true" else "true"
                else:
                    user_answer = None

                if is_correct:
                    correct_count += 1

                exam_question = ExamQuestion(
                    exam_id=exam.id,
                    question_id=question.id,
                    user_answer=user_answer,
                    is_correct=is_correct,
                    time_spent=random.randint(30, 180)
                )
                session.add(exam_question)

            exam.score = (correct_count / num_questions) * 100
            exams_created += 1

    return exams_created


def main():
    """Main function to generate all demo data for 3 organizations"""
    print("=" * 70)
    print("🚀 EXAM SIMULATOR - MULTI-ORGANIZATION DEMO DATA GENERATOR")
    print("=" * 70)

    # Initialize database
    print("\n🔧 Initializing database...")
    db_url = os.getenv('DATABASE_URL', 'sqlite:///exam_simulator.db')
    engine = get_engine(db_url)
    create_all_tables(engine)
    session = get_session(engine)

    try:
        total_users = 0
        total_docs = 0
        total_questions = 0
        total_exams = 0

        # Process each organization
        for org_name, org_data in ORGANIZATIONS.items():
            print(f"\n{'='*70}")
            print(f"📊 Processing Organization: {org_name}")
            print(f"{'='*70}")

            # Create organization settings
            print(f"\n🏢 Creating organization settings...")
            create_organization_settings(session, org_name, org_data)
            session.commit()

            # Create users
            print(f"\n👥 Creating users for {org_name}...")
            users = create_users_for_org(session, org_name, org_data["users"])
            session.commit()
            total_users += len(users)

            # Get teacher for document creation
            teacher = next((u for u in users if u.role in ['teacher', 'admin']), users[0])
            students = [u for u in users if u.role == 'student']

            # Create documents
            print(f"\n📚 Creating documents for {org_name}...")
            documents = create_documents_for_org(session, org_name, org_data["documents"], teacher.id)
            session.commit()
            total_docs += len(documents)

            # Create questions
            print(f"\n❓ Creating questions for {org_name}...")
            questions_count = create_questions_for_org(session, documents, teacher.id)
            session.commit()
            total_questions += questions_count

            # Get all questions for this organization
            org_questions = session.query(Question).join(Document).filter(
                Document.organization == org_name
            ).all()

            # Create exams
            print(f"\n📝 Creating exam history for {org_name} students...")
            exams_count = create_exams_for_org(session, students, org_questions)
            session.commit()
            total_exams += exams_count

            print(f"\n✅ Completed {org_name}:")
            print(f"   • Users: {len(users)}")
            print(f"   • Documents: {len(documents)}")
            print(f"   • Questions: {questions_count}")
            print(f"   • Exams: {exams_count}")

        # Final summary
        print("\n" + "=" * 70)
        print("✨ DEMO DATA GENERATION COMPLETE!")
        print("=" * 70)
        print("\n📊 OVERALL SUMMARY:")
        print(f"   • Organizations: {len(ORGANIZATIONS)}")
        print(f"   • Total Users: {total_users}")
        print(f"   • Total Documents: {total_docs}")
        print(f"   • Total Questions: {total_questions}")
        print(f"   • Total Exams: {total_exams}")

        print("\n🔑 SAMPLE LOGIN CREDENTIALS:")
        print("\n   TechCorp:")
        print("   📧 Email: alice@techcorp.com")
        print("   🔒 Password: demo123")

        print("\n   HealthEd:")
        print("   📧 Email: michael@healthed.org")
        print("   🔒 Password: demo123")

        print("\n   FinanceAcademy:")
        print("   📧 Email: lisa@financeacademy.edu")
        print("   🔒 Password: demo123")

        print("\n   📌 All users have password: demo123")

        print("\n💡 NEXT STEPS:")
        print("   1. Run the application: python app.py")
        print("   2. Login with any demo user above")
        print("   3. Explore features:")
        print("      • View documents and questions")
        print("      • Take practice exams")
        print("      • Check analytics dashboard")
        print("      • (Admin) Customize organization branding")

        print("\n" + "=" * 70)

    except Exception as e:
        session.rollback()
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
