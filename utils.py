"""
Utility functions for file processing and text extraction
"""
import os
import PyPDF2
import docx
from datetime import datetime


def generate_unique_filename(original_filename):
    """
    Generate a unique filename to avoid collisions
    Format: timestamp_originalname.ext
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    name, ext = os.path.splitext(original_filename)
    # Sanitize the name
    name = ''.join(c for c in name if c.isalnum() or c in ('_', '-'))
    return f"{timestamp}_{name}{ext}"


def extract_text_from_pdf(file_path, max_pages=None):
    """
    Extract text content from a PDF file (optimized for large files)

    Args:
        file_path: Path to the PDF file
        max_pages: Maximum number of pages to extract (None for all)

    Returns:
        Extracted text as string
    """
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            num_pages = len(pdf_reader.pages)

            # Limit pages for very large PDFs
            if max_pages is None:
                pages_to_extract = num_pages
            else:
                pages_to_extract = min(num_pages, max_pages)

            text_content = []

            # Extract text from pages
            for page_num in range(pages_to_extract):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(page_text)
                except Exception as page_error:
                    # Skip problematic pages but continue
                    print(f"Warning: Could not extract page {page_num + 1}: {page_error}")
                    continue

            if not text_content:
                raise Exception("No text could be extracted from PDF")

            return '\n\n'.join(text_content)
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")


def extract_text_from_docx(file_path):
    """
    Extract text content from a DOCX file

    Args:
        file_path: Path to the DOCX file

    Returns:
        Extracted text as string
    """
    try:
        doc = docx.Document(file_path)
        text_content = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)

        return '\n\n'.join(text_content)
    except Exception as e:
        raise Exception(f"Error extracting text from DOCX: {str(e)}")


def extract_text_from_txt(file_path):
    """
    Extract text content from a TXT file

    Args:
        file_path: Path to the TXT file

    Returns:
        Extracted text as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error extracting text from TXT: {str(e)}")
    except Exception as e:
        raise Exception(f"Error extracting text from TXT: {str(e)}")


def extract_text_from_file(file_path):
    """
    Extract text from a file based on its extension

    Args:
        file_path: Path to the file

    Returns:
        Extracted text as string
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def get_file_size_mb(file_path):
    """
    Get file size in megabytes

    Args:
        file_path: Path to the file

    Returns:
        File size in MB as float
    """
    size_bytes = os.path.getsize(file_path)
    return round(size_bytes / (1024 * 1024), 2)


def validate_file_content(text_content, min_length=10):
    """
    Validate that extracted text has meaningful content

    Args:
        text_content: Extracted text
        min_length: Minimum character length

    Returns:
        Boolean indicating if content is valid
    """
    if not text_content:
        return False

    # Remove whitespace and check length
    cleaned_content = text_content.strip()
    return len(cleaned_content) >= min_length


# ============================================================================
# QUESTION VALIDATION FUNCTIONS
# ============================================================================

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional


def validate_question_length(question_text: str, min_length: int = 20, max_length: int = 500) -> Tuple[bool, str]:
    """
    Validate question text length

    Args:
        question_text: The question text to validate
        min_length: Minimum allowed characters
        max_length: Maximum allowed characters

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not question_text or not question_text.strip():
        return False, "Question text cannot be empty"

    text_length = len(question_text.strip())

    if text_length < min_length:
        return False, f"Question is too short (minimum {min_length} characters, got {text_length})"

    if text_length > max_length:
        return False, f"Question is too long (maximum {max_length} characters, got {text_length})"

    return True, ""


def validate_mcq_options(options: Dict[str, str]) -> Tuple[bool, str]:
    """
    Validate MCQ options format and content

    Args:
        options: Dictionary of options (A, B, C, D)

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_keys = ['A', 'B', 'C', 'D']

    # Check if all required keys exist
    if not options:
        return False, "Options cannot be empty"

    missing_keys = [key for key in required_keys if key not in options]
    if missing_keys:
        return False, f"Missing options: {', '.join(missing_keys)}"

    # Check if all options have content
    for key, value in options.items():
        if not value or not str(value).strip():
            return False, f"Option {key} cannot be empty"

    # Check option lengths
    for key, value in options.items():
        option_length = len(str(value).strip())
        if option_length < 1:
            return False, f"Option {key} is too short"
        if option_length > 300:
            return False, f"Option {key} is too long (maximum 300 characters)"

    # Check for duplicate options
    option_values = [str(v).strip().lower() for v in options.values()]
    if len(option_values) != len(set(option_values)):
        return False, "Options contain duplicates"

    return True, ""


def validate_correct_answer(correct_answer: str, question_type: str, options: Optional[Dict] = None) -> Tuple[bool, str]:
    """
    Validate that the correct answer is valid for the question type

    Args:
        correct_answer: The correct answer value
        question_type: Type of question (mcq, true_false, short_answer)
        options: Dictionary of options (for MCQ)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not correct_answer:
        return False, "Correct answer cannot be empty"

    if question_type == 'mcq':
        if correct_answer not in ['A', 'B', 'C', 'D']:
            return False, f"Invalid MCQ answer '{correct_answer}'. Must be A, B, C, or D"

        if options and correct_answer not in options:
            return False, f"Correct answer '{correct_answer}' not found in options"

    elif question_type == 'true_false':
        valid_answers = ['true', 'false', 'True', 'False', True, False]
        if correct_answer not in valid_answers:
            return False, f"Invalid True/False answer. Must be 'true' or 'false'"

    return True, ""


def check_duplicate_question(question_text: str, existing_questions: List[str], threshold: float = 0.85) -> Tuple[bool, Optional[str]]:
    """
    Check if a question is too similar to existing questions

    Args:
        question_text: The question to check
        existing_questions: List of existing question texts
        threshold: Similarity threshold (0.0 to 1.0)

    Returns:
        Tuple of (is_duplicate, similar_question)
    """
    if not existing_questions:
        return False, None

    question_normalized = question_text.strip().lower()

    for existing in existing_questions:
        existing_normalized = existing.strip().lower()

        # Calculate similarity ratio
        similarity = SequenceMatcher(None, question_normalized, existing_normalized).ratio()

        if similarity >= threshold:
            return True, existing

    return False, None


def calculate_difficulty_score(question_text: str, options: Optional[Dict] = None) -> str:
    """
    Auto-calculate difficulty level based on question characteristics

    Args:
        question_text: The question text
        options: Dictionary of options (for MCQ)

    Returns:
        Difficulty level: 'easy', 'medium', or 'hard'
    """
    score = 0

    # Factor 1: Question length
    question_length = len(question_text.strip())
    if question_length > 150:
        score += 2
    elif question_length > 80:
        score += 1

    # Factor 2: Complexity indicators in question
    complexity_keywords = [
        'analyze', 'evaluate', 'compare', 'contrast', 'explain why',
        'justify', 'critique', 'synthesize', 'infer', 'predict',
        'how would', 'what if', 'why do you think'
    ]

    question_lower = question_text.lower()
    for keyword in complexity_keywords:
        if keyword in question_lower:
            score += 1
            break

    # Factor 3: Simple recall keywords (reduce score)
    simple_keywords = ['what is', 'who is', 'when did', 'where is', 'define', 'list']
    for keyword in simple_keywords:
        if keyword in question_lower:
            score -= 1
            break

    # Factor 4: Multiple choice option complexity
    if options:
        avg_option_length = sum(len(str(v)) for v in options.values()) / len(options)
        if avg_option_length > 100:
            score += 2
        elif avg_option_length > 50:
            score += 1

        # Check if options are very similar (harder question)
        option_values = [str(v).lower() for v in options.values()]
        total_similarity = 0
        comparisons = 0

        for i in range(len(option_values)):
            for j in range(i + 1, len(option_values)):
                similarity = SequenceMatcher(None, option_values[i], option_values[j]).ratio()
                total_similarity += similarity
                comparisons += 1

        if comparisons > 0:
            avg_similarity = total_similarity / comparisons
            if avg_similarity > 0.6:
                score += 2

    # Determine difficulty based on score
    if score <= 0:
        return 'easy'
    elif score <= 3:
        return 'medium'
    else:
        return 'hard'


def auto_fix_question_formatting(question_text: str) -> str:
    """
    Automatically fix common formatting issues in question text

    Args:
        question_text: The question text to fix

    Returns:
        Fixed question text
    """
    if not question_text:
        return question_text

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', question_text.strip())

    # Ensure question ends with proper punctuation
    if text and text[-1] not in '.?!':
        # Add question mark if it looks like a question
        question_starters = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should']
        first_word = text.split()[0].lower() if text.split() else ''

        if first_word in question_starters:
            text += '?'
        else:
            text += '.'

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # Fix common spacing issues
    text = re.sub(r'\s+([?.!,;:])', r'\1', text)  # Remove space before punctuation
    text = re.sub(r'([?.!,;:])([^\s])', r'\1 \2', text)  # Add space after punctuation

    # Fix multiple punctuation
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\?{2,}', '?', text)

    return text


def auto_fix_option_formatting(option_text: str) -> str:
    """
    Automatically fix formatting issues in option text

    Args:
        option_text: The option text to fix

    Returns:
        Fixed option text
    """
    if not option_text:
        return option_text

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', option_text.strip())

    # Capitalize first letter
    if text:
        text = text[0].upper() + text[1:]

    # Remove trailing punctuation (options don't need it)
    while text and text[-1] in '.?!':
        text = text[:-1].strip()

    # Fix spacing issues
    text = re.sub(r'\s+([,;:])', r'\1', text)
    text = re.sub(r'([,;:])([^\s])', r'\1 \2', text)

    return text


def validate_question_complete(
    question_text: str,
    question_type: str,
    correct_answer: Optional[str] = None,
    options: Optional[Dict] = None,
    existing_questions: Optional[List[str]] = None,
    auto_fix: bool = True
) -> Tuple[bool, List[str], Dict[str, any]]:
    """
    Comprehensive question validation with optional auto-fixing

    Args:
        question_text: The question text
        question_type: Type of question (mcq, true_false, short_answer)
        correct_answer: The correct answer
        options: Dictionary of options (for MCQ)
        existing_questions: List of existing questions to check for duplicates
        auto_fix: Whether to auto-fix formatting issues

    Returns:
        Tuple of (is_valid, errors_list, fixed_data)
    """
    errors = []
    fixed_data = {
        'question_text': question_text,
        'options': options,
        'difficulty': 'medium'
    }

    # Auto-fix if enabled
    if auto_fix:
        fixed_data['question_text'] = auto_fix_question_formatting(question_text)

        if options and question_type == 'mcq':
            fixed_data['options'] = {
                key: auto_fix_option_formatting(value)
                for key, value in options.items()
            }

    # Validate question length
    is_valid, error = validate_question_length(fixed_data['question_text'])
    if not is_valid:
        errors.append(error)

    # Validate question type specific requirements
    if question_type == 'mcq':
        if not options:
            errors.append("MCQ questions require options")
        else:
            is_valid, error = validate_mcq_options(fixed_data['options'])
            if not is_valid:
                errors.append(error)

            # Validate correct answer
            if correct_answer:
                is_valid, error = validate_correct_answer(correct_answer, question_type, fixed_data['options'])
                if not is_valid:
                    errors.append(error)

    elif question_type == 'true_false':
        if correct_answer:
            is_valid, error = validate_correct_answer(correct_answer, question_type)
            if not is_valid:
                errors.append(error)

    # Check for duplicates
    if existing_questions:
        is_duplicate, similar = check_duplicate_question(
            fixed_data['question_text'],
            existing_questions
        )
        if is_duplicate:
            errors.append(f"Question is too similar to existing question: '{similar[:100]}...'")

    # Calculate difficulty
    if question_type == 'mcq' and fixed_data['options']:
        fixed_data['difficulty'] = calculate_difficulty_score(
            fixed_data['question_text'],
            fixed_data['options']
        )
    else:
        fixed_data['difficulty'] = calculate_difficulty_score(fixed_data['question_text'])

    return len(errors) == 0, errors, fixed_data
