"""
Question Generator Module
Generates different types of questions (MCQ, True/False, Short Answer) from text using AI APIs
Supports: OpenAI and Google Gemini
"""

import os
import json
import re
import time
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from openai import OpenAI
from functools import wraps
import google.generativeai as genai

# Initialize clients
openai_client = None
gemini_configured = False

# AI Model configurations
AI_MODELS = {
    'openai': {
        'gpt-4o-mini': 'GPT-4o Mini (Fast & Economical)',
        'gpt-4.1-mini': 'GPT-4.1 Mini (Latest)',
    },
    'gemini': {
        'gemini-2.5-flash': 'Gemini 2.5 Flash (Default - Fast & Latest)',
        'gemini-2.5-pro': 'Gemini 2.5 Pro (Most Capable)',
    }
}


def get_openai_client():
    """Get or initialize OpenAI client"""
    global openai_client
    if openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file")
        openai_client = OpenAI(api_key=api_key)
    return openai_client


def configure_gemini():
    """Configure Google Gemini API"""
    global gemini_configured
    if not gemini_configured:
        api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in .env file")
        genai.configure(api_key=api_key)
        gemini_configured = True


# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10  # Max requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds
request_timestamps = []


# ============================================================================
# RATE LIMITING DECORATOR
# ============================================================================

def rate_limit(max_calls: int = RATE_LIMIT_REQUESTS, time_window: int = RATE_LIMIT_WINDOW):
    """
    Decorator to enforce rate limiting on API calls

    Args:
        max_calls: Maximum number of calls allowed within time_window
        time_window: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global request_timestamps
            now = datetime.now()

            # Remove timestamps older than the time window
            request_timestamps = [
                ts for ts in request_timestamps
                if now - ts < timedelta(seconds=time_window)
            ]

            # Check if we've exceeded the rate limit
            if len(request_timestamps) >= max_calls:
                oldest_request = min(request_timestamps)
                sleep_time = (oldest_request + timedelta(seconds=time_window) - now).total_seconds()
                if sleep_time > 0:
                    print(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                    time.sleep(sleep_time)
                    # Clean up old timestamps again after sleeping
                    request_timestamps = [
                        ts for ts in request_timestamps
                        if datetime.now() - ts < timedelta(seconds=time_window)
                    ]

            # Add current timestamp and make the call
            request_timestamps.append(datetime.now())
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

MCQ_PROMPT_TEMPLATE = """Generate {num_questions} multiple choice questions from the following text.
Each question should have 4 options (A, B, C, D) with exactly one correct answer.

Text:
{text}

Requirements:
- Questions should test understanding, not just memorization
- Options should be plausible and of similar length
- Avoid "all of the above" or "none of the above" options
- Vary difficulty levels

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "options": {{
      "A": "First option",
      "B": "Second option",
      "C": "Third option",
      "D": "Fourth option"
    }},
    "correct_answer": "A",
    "explanation": "Brief explanation of why this is correct"
  }}
]

Return ONLY the JSON array, no other text."""

TRUE_FALSE_PROMPT_TEMPLATE = """Generate {num_questions} True/False questions from the following text.
Each question should be a clear statement that is definitively true or false based on the text.

Text:
{text}

Requirements:
- Statements should be unambiguous
- Avoid trick questions or double negatives
- Mix true and false answers
- Test key concepts from the text

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "Statement text here.",
    "correct_answer": true,
    "explanation": "Brief explanation of why this is true/false"
  }}
]

Return ONLY the JSON array, no other text."""

SHORT_ANSWER_PROMPT_TEMPLATE = """Generate {num_questions} short answer questions from the following text.
Each question should require a brief written response (1-3 sentences).

Text:
{text}

Requirements:
- Questions should encourage critical thinking
- Avoid questions with one-word answers
- Test understanding and application of concepts
- Provide comprehensive model answers

Format your response as a JSON array with this exact structure:
[
  {{
    "question": "Question text here?",
    "model_answer": "Expected answer (1-3 sentences)",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"]
  }}
]

Return ONLY the JSON array, no other text."""


# ============================================================================
# RESPONSE PARSING FUNCTIONS
# ============================================================================

def extract_json_from_response(response_text: str) -> Optional[List[Dict]]:
    """
    Extract and parse JSON from API response, handling various formats

    Args:
        response_text: Raw response text from API

    Returns:
        Parsed JSON as list of dictionaries, or None if parsing fails
    """
    try:
        # Try direct JSON parsing first
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON array in the response
    json_pattern = r'\[\s*\{.*?\}\s*\]'
    matches = re.findall(json_pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    # Try to find JSON between code blocks
    code_block_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
    matches = re.findall(code_block_pattern, response_text, re.DOTALL)

    for match in matches:
        try:
            return json.loads(match)
        except json.JSONDecodeError:
            continue

    return None


def validate_mcq_question(question: Dict) -> Tuple[bool, str]:
    """
    Validate MCQ question structure

    Args:
        question: Dictionary containing question data

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['question', 'options', 'correct_answer', 'explanation']

    for field in required_fields:
        if field not in question:
            return False, f"Missing required field: {field}"

    if not isinstance(question['options'], dict):
        return False, "Options must be a dictionary"

    required_options = ['A', 'B', 'C', 'D']
    for option in required_options:
        if option not in question['options']:
            return False, f"Missing option: {option}"

    if question['correct_answer'] not in required_options:
        return False, f"Invalid correct_answer: {question['correct_answer']}"

    return True, ""


def validate_true_false_question(question: Dict) -> Tuple[bool, str]:
    """
    Validate True/False question structure

    Args:
        question: Dictionary containing question data

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['question', 'correct_answer', 'explanation']

    for field in required_fields:
        if field not in question:
            return False, f"Missing required field: {field}"

    if not isinstance(question['correct_answer'], bool):
        return False, "correct_answer must be a boolean"

    return True, ""


def validate_short_answer_question(question: Dict) -> Tuple[bool, str]:
    """
    Validate Short Answer question structure

    Args:
        question: Dictionary containing question data

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['question', 'model_answer', 'key_points']

    for field in required_fields:
        if field not in question:
            return False, f"Missing required field: {field}"

    if not isinstance(question['key_points'], list):
        return False, "key_points must be a list"

    return True, ""


# ============================================================================
# AI PROVIDER FUNCTIONS
# ============================================================================

def call_ai_api(prompt: str, provider: str = 'gemini', model: str = 'gemini-2.5-flash', temperature: float = 0.7) -> Tuple[Optional[str], Optional[str]]:
    """
    Universal function to call either OpenAI or Gemini API

    Args:
        prompt: The prompt to send to the AI
        provider: 'openai' or 'gemini'
        model: Model name
        temperature: Sampling temperature

    Returns:
        Tuple of (response_text, error_message)
    """
    try:
        if provider == 'openai':
            client = get_openai_client()
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert educator who creates high-quality assessment questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=2000
            )
            return response.choices[0].message.content, None

        elif provider == 'gemini':
            configure_gemini()
            gemini_model = genai.GenerativeModel(model)
            response = gemini_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=2000,
                )
            )
            return response.text, None

        else:
            return None, f"Unknown AI provider: {provider}"

    except Exception as e:
        return None, f"API call failed: {str(e)}"


# ============================================================================
# QUESTION GENERATION FUNCTIONS
# ============================================================================

@rate_limit(max_calls=RATE_LIMIT_REQUESTS, time_window=RATE_LIMIT_WINDOW)
def generate_mcq_questions(
    text: str,
    num_questions: int = 5,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    provider: str = 'gemini'
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Generate multiple choice questions from text using AI API

    Args:
        text: Source text to generate questions from
        num_questions: Number of questions to generate
        model: AI model to use
        temperature: Sampling temperature (0.0 to 1.0)
        provider: 'openai' or 'gemini'

    Returns:
        Tuple of (questions_list, error_message)
        questions_list is None if generation fails
    """
    print(f"[MCQ] Starting generation with {num_questions} questions using {provider}/{model}")

    if not text or not text.strip():
        return None, "Input text cannot be empty"

    if num_questions < 1 or num_questions > 20:
        return None, "Number of questions must be between 1 and 20"

    try:
        # Prepare the prompt
        prompt = MCQ_PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            text=text[:4000]  # Limit text length to avoid token limits
        )

        print(f"[MCQ] Calling AI API...")

        # Call AI API (OpenAI or Gemini)
        response_text, error = call_ai_api(prompt, provider, model, temperature)

        if error:
            print(f"[MCQ] API Error: {error}")
            return None, error

        print(f"[MCQ] Received response, parsing JSON...")
        print(f"[MCQ] Response preview: {response_text[:200]}...")

        # Parse JSON from response
        questions = extract_json_from_response(response_text)

        if questions is None:
            print(f"[MCQ] Failed to parse JSON. Full response: {response_text}")
            return None, "Failed to parse JSON from API response"

        print(f"[MCQ] Parsed {len(questions)} questions, validating...")

        # Validate each question
        valid_questions = []
        for i, question in enumerate(questions):
            is_valid, error = validate_mcq_question(question)
            if is_valid:
                valid_questions.append(question)
                print(f"[MCQ] Question {i+1} validated successfully")
            else:
                print(f"[MCQ] Question {i+1} validation failed: {error}")
                print(f"[MCQ] Question data: {question}")

        if not valid_questions:
            print(f"[MCQ] No valid questions generated!")
            return None, "No valid questions were generated"

        print(f"[MCQ] Successfully generated {len(valid_questions)} valid questions")
        return valid_questions, None

    except Exception as e:
        error_message = f"Error generating MCQ questions: {str(e)}"
        print(error_message)
        return None, error_message


@rate_limit(max_calls=RATE_LIMIT_REQUESTS, time_window=RATE_LIMIT_WINDOW)
def generate_true_false_questions(
    text: str,
    num_questions: int = 5,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    provider: str = 'gemini'
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Generate True/False questions from text using AI API

    Args:
        text: Source text to generate questions from
        num_questions: Number of questions to generate
        model: AI model to use
        temperature: Sampling temperature (0.0 to 1.0)
        provider: 'openai' or 'gemini'

    Returns:
        Tuple of (questions_list, error_message)
        questions_list is None if generation fails
    """
    if not text or not text.strip():
        return None, "Input text cannot be empty"

    if num_questions < 1 or num_questions > 20:
        return None, "Number of questions must be between 1 and 20"

    try:
        # Prepare the prompt
        prompt = TRUE_FALSE_PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            text=text[:4000]  # Limit text length to avoid token limits
        )

        # Call AI API (OpenAI or Gemini)
        response_text, error = call_ai_api(prompt, provider, model, temperature)

        if error:
            return None, error

        # Parse JSON from response
        questions = extract_json_from_response(response_text)

        if questions is None:
            return None, "Failed to parse JSON from API response"

        # Validate each question
        valid_questions = []
        for i, question in enumerate(questions):
            is_valid, error = validate_true_false_question(question)
            if is_valid:
                valid_questions.append(question)
            else:
                print(f"Warning: Question {i+1} validation failed: {error}")

        if not valid_questions:
            return None, "No valid questions were generated"

        return valid_questions, None

    except Exception as e:
        error_message = f"Error generating True/False questions: {str(e)}"
        print(error_message)
        return None, error_message


@rate_limit(max_calls=RATE_LIMIT_REQUESTS, time_window=RATE_LIMIT_WINDOW)
def generate_short_answer_questions(
    text: str,
    num_questions: int = 5,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.7,
    provider: str = 'gemini'
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Generate Short Answer questions from text using AI API

    Args:
        text: Source text to generate questions from
        num_questions: Number of questions to generate
        model: AI model to use
        temperature: Sampling temperature (0.0 to 1.0)
        provider: 'openai' or 'gemini'

    Returns:
        Tuple of (questions_list, error_message)
        questions_list is None if generation fails
    """
    if not text or not text.strip():
        return None, "Input text cannot be empty"

    if num_questions < 1 or num_questions > 20:
        return None, "Number of questions must be between 1 and 20"

    try:
        # Prepare the prompt
        prompt = SHORT_ANSWER_PROMPT_TEMPLATE.format(
            num_questions=num_questions,
            text=text[:4000]  # Limit text length to avoid token limits
        )

        # Call AI API (OpenAI or Gemini)
        response_text, error = call_ai_api(prompt, provider, model, temperature)

        if error:
            return None, error

        # Parse JSON from response
        questions = extract_json_from_response(response_text)

        if questions is None:
            return None, "Failed to parse JSON from API response"

        # Validate each question
        valid_questions = []
        for i, question in enumerate(questions):
            is_valid, error = validate_short_answer_question(question)
            if is_valid:
                valid_questions.append(question)
            else:
                print(f"Warning: Question {i+1} validation failed: {error}")

        if not valid_questions:
            return None, "No valid questions were generated"

        return valid_questions, None

    except Exception as e:
        error_message = f"Error generating Short Answer questions: {str(e)}"
        print(error_message)
        return None, error_message


# ============================================================================
# BACKWARD COMPATIBILITY FUNCTIONS
# ============================================================================

def generate_questions_from_content(content, num_questions=10, difficulty='medium'):
    """
    Generate multiple choice questions from document content using AI
    (Backward compatibility function)

    Args:
        content: Text content from document
        num_questions: Number of questions to generate
        difficulty: Difficulty level (easy, medium, hard)

    Returns:
        List of question dictionaries
    """
    questions, error = generate_mcq_questions(
        text=content,
        num_questions=num_questions,
        model="gemini-2.5-flash",
        temperature=0.7,
        provider='gemini'
    )

    if error:
        raise ValueError(error)

    # Add difficulty to each question for backward compatibility
    for question in questions:
        question['difficulty'] = difficulty

    return questions


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_questions_mixed(
    text: str,
    num_mcq: int = 3,
    num_true_false: int = 2,
    num_short_answer: int = 2,
    model: str = "gemini-2.5-flash",
    provider: str = 'gemini'
) -> Dict[str, any]:
    """
    Generate a mix of different question types from text

    Args:
        text: Source text to generate questions from
        num_mcq: Number of MCQ questions
        num_true_false: Number of True/False questions
        num_short_answer: Number of Short Answer questions
        model: AI model to use
        provider: 'openai' or 'gemini'

    Returns:
        Dictionary with questions and any errors
    """
    results = {
        'mcq': [],
        'true_false': [],
        'short_answer': [],
        'errors': []
    }

    # Generate MCQs
    if num_mcq > 0:
        mcq_questions, error = generate_mcq_questions(text, num_mcq, model, temperature=0.7, provider=provider)
        if mcq_questions:
            results['mcq'] = mcq_questions
        if error:
            results['errors'].append(f"MCQ: {error}")
            print(f"MCQ Generation Error: {error}")  # Debug logging

    # Generate True/False
    if num_true_false > 0:
        tf_questions, error = generate_true_false_questions(text, num_true_false, model, temperature=0.7, provider=provider)
        if tf_questions:
            results['true_false'] = tf_questions
        if error:
            results['errors'].append(f"True/False: {error}")
            print(f"True/False Generation Error: {error}")  # Debug logging

    # Generate Short Answer
    if num_short_answer > 0:
        sa_questions, error = generate_short_answer_questions(text, num_short_answer, model, temperature=0.7, provider=provider)
        if sa_questions:
            results['short_answer'] = sa_questions
        if error:
            results['errors'].append(f"Short Answer: {error}")
            print(f"Short Answer Generation Error: {error}")  # Debug logging

    return results


def format_questions_for_display(questions: List[Dict], question_type: str) -> str:
    """
    Format questions for readable display

    Args:
        questions: List of question dictionaries
        question_type: Type of questions ('mcq', 'true_false', 'short_answer')

    Returns:
        Formatted string representation of questions
    """
    output = []

    for i, q in enumerate(questions, 1):
        output.append(f"\n{'='*60}")
        output.append(f"Question {i} ({question_type.upper()})")
        output.append('='*60)
        output.append(f"\n{q['question']}\n")

        if question_type == 'mcq':
            for option, text in q['options'].items():
                marker = "✓" if option == q['correct_answer'] else " "
                output.append(f"  [{marker}] {option}. {text}")
            output.append(f"\nExplanation: {q['explanation']}")

        elif question_type == 'true_false':
            answer = "TRUE" if q['correct_answer'] else "FALSE"
            output.append(f"Answer: {answer}")
            output.append(f"Explanation: {q['explanation']}")

        elif question_type == 'short_answer':
            output.append(f"Model Answer: {q['model_answer']}")
            output.append("\nKey Points:")
            for point in q['key_points']:
                output.append(f"  • {point}")

    return '\n'.join(output)


def generate_simple_questions(content, num_questions=5):
    """
    Generate simple questions without AI (fallback method)
    Creates basic questions from the content
    """
    questions = []

    # Split content into sentences
    sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 20]

    # Generate simple comprehension questions
    for i in range(min(num_questions, len(sentences))):
        sentence = sentences[i]

        # Create a simple fill-in-the-blank style question
        words = sentence.split()
        if len(words) > 5:
            # Pick a word in the middle
            blank_index = len(words) // 2
            answer_word = words[blank_index]

            # Create question
            question_words = words.copy()
            question_words[blank_index] = "______"
            question_text = f"Fill in the blank: {' '.join(question_words)}?"

            # Create options (including the correct answer)
            questions.append({
                "question": question_text,
                "options": {
                    "A": answer_word,
                    "B": "incorrect1",
                    "C": "incorrect2",
                    "D": "incorrect3"
                },
                "correct_answer": "A",
                "explanation": f"The correct word is '{answer_word}'",
                "difficulty": "medium"
            })

    return questions if questions else [{
        "question": "What is the main topic of this document?",
        "options": {
            "A": "The uploaded content",
            "B": "Random topic",
            "C": "Another topic",
            "D": "Different subject"
        },
        "correct_answer": "A",
        "explanation": "This is a sample question based on the document.",
        "difficulty": "easy"
    }]


# ============================================================================
# MAIN FUNCTION FOR TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with sample text
    sample_text = """
    Photosynthesis is the process by which plants convert light energy into chemical energy.
    This process occurs in chloroplasts, which contain the green pigment chlorophyll.
    During photosynthesis, plants take in carbon dioxide from the air and water from the soil.
    Using light energy, they convert these into glucose (a sugar) and oxygen.
    The oxygen is released into the atmosphere, while the glucose is used for energy or stored.
    This process is essential for life on Earth, as it produces oxygen and forms the base of most food chains.
    """

    print("Testing Question Generator...")
    print("\n" + "="*60)
    print("Generating Mixed Questions")
    print("="*60)

    results = generate_questions_mixed(
        text=sample_text,
        num_mcq=2,
        num_true_false=2,
        num_short_answer=1
    )

    if results['mcq']:
        print(format_questions_for_display(results['mcq'], 'mcq'))

    if results['true_false']:
        print(format_questions_for_display(results['true_false'], 'true_false'))

    if results['short_answer']:
        print(format_questions_for_display(results['short_answer'], 'short_answer'))

    if results['errors']:
        print("\n" + "="*60)
        print("ERRORS")
        print("="*60)
        for error in results['errors']:
            print(f"  • {error}")
