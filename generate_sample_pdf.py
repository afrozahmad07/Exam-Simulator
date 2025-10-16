#!/usr/bin/env python3
"""
Generate a sample PDF document for testing the upload functionality
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from datetime import datetime


def generate_sample_pdf(filename='sample_study_material.pdf'):
    """Generate a sample PDF with educational content"""

    # Create the PDF document
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='navy',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = styles['Heading2']
    normal_style = styles['BodyText']
    normal_style.alignment = TA_JUSTIFY

    # Title
    title = Paragraph("Introduction to Python Programming", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.2 * inch))

    # Introduction
    intro_text = """
    Python is a high-level, interpreted programming language known for its simplicity and readability.
    Created by Guido van Rossum and first released in 1991, Python has become one of the most popular
    programming languages in the world. It supports multiple programming paradigms, including procedural,
    object-oriented, and functional programming.
    """
    elements.append(Paragraph(intro_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 1: Basic Concepts
    elements.append(Paragraph("1. Basic Concepts", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    basic_text = """
    <b>Variables and Data Types:</b> Python is dynamically typed, meaning you don't need to declare
    variable types explicitly. The main data types include integers, floats, strings, booleans, lists,
    tuples, dictionaries, and sets. Variables are created when you assign a value to them using the
    assignment operator (=).
    """
    elements.append(Paragraph(basic_text, normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    operators_text = """
    <b>Operators:</b> Python supports various operators including arithmetic operators (+, -, *, /, //, %, **),
    comparison operators (==, !=, <, >, <=, >=), logical operators (and, or, not), and assignment operators
    (=, +=, -=, *=, /=).
    """
    elements.append(Paragraph(operators_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 2: Control Structures
    elements.append(Paragraph("2. Control Structures", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    control_text = """
    <b>Conditional Statements:</b> Python uses if, elif, and else statements for conditional execution.
    The syntax relies on indentation rather than braces, making the code more readable. Conditions are
    evaluated as boolean expressions, and the corresponding code block is executed when the condition is True.
    """
    elements.append(Paragraph(control_text, normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    loops_text = """
    <b>Loops:</b> Python provides two main types of loops: for loops and while loops. For loops are used
    to iterate over sequences (lists, tuples, strings, etc.) or other iterable objects. While loops continue
    executing as long as a specified condition remains True. Both loop types support break and continue
    statements for flow control.
    """
    elements.append(Paragraph(loops_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 3: Functions
    elements.append(Paragraph("3. Functions", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    functions_text = """
    Functions in Python are defined using the 'def' keyword followed by the function name and parameters
    in parentheses. Functions can accept arguments and return values using the 'return' statement. Python
    supports default arguments, keyword arguments, and variable-length arguments (*args and **kwargs).
    Functions are first-class objects, meaning they can be assigned to variables, passed as arguments,
    and returned from other functions.
    """
    elements.append(Paragraph(functions_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 4: Data Structures
    elements.append(Paragraph("4. Data Structures", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    lists_text = """
    <b>Lists:</b> Lists are ordered, mutable collections that can contain elements of different data types.
    They are created using square brackets [] and support various methods like append(), insert(), remove(),
    and pop(). Lists can be indexed and sliced to access specific elements or ranges.
    """
    elements.append(Paragraph(lists_text, normal_style))
    elements.append(Spacer(1, 0.2 * inch))

    dicts_text = """
    <b>Dictionaries:</b> Dictionaries are unordered collections of key-value pairs. They are created using
    curly braces {} with keys and values separated by colons. Dictionaries provide fast lookup times and
    are commonly used for mapping relationships and storing structured data.
    """
    elements.append(Paragraph(dicts_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 5: Object-Oriented Programming
    elements.append(Paragraph("5. Object-Oriented Programming", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    oop_text = """
    Python supports object-oriented programming through classes and objects. Classes are defined using the
    'class' keyword and can contain attributes (data) and methods (functions). Objects are instances of
    classes. Python supports key OOP concepts including encapsulation, inheritance, and polymorphism.
    The __init__ method serves as a constructor, and the self parameter refers to the instance itself.
    """
    elements.append(Paragraph(oop_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Section 6: Modules and Packages
    elements.append(Paragraph("6. Modules and Packages", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    modules_text = """
    Modules are Python files containing definitions and statements. They help organize code into logical
    units and promote code reuse. Modules are imported using the 'import' statement. Python's standard
    library provides numerous built-in modules for various tasks. Packages are collections of modules
    organized in directories with an __init__.py file.
    """
    elements.append(Paragraph(modules_text, normal_style))
    elements.append(Spacer(1, 0.3 * inch))

    # Conclusion
    elements.append(Paragraph("Conclusion", heading_style))
    elements.append(Spacer(1, 0.1 * inch))

    conclusion_text = """
    Python's simplicity, versatility, and extensive ecosystem make it an excellent choice for beginners
    and experienced developers alike. Whether you're building web applications, analyzing data, creating
    machine learning models, or automating tasks, Python provides the tools and libraries needed to get
    the job done efficiently. Its readable syntax and strong community support continue to drive its
    popularity across various domains.
    """
    elements.append(Paragraph(conclusion_text, normal_style))

    # Build PDF
    doc.build(elements)
    print(f"✓ Sample PDF generated successfully: {filename}")
    return filename


if __name__ == '__main__':
    # Generate the sample PDF
    pdf_file = generate_sample_pdf('sample_study_material.pdf')
    print(f"\nYou can now upload this file: {pdf_file}")
    print("File size:", f"{__import__('os').path.getsize(pdf_file) / 1024:.1f} KB")
