# Exam Simulator - Complete Workflow Guide

## Overview

This guide explains the complete workflow from uploading documents to taking exams and viewing results.

---

## 📚 Complete Workflow

```
1. Upload Documents
   ↓
2. AI Generates Questions (automatic)
   ↓
3. Review Questions in Question Bank (optional)
   ↓
4. Take Practice Exam
   ↓
5. View Results & Analytics
```

---

## Step 1: Upload Documents

**Location:** Content → Upload Documents

### What You Can Upload:
- PDF files (.pdf)
- Word documents (.docx)
- Text files (.txt)

### What Happens:
1. You upload your study material
2. System extracts text from the document
3. Document is saved to "My Documents"
4. **Questions are NOT generated yet** (happens when you start an exam)

### Organization Documents:
- If you belong to an organization, all members can see uploaded documents
- Documents are tagged with organization name
- Everyone in the org can take exams on shared documents

---

## Step 2: Question Bank (Auto-Generated)

**Location:** Content → Question Bank

### What Is the Question Bank?

The Question Bank is a **repository of all generated questions** from your documents. Think of it as a library of practice questions.

### When Are Questions Generated?

Questions are generated **on-demand** in two scenarios:
1. **When you start an exam** - Questions are generated if they don't exist
2. **When you manually generate** - From Content → My Documents → Generate Questions

### What You See in Question Bank:

- **All approved questions** from your organization's documents
- **Filter by:**
  - Document
  - Question Type (MCQ, True/False, Short Answer)
  - Status (Approved, Pending, Rejected)

### What You Can Do:

✅ **Review Questions** - See what questions were generated
✅ **Delete Questions** - Remove inappropriate or duplicate questions
✅ **Take Practice Exam** - Click the button to start an exam with these questions

❌ **You CANNOT** - Manually create or edit questions (all AI-generated)

### Relationship to Exams:

```
Document → AI Generates Questions → Question Bank → Selected for Exam → You Take Exam
```

The Question Bank is the **source pool** from which exam questions are randomly selected.

---

## Step 3: Take Practice Exam

**Location:** Take Exam

### How to Start an Exam:

1. Click "Take Exam" from the dashboard
2. **Select Options:**
   - **Document**: Choose which document to test on (shows ALL organization documents)
   - **Number of Questions**: 5, 10, 15, 20, or 25 questions
   - **Difficulty Level**: Easy, Medium, Hard, or All Levels
   - **Exam Duration**: 10, 15, 20, 30, 45, 60, 90, or 120 minutes
3. Click "Start Exam"

### What Happens Behind the Scenes:

```
1. System checks if questions exist for that document
   ├─ If YES: Randomly select N questions from Question Bank
   └─ If NO: Generate questions first, then select

2. Create exam session with:
   ├─ Selected questions
   ├─ Start time
   ├─ Duration (user-selected)
   └─ Empty answer sheet

3. Start timer and show first question
```

### During the Exam:

- **Timer counts down** from your selected duration
- **Answers auto-save** as you type/select
- **Navigate freely** between questions using the navigator
- **Progress tracked** - See which questions are answered
- **Time tracking** - Each question tracks how long you spent

### Question Types:

1. **Multiple Choice (MCQ)**
   - 4 options (A, B, C, D)
   - Select one correct answer
   - Graded automatically

2. **True/False**
   - Two options
   - Graded automatically

3. **Short Answer**
   - Text area for 2-5 line answers
   - **Graded by AI** - Compares your answer to model answer and key points
   - Pass threshold: 60% similarity or 50% key points covered

### When Time Expires:

- Modal appears: "Time is up! Your exam will be submitted automatically"
- Exam is submitted automatically
- Can't make changes after time expires
- Redirects to results page

---

## Step 4: View Results

**Location:** Automatically redirected after submitting exam

### What You See:

#### Overall Score Card:
- **Score percentage** (e.g., 85%)
- **Questions answered** (e.g., 8/10)
- **Correct answers** (e.g., 7)
- **Wrong answers** (e.g., 1)
- **Total time spent**
- **Average time per question**

#### Question-by-Question Breakdown:

For each question, you see:

**Multiple Choice & True/False:**
- ✅ Your answer (highlighted in green if correct, red if wrong)
- ✅ Correct answer (always shown)
- ✅ All options (with indicators)
- ✅ Explanation (if available)

**Short Answer:**
- ✅ **Your full typed answer** (with line breaks preserved)
- ✅ **Model answer** - The ideal answer
- ✅ **Key points** - Important points that should be covered
- ✅ **Grading note** - Explains AI grading was used
- ℹ️ Note: "Short answer questions require manual grading by your instructor"

### Actions Available:

- **Download PDF** - Get a printable PDF of your results
- **Take Another Exam** - Start a new practice session
- **View Analytics** - See your performance trends

---

## Step 5: Analytics & Progress

**Location:** Performance → Analytics

### What You Track:

1. **Exam History**
   - All exams you've taken
   - Scores over time
   - Dates and times

2. **Performance Trends**
   - Chart showing score progression
   - Average score across all exams
   - Total questions answered

3. **Difficulty Analysis**
   - Success rate by difficulty (Easy, Medium, Hard)
   - Identify your weak areas

4. **Export Data**
   - Download CSV of all your exam data
   - For personal tracking or analysis

---

## 🎯 Common Workflows

### Workflow 1: Quick Practice Session

```
1. Go to "Take Exam"
2. Select any document
3. Choose 10 questions, 15 minutes
4. Take exam
5. Review results
```

**Use Case:** Quick knowledge check before a test

---

### Workflow 2: Comprehensive Study

```
1. Upload study materials (multiple documents)
2. Go to Question Bank
3. Review all generated questions
4. Delete any inappropriate questions
5. Take exam on each document (25 questions, 60 minutes)
6. Review results and focus on weak areas
7. Repeat until confident
```

**Use Case:** Thorough exam preparation

---

### Workflow 3: Organization-Wide Practice

```
1. Teacher uploads course materials
2. All students in organization can see documents
3. Students take practice exams independently
4. Teacher monitors question bank quality
5. Students compare performance in analytics
```

**Use Case:** Classroom or training environment

---

## 🔄 Document to Exam Flow (Detailed)

### Scenario: You just uploaded a new PDF

**Step 1: Document Upload**
```
You → Upload "Biology Chapter 5.pdf"
     ↓
System → Saves to database
      → Links to your organization
      → Status: Ready for question generation
```

**Step 2: First Exam Attempt**
```
You → Click "Take Exam"
    → Select "Biology Chapter 5.pdf"
    → Choose 10 questions, 30 minutes
    ↓
System → Checks Question Bank: "0 questions found"
       → Triggers AI generation
       → Generates 20-30 questions (MCQ, T/F, Short Answer)
       → Saves to Question Bank
       → Marks questions as "approved"
       → Randomly selects 10 questions
       → Starts exam session
```

**Step 3: Subsequent Exams**
```
You → Click "Take Exam" again
    → Select "Biology Chapter 5.pdf"
    → Choose 15 questions, 20 minutes
    ↓
System → Checks Question Bank: "30 questions found"
       → Randomly selects 15 questions (different from before)
       → Starts exam session
```

**No re-generation needed!** Questions are reused.

---

## 📊 Question Selection Algorithm

### How Questions Are Selected for Exams:

1. **Pool Creation**
   ```
   Filter Question Bank by:
   - Document ID (selected document)
   - Status = 'approved'
   - Difficulty (if specified, otherwise all)
   ```

2. **Random Selection**
   ```
   If pool has 50 questions and you want 10:
   - Randomly select 10 unique questions
   - Use time-based seed for uniqueness
   - Never repeat questions within same exam
   ```

3. **Fair Distribution (if possible)**
   ```
   Try to balance:
   - Question types (MCQ, T/F, Short Answer)
   - Difficulty levels (if "All" selected)
   ```

---

## 🎓 Tips for Best Results

### For Students:

1. **Upload quality materials** - The better the document, the better the questions
2. **Review Question Bank first** - Familiarize yourself with question styles
3. **Start with shorter exams** - Build confidence with 10 questions, 15 minutes
4. **Use all difficulty levels** - Don't just stick to "Easy"
5. **Review wrong answers** - Learn from mistakes in results
6. **Track progress** - Use Analytics to see improvement over time

### For Teachers/Admins:

1. **Upload comprehensive materials** - Cover all topics thoroughly
2. **Review generated questions** - Delete poor quality questions
3. **Set organization** - Ensure students are in correct organization
4. **Monitor Question Bank** - Keep question pool fresh and accurate
5. **Encourage practice** - Students can take unlimited exams

---

## ❓ FAQs

### Q: How many times can I take an exam?
**A:** Unlimited! Each exam uses randomly selected questions, so it's different every time.

### Q: Can I retake the exact same exam?
**A:** No. Each exam session is unique. Questions are randomly selected from the pool.

### Q: What if I run out of time?
**A:** Exam auto-submits when timer reaches 0. Answered questions are scored, unanswered count as wrong.

### Q: Can I pause an exam?
**A:** Yes! Close the browser and come back later. Your timer continues, but answers are saved.

### Q: How are short answers graded?
**A:** AI compares your answer to the model answer and key points. 60% similarity = pass.

### Q: Can I see questions from other people's documents?
**A:** Only if you're in the same organization. Organization members share documents.

### Q: What happens if no questions exist for a document?
**A:** System automatically generates questions when you start the exam (takes 10-30 seconds).

### Q: Can I edit generated questions?
**A:** No, but you can delete them. Questions are AI-generated and not manually editable.

---

## 🔧 Troubleshooting

### Issue: No documents showing in exam selection

**Solution:**
1. Check that you've uploaded documents
2. If in organization, check that documents have organization tag
3. Try uploading a new document

### Issue: "No questions available for this document"

**Solution:**
1. System will generate questions automatically
2. Wait 10-30 seconds
3. Or manually generate from "My Documents" → Generate Questions

### Issue: Timer stuck or not counting

**Solution:**
1. Refresh the page (answers are auto-saved)
2. Timer will recalculate based on start time
3. If expired, exam will auto-submit

### Issue: Short answer not showing in results

**Solution:**
- Fixed in latest update! Run `./deploy-server.sh` to deploy fix

### Issue: Can't select custom exam duration

**Solution:**
- Fixed in latest update! Now shows 8 duration options (10-120 minutes)

---

## 🚀 Recent Improvements

### Latest Updates (October 2025):

1. ✅ **Custom Exam Duration** - Choose from 10 to 120 minutes
2. ✅ **Organization Documents** - See all documents from your organization
3. ✅ **Short Answer Display** - Full answers shown in results
4. ✅ **AI Grading** - Intelligent grading for short answers
5. ✅ **Question Bank Clarity** - Added "Take Practice Exam" button and info

---

**Last Updated:** 2025-10-20
**Version:** 2.0
**For Support:** Check the main README or contact your administrator
