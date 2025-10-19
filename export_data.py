import json
from datetime import datetime
from models import User, Document, Question, Exam, ExamQuestion, OrganizationSettings, get_engine, get_session

# Connect to SQLite database
engine = get_engine('sqlite:///exam_simulator.db')
session = get_session(engine)

# Initialize data structure
data = {
    'users': [],
    'organization_settings': [],
    'documents': [],
    'questions': [],
    'exams': [],
    'exam_questions': []
}

# Export users
print("Exporting users...")
for user in session.query(User).all():
    data['users'].append({
        'id': user.id,
        'email': user.email,
        'password_hash': user.password_hash,
        'name': user.name,
        'organization': user.organization,
        'role': user.role,
        'remember_token': user.remember_token,
        'ai_provider': user.ai_provider,
        'ai_model': user.ai_model,
        'created_at': user.created_at.isoformat() if user.created_at else None
    })

# Export organization settings
print("Exporting organization settings...")
for org in session.query(OrganizationSettings).all():
    data['organization_settings'].append({
        'id': org.id,
        'organization_name': org.organization_name,
        'display_name': org.display_name,
        'subdomain': org.subdomain,
        'url_path': org.url_path,
        'logo_filename': org.logo_filename,
        'favicon_filename': org.favicon_filename,
        'primary_color': org.primary_color,
        'secondary_color': org.secondary_color,
        'success_color': org.success_color,
        'danger_color': org.danger_color,
        'custom_css': org.custom_css,
        'custom_footer_html': org.custom_footer_html,
        'enable_analytics': org.enable_analytics,
        'enable_csv_export': org.enable_csv_export,
        'enable_pdf_export': org.enable_pdf_export,
        'contact_email': org.contact_email,
        'support_url': org.support_url,
        'openai_api_key': org.openai_api_key,
        'gemini_api_key': org.gemini_api_key,
        'created_at': org.created_at.isoformat() if org.created_at else None,
        'updated_at': org.updated_at.isoformat() if org.updated_at else None
    })

# Export documents
print("Exporting documents...")
for doc in session.query(Document).all():
    data['documents'].append({
        'id': doc.id,
        'filename': doc.filename,
        'content': doc.content,
        'uploaded_by': doc.uploaded_by,
        'organization': doc.organization,
        'created_at': doc.created_at.isoformat() if doc.created_at else None
    })

# Export questions
print("Exporting questions...")
for q in session.query(Question).all():
    data['questions'].append({
        'id': q.id,
        'question_text': q.question_text,
        'question_type': q.question_type,
        'options_json': q.options_json,
        'correct_answer': q.correct_answer,
        'model_answer': q.model_answer,
        'key_points': q.key_points,
        'explanation': q.explanation,
        'document_id': q.document_id,
        'difficulty': q.difficulty,
        'status': q.status,
        'created_by': q.created_by,
        'created_at': q.created_at.isoformat() if q.created_at else None
    })

# Export exams
print("Exporting exams...")
for exam in session.query(Exam).all():
    data['exams'].append({
        'id': exam.id,
        'user_id': exam.user_id,
        'score': exam.score,
        'total_questions': exam.total_questions,
        'completed_at': exam.completed_at.isoformat() if exam.completed_at else None,
        'created_at': exam.created_at.isoformat() if exam.created_at else None
    })

# Export exam questions
print("Exporting exam questions...")
for eq in session.query(ExamQuestion).all():
    data['exam_questions'].append({
        'id': eq.id,
        'exam_id': eq.exam_id,
        'question_id': eq.question_id,
        'user_answer': eq.user_answer,
        'is_correct': eq.is_correct,
        'time_spent': eq.time_spent,
        'created_at': eq.created_at.isoformat() if eq.created_at else None
    })

# Save to JSON file
print("\nWriting to file...")
with open('exam_data_export.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\n" + "="*50)
print("EXPORT COMPLETE!")
print("="*50)
print(f"Users: {len(data['users'])}")
print(f"Organizations: {len(data['organization_settings'])}")
print(f"Documents: {len(data['documents'])}")
print(f"Questions: {len(data['questions'])}")
print(f"Exams: {len(data['exams'])}")
print(f"Exam Questions: {len(data['exam_questions'])}")
print("="*50)
print(f"\nData exported to: exam_data_export.json")
print(f"File size: {len(json.dumps(data))/1024:.2f} KB")

session.close()
