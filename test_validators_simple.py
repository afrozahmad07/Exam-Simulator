#!/usr/bin/env python3
"""
Simple standalone test for validation functions
Tests core validation logic without external dependencies
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional


# Copy of validation functions for standalone testing
def validate_question_length(question_text: str, min_length: int = 20, max_length: int = 500) -> Tuple[bool, str]:
    """Validate question text length"""
    if not question_text or not question_text.strip():
        return False, "Question text cannot be empty"

    text_length = len(question_text.strip())

    if text_length < min_length:
        return False, f"Question is too short (minimum {min_length} characters, got {text_length})"

    if text_length > max_length:
        return False, f"Question is too long (maximum {max_length} characters, got {text_length})"

    return True, ""


def validate_mcq_options(options: Dict[str, str]) -> Tuple[bool, str]:
    """Validate MCQ options format and content"""
    required_keys = ['A', 'B', 'C', 'D']

    if not options:
        return False, "Options cannot be empty"

    missing_keys = [key for key in required_keys if key not in options]
    if missing_keys:
        return False, f"Missing options: {', '.join(missing_keys)}"

    for key, value in options.items():
        if not value or not str(value).strip():
            return False, f"Option {key} cannot be empty"

    for key, value in options.items():
        option_length = len(str(value).strip())
        if option_length < 1:
            return False, f"Option {key} is too short"
        if option_length > 300:
            return False, f"Option {key} is too long (maximum 300 characters)"

    option_values = [str(v).strip().lower() for v in options.values()]
    if len(option_values) != len(set(option_values)):
        return False, "Options contain duplicates"

    return True, ""


def auto_fix_question_formatting(question_text: str) -> str:
    """Automatically fix common formatting issues"""
    if not question_text:
        return question_text

    text = re.sub(r'\s+', ' ', question_text.strip())

    if text and text[-1] not in '.?!':
        question_starters = ['what', 'when', 'where', 'who', 'why', 'how', 'which', 'is', 'are', 'do', 'does', 'can', 'could', 'would', 'should']
        first_word = text.split()[0].lower() if text.split() else ''

        if first_word in question_starters:
            text += '?'
        else:
            text += '.'

    if text:
        text = text[0].upper() + text[1:]

    text = re.sub(r'\s+([?.!,;:])', r'\1', text)
    text = re.sub(r'([?.!,;:])([^\s])', r'\1 \2', text)
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'\?{2,}', '?', text)

    return text


def check_duplicate_question(question_text: str, existing_questions: List[str], threshold: float = 0.85) -> Tuple[bool, Optional[str]]:
    """Check if question is duplicate"""
    if not existing_questions:
        return False, None

    question_normalized = question_text.strip().lower()

    for existing in existing_questions:
        existing_normalized = existing.strip().lower()
        similarity = SequenceMatcher(None, question_normalized, existing_normalized).ratio()

        if similarity >= threshold:
            return True, existing

    return False, None


def calculate_difficulty_score(question_text: str, options: Optional[Dict] = None) -> str:
    """Calculate difficulty level"""
    score = 0

    question_length = len(question_text.strip())
    if question_length > 150:
        score += 2
    elif question_length > 80:
        score += 1

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

    simple_keywords = ['what is', 'who is', 'when did', 'where is', 'define', 'list']
    for keyword in simple_keywords:
        if keyword in question_lower:
            score -= 1
            break

    if score <= 0:
        return 'easy'
    elif score <= 3:
        return 'medium'
    else:
        return 'hard'


# Test functions
def test_all():
    """Run all validation tests"""
    print("\n" + "=" * 70)
    print(" QUESTION VALIDATION TEST RESULTS")
    print("=" * 70)

    # Test 1: Question Length
    print("\n1. QUESTION LENGTH VALIDATION")
    print("-" * 70)

    test_cases = [
        ("What is photosynthesis?", True, "Valid question"),
        ("Too short", False, "Too short"),
        ("", False, "Empty question"),
    ]

    for question, expected, desc in test_cases:
        is_valid, error = validate_question_length(question)
        status = "✓" if is_valid == expected else "✗"
        print(f"{status} {desc}: {'PASS' if is_valid == expected else 'FAIL'}")
        if error:
            print(f"   Error: {error}")

    # Test 2: MCQ Options
    print("\n2. MCQ OPTIONS VALIDATION")
    print("-" * 70)

    options_valid = {'A': 'CO2', 'B': 'O2', 'C': 'H2O', 'D': 'N2'}
    options_missing = {'A': 'CO2', 'B': 'O2', 'C': 'H2O'}
    options_duplicate = {'A': 'Same', 'B': 'Same', 'C': 'Diff', 'D': 'Other'}

    test_cases = [
        (options_valid, True, "Valid options"),
        (options_missing, False, "Missing option D"),
        (options_duplicate, False, "Duplicate options"),
    ]

    for options, expected, desc in test_cases:
        is_valid, error = validate_mcq_options(options)
        status = "✓" if is_valid == expected else "✗"
        print(f"{status} {desc}: {'PASS' if is_valid == expected else 'FAIL'}")
        if error:
            print(f"   Error: {error}")

    # Test 3: Auto-Fix Formatting
    print("\n3. AUTO-FIX FORMATTING")
    print("-" * 70)

    test_cases = [
        ("what  is  this", "What is this?"),
        ("How does it work", "How does it work?"),
        ("explain  the  process  .", "Explain the process."),
    ]

    for original, expected in test_cases:
        fixed = auto_fix_question_formatting(original)
        status = "✓" if fixed == expected else "✗"
        print(f"{status} '{original}' -> '{fixed}'")

    # Test 4: Duplicate Detection
    print("\n4. DUPLICATE DETECTION")
    print("-" * 70)

    existing = ["What is photosynthesis?", "How do plants grow?"]

    test_cases = [
        ("What is photosynthesis?", True, "Exact duplicate"),
        ("What is Photosynthesis?", True, "Case-insensitive duplicate"),
        ("How does cellular respiration work?", False, "Not a duplicate"),
    ]

    for question, expected, desc in test_cases:
        is_dup, similar = check_duplicate_question(question, existing)
        status = "✓" if is_dup == expected else "✗"
        print(f"{status} {desc}: {'PASS' if is_dup == expected else 'FAIL'}")

    # Test 5: Difficulty Scoring
    print("\n5. DIFFICULTY SCORING")
    print("-" * 70)

    test_cases = [
        ("What is water?", None, "easy"),
        ("Analyze the process of photosynthesis and compare it with cellular respiration.", None, "hard"),
        ("How do plants grow?", None, "medium"),
    ]

    for question, options, expected in test_cases:
        difficulty = calculate_difficulty_score(question, options)
        status = "✓" if difficulty == expected else "✗"
        print(f"{status} Expected '{expected}', Got '{difficulty}': {question[:50]}...")

    print("\n" + "=" * 70)
    print(" ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    test_all()
