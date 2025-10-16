#!/usr/bin/env python3
"""
Test script for question validation functions
Demonstrates all validation features
"""

from utils import (
    validate_question_length,
    validate_mcq_options,
    validate_correct_answer,
    check_duplicate_question,
    calculate_difficulty_score,
    auto_fix_question_formatting,
    auto_fix_option_formatting,
    validate_question_complete
)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_question_length_validation():
    """Test question length validation"""
    print_section("TEST 1: Question Length Validation")

    test_cases = [
        ("", "Empty question"),
        ("Too short", "Question too short"),
        ("What is photosynthesis?", "Valid length question"),
        ("A" * 600, "Question too long"),
    ]

    for question, description in test_cases:
        is_valid, error = validate_question_length(question)
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"\n{status} - {description}")
        if not is_valid:
            print(f"   Error: {error}")


def test_mcq_options_validation():
    """Test MCQ options validation"""
    print_section("TEST 2: MCQ Options Validation")

    test_cases = [
        (None, "Null options"),
        ({}, "Empty options"),
        ({'A': 'Option 1'}, "Missing options B, C, D"),
        ({'A': 'Opt 1', 'B': '', 'C': 'Opt 3', 'D': 'Opt 4'}, "Empty option B"),
        ({'A': 'Same', 'B': 'Same', 'C': 'Different', 'D': 'Another'}, "Duplicate options"),
        ({'A': 'Carbon dioxide', 'B': 'Oxygen', 'C': 'Nitrogen', 'D': 'Hydrogen'}, "Valid options"),
    ]

    for options, description in test_cases:
        is_valid, error = validate_mcq_options(options) if options is not None else (False, "Options cannot be empty")
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"\n{status} - {description}")
        if not is_valid:
            print(f"   Error: {error}")


def test_correct_answer_validation():
    """Test correct answer validation"""
    print_section("TEST 3: Correct Answer Validation")

    test_cases = [
        ('A', 'mcq', {'A': 'Opt 1', 'B': 'Opt 2', 'C': 'Opt 3', 'D': 'Opt 4'}, "Valid MCQ answer"),
        ('E', 'mcq', {'A': 'Opt 1', 'B': 'Opt 2', 'C': 'Opt 3', 'D': 'Opt 4'}, "Invalid MCQ answer"),
        ('true', 'true_false', None, "Valid True/False answer"),
        ('maybe', 'true_false', None, "Invalid True/False answer"),
    ]

    for answer, q_type, options, description in test_cases:
        is_valid, error = validate_correct_answer(answer, q_type, options)
        status = "✓ PASS" if is_valid else "✗ FAIL"
        print(f"\n{status} - {description}")
        if not is_valid:
            print(f"   Error: {error}")


def test_duplicate_detection():
    """Test duplicate question detection"""
    print_section("TEST 4: Duplicate Question Detection")

    existing_questions = [
        "What is photosynthesis?",
        "How do plants make their food?",
        "What is the chemical formula for water?"
    ]

    test_cases = [
        ("What is photosynthesis?", "Exact duplicate", True),
        ("What is Photosynthesis?", "Case-insensitive duplicate", True),
        ("what is the process of photosynthesis", "Similar question", True),
        ("How does cellular respiration work?", "Completely different", False),
    ]

    for question, description, expected_duplicate in test_cases:
        is_duplicate, similar = check_duplicate_question(question, existing_questions)
        status = "✓ PASS" if is_duplicate == expected_duplicate else "✗ FAIL"
        print(f"\n{status} - {description}")
        print(f"   Question: {question}")
        if is_duplicate:
            print(f"   Similar to: {similar}")


def test_difficulty_scoring():
    """Test difficulty scoring algorithm"""
    print_section("TEST 5: Difficulty Scoring")

    test_cases = [
        (
            "What is water?",
            {'A': 'H2O', 'B': 'CO2', 'C': 'O2', 'D': 'N2'},
            "Simple recall question"
        ),
        (
            "Analyze how the process of photosynthesis differs from cellular respiration and explain why both are essential for life on Earth.",
            {
                'A': 'Photosynthesis produces oxygen while respiration consumes it, and both are needed for energy cycles',
                'B': 'They are opposite processes that work together',
                'C': 'Photosynthesis happens in plants and respiration in animals',
                'D': 'Both produce energy for organisms'
            },
            "Complex analysis question"
        ),
        (
            "Compare and contrast the structures of DNA and RNA molecules.",
            None,
            "Medium complexity without options"
        ),
    ]

    for question, options, description in test_cases:
        difficulty = calculate_difficulty_score(question, options)
        print(f"\n{description}")
        print(f"   Question: {question[:80]}...")
        print(f"   Calculated Difficulty: {difficulty.upper()}")


def test_auto_fix_formatting():
    """Test auto-fix formatting functions"""
    print_section("TEST 6: Auto-Fix Formatting")

    question_test_cases = [
        "what  is   photosynthesis",
        "How does this work",
        "explain the process  .",
        "Why   is   this  important???",
    ]

    print("\nQuestion Formatting:")
    for question in question_test_cases:
        fixed = auto_fix_question_formatting(question)
        print(f"\n   Original: '{question}'")
        print(f"   Fixed:    '{fixed}'")

    option_test_cases = [
        "the process of converting light to energy.",
        "CARBON DIOXIDE",
        "oxygen  and  water  ,  along with glucose",
    ]

    print("\n\nOption Formatting:")
    for option in option_test_cases:
        fixed = auto_fix_option_formatting(option)
        print(f"\n   Original: '{option}'")
        print(f"   Fixed:    '{fixed}'")


def test_complete_validation():
    """Test complete validation with auto-fix"""
    print_section("TEST 7: Complete Validation (with Auto-Fix)")

    # Test valid MCQ question
    print("\n1. Testing Valid MCQ Question:")
    is_valid, errors, fixed_data = validate_question_complete(
        question_text="what  is  the  primary  product  of  photosynthesis",
        question_type='mcq',
        correct_answer='A',
        options={
            'A': 'glucose  and  oxygen.',
            'B': 'carbon dioxide',
            'C': 'WATER',
            'D': 'nitrogen'
        },
        auto_fix=True
    )

    if is_valid:
        print("   ✓ Validation PASSED")
        print(f"   Fixed Question: {fixed_data['question_text']}")
        print(f"   Fixed Options:")
        for key, value in fixed_data['options'].items():
            print(f"      {key}: {value}")
        print(f"   Calculated Difficulty: {fixed_data['difficulty']}")
    else:
        print("   ✗ Validation FAILED")
        for error in errors:
            print(f"      - {error}")

    # Test question with missing option
    print("\n2. Testing MCQ with Missing Option:")
    is_valid, errors, fixed_data = validate_question_complete(
        question_text="What is the capital of France?",
        question_type='mcq',
        correct_answer='A',
        options={
            'A': 'Paris',
            'B': 'London',
            'C': 'Berlin'
            # Missing option D
        },
        auto_fix=True
    )

    if is_valid:
        print("   ✓ Validation PASSED")
    else:
        print("   ✗ Validation FAILED (Expected)")
        for error in errors:
            print(f"      - {error}")

    # Test duplicate detection
    print("\n3. Testing Duplicate Detection:")
    existing_questions = ["What is photosynthesis?", "How do plants produce energy?"]

    is_valid, errors, fixed_data = validate_question_complete(
        question_text="What is photosynthesis?",
        question_type='mcq',
        correct_answer='A',
        options={'A': 'Opt1', 'B': 'Opt2', 'C': 'Opt3', 'D': 'Opt4'},
        existing_questions=existing_questions,
        auto_fix=True
    )

    if is_valid:
        print("   ✓ Validation PASSED")
    else:
        print("   ✗ Validation FAILED (Expected - Duplicate)")
        for error in errors:
            print(f"      - {error}")

    # Test True/False question
    print("\n4. Testing True/False Question:")
    is_valid, errors, fixed_data = validate_question_complete(
        question_text="plants  convert  sunlight  into  chemical  energy",
        question_type='true_false',
        correct_answer='true',
        auto_fix=True
    )

    if is_valid:
        print("   ✓ Validation PASSED")
        print(f"   Fixed Question: {fixed_data['question_text']}")
        print(f"   Calculated Difficulty: {fixed_data['difficulty']}")
    else:
        print("   ✗ Validation FAILED")
        for error in errors:
            print(f"      - {error}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print(" QUESTION VALIDATION TEST SUITE")
    print("=" * 70)

    try:
        test_question_length_validation()
        test_mcq_options_validation()
        test_correct_answer_validation()
        test_duplicate_detection()
        test_difficulty_scoring()
        test_auto_fix_formatting()
        test_complete_validation()

        print("\n" + "=" * 70)
        print(" ALL TESTS COMPLETED")
        print("=" * 70)
        print()

    except Exception as e:
        print(f"\n\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
