# Google Gemini Integration Guide

## Overview
This guide explains how to add Google Gemini AI support alongside OpenAI, with model selection for Admin and Teacher roles.

## Changes Made

### 1. Database Changes (`models.py`)

Added AI preferences to User model:
```python
# AI Settings (for teachers and admins)
ai_provider = Column(String(50), default='gemini')  # 'openai' or 'gemini'
ai_model = Column(String(100), default='gemini-2.5-flash')  # Specific model name
```

### 2. Question Generator Updates (`question_generator.py`)

#### AI Models Configuration
```python
AI_MODELS = {
    'openai': {
        'gpt-4.1-mini-mini': 'GPT-4 (Most Capable)',
        'gpt-4.1-mini': 'GPT-4 Turbo (Fast & Capable)',
        'gpt-4.1-mini-mini': 'GPT-3.5 Turbo (Fast & Economical)',
        'gpt-4.1-mini': 'GPT-4o (Optimized)',
    },
    'gemini': {
        'gemini-2.5-flash': 'Gemini 2.0 Flash (Default - Fast & Latest)',
        'gemini-2.5-pro': 'Gemini Experimental 1206 (Advanced)',
        'gemini-2.0-flash-thinking-exp-1219': 'Gemini 2.0 Flash Thinking (Reasoning)',
        'Removed - see Oct 2025 models': 'Gemini 1.5 Pro (Balanced)',
        'Removed - see Oct 2025 models': 'Gemini 1.5 Flash (Fast)',
    }
}
```

#### Universal API Call Function
```python
def call_ai_api(prompt: str, provider: str = 'gemini', model: str = 'gemini-2.5-flash', temperature: float = 0.7):
    """Call either OpenAI or Gemini API"""
    if provider == 'openai':
        client = get_openai_client()
        response = client.chat.completions.create(...)
        return response.choices[0].message.content, None

    elif provider == 'gemini':
        configure_gemini()
        gemini_model = genai.GenerativeModel(model)
        response = gemini_model.generate_content(prompt, ...)
        return response.text, None
```

#### Updated Generation Functions
All generation functions now accept `provider` parameter:
```python
def generate_mcq_questions(text, num_questions=5, model="gemini-2.5-flash", temperature=0.7, provider='gemini'):
    # Uses call_ai_api() instead of direct OpenAI calls
```

### 3. App.py Routes

#### Settings Route (Admin/Teacher Only)
```python
@app.route('/settings', methods=['GET', 'POST'])
@login_required
@role_required('teacher', 'admin')
def settings():
    """AI Settings page for teachers and admins"""
    if request.method == 'POST':
        provider = request.form.get('ai_provider')
        model = request.form.get('ai_model')

        db_session = get_session(db_engine)
        try:
            current_user.ai_provider = provider
            current_user.ai_model = model
            db_session.commit()
            flash('AI settings updated successfully!', 'success')
        finally:
            db_session.close()

    return render_template('settings.html', ai_models=AI_MODELS)
```

#### Updated Generate Questions Route
```python
@app.route('/generate-questions/<int:document_id>', methods=['POST'])
def generate_questions(document_id):
    # Get user's AI preferences
    provider = current_user.ai_provider or 'gemini'
    model = current_user.ai_model or 'gemini-2.5-flash'

    # Pass to generation function
    results = generate_questions_mixed(
        text=document.content,
        num_mcq=num_mcq,
        num_true_false=num_true_false,
        num_short_answer=num_short_answer,
        provider=provider,
        model=model
    )
```

### 4. Settings Template (`templates/settings.html`)

```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <h1>AI Model Settings</h1>

    <form method="POST">
        <div class="mb-3">
            <label>AI Provider</label>
            <select name="ai_provider" class="form-select" id="providerSelect">
                <option value="gemini" {% if current_user.ai_provider == 'gemini' %}selected{% endif %}>
                    Google Gemini
                </option>
                <option value="openai" {% if current_user.ai_provider == 'openai' %}selected{% endif %}>
                    OpenAI
                </option>
            </select>
        </div>

        <div class="mb-3">
            <label>AI Model</label>
            <select name="ai_model" class="form-select" id="modelSelect">
                {% for provider_name, models in ai_models.items() %}
                    <optgroup label="{{ provider_name|upper }}">
                        {% for model_id, model_name in models.items() %}
                            <option value="{{ model_id }}"
                                    data-provider="{{ provider_name }}"
                                    {% if current_user.ai_model == model_id %}selected{% endif %}>
                                {{ model_name }}
                            </option>
                        {% endfor %}
                    </optgroup>
                {% endfor %}
            </select>
        </div>

        <button type="submit" class="btn btn-primary">Save Settings</button>
    </form>
</div>
{% endblock %}
```

### 5. Database Migration

Update `migrate_db.py`:
```python
migrations = [
    ('ai_provider', "ALTER TABLE users ADD COLUMN ai_provider VARCHAR(50) DEFAULT 'gemini'"),
    ('ai_model', "ALTER TABLE users ADD COLUMN ai_model VARCHAR(100) DEFAULT 'gemini-2.5-flash'"),
]

for column_name, sql in migrations:
    if column_name not in user_columns:
        print(f"  Adding {column_name} column...")
        cursor.execute(sql)
```

### 6. Environment Variables

Add to `.env` file:
```bash
# OpenAI API Key (optional if using Gemini)
OPENAI_API_KEY=your-openai-key

# Google Gemini API Key (default provider)
GEMINI_API_KEY=your-gemini-key
# OR
GOOGLE_API_KEY=your-gemini-key
```

### 7. Install Dependencies

```bash
pip install google-generativeai
```

## Usage

1. **For Admin/Teacher**:
   - Go to Settings page (new navigation link)
   - Select AI Provider (OpenAI or Gemini)
   - Choose specific model
   - Save settings

2. **For Students**:
   - Cannot access Settings
   - Use system default (Gemini 2.0 Flash)

3. **Question Generation**:
   - Uses user's selected provider and model
   - Falls back to Gemini 2.0 Flash if not set

## Model Recommendations

### Google Gemini (Default)
- **gemini-2.5-flash**: Fast, cost-effective, latest model (DEFAULT)
- **gemini-2.5-pro**: Advanced experimental features
- **Removed - see Oct 2025 models**: Best for complex questions
- **Removed - see Oct 2025 models**: Fastest responses

### OpenAI
- **gpt-4.1-mini**: Best overall quality
- **gpt-4.1-mini**: Fast and capable
- **gpt-4.1-mini-mini**: Most economical

## Implementation Steps

1. Run database migration: `python3 migrate_db.py`
2. Update `question_generator.py` with new functions
3. Add settings route to `app.py`
4. Create `settings.html` template
5. Update navigation in `base.html`
6. Install `google-generativeai`: `pip install google-generativeai`
7. Add Gemini API key to `.env` file
8. Restart application

## Benefits

✅ **Choice**: Users can select between OpenAI and Gemini
✅ **Cost-effective**: Gemini is more economical for high volume
✅ **Latest Models**: Access to newest AI capabilities
✅ **Flexibility**: Different models for different needs
✅ **Fallback**: If one provider fails, can switch to another
