# NSU Graduation Audit Engine

A professional-grade command-line tool for auditing student graduation eligibility at North South University (NSU). Built with enterprise software engineering practices, this tool processes student transcripts against program requirements to determine graduation readiness.

## 🎯 Project Overview

This project implements a three-tiered graduation audit system:

- **Level 1**: Credit Tally Engine - Calculates earned vs. attempted credits
- **Level 2**: GPA Calculator - Computes CGPA with NSU grading rules and waiver handling
- **Level 3**: Complete Audit - Full graduation eligibility check with deficiency reporting

## ✨ Key Features

### Accurate NSU Grading System
- Official NSU 4.0 scale implementation
- Proper handling of A, A-, B+, B, B-, C+, C, C-, D+, D, F grades
- W (Withdrawal) and I (Incomplete) grade handling
- 0-credit course processing (labs)

### Intelligent Retake Logic
- Automatically identifies retaken courses
- Uses best grade for CGPA calculation
- Tracks all attempts on transcript
- Handles multiple retakes correctly

### Edge Case Handling
- Failed courses (F grades)
- Withdrawn courses (W grades)
- 0-credit lab courses
- Course waivers (ENG102, BUS112)
- Mixed valid/invalid grades

### Comprehensive Reporting
- Credit breakdown by status
- Semester-wise GPA tracking
- Grade distribution visualization
- Missing course identification
- Retake history reporting

## 📁 Project Structure

```
nsu-audit-engine/
├── src/
│   ├── models/
│   │   ├── grade.py          # NSU grading system
│   │   ├── transcript.py     # Student transcript model
│   │   └── program.py        # Program requirements model
│   ├── parsers/
│   │   ├── csv_parser.py     # CSV transcript parser
│   │   └── md_parser.py      # Markdown program parser
│   ├── calculators/
│   │   ├── credit_calculator.py    # Level 1: Credit tally
│   │   ├── gpa_calculator.py       # Level 2: GPA calculation
│   │   └── audit_calculator.py     # Level 3: Full audit
│   └── main.py               # CLI application
├── data/
│   ├── programs/
│   │   ├── bba_program.md    # BBA requirements
│   │   └── cse_program.md    # CSE requirements
│   ├── transcripts/          # Sample transcripts
│   └── test_cases/           # Test data files
│       ├── test_L1.csv       # Level 1 test cases
│       ├── test_L2.csv       # Level 2 test cases
│       └── test_L3_retakes.csv  # Level 3 test cases
├── tests/                    # Unit tests
├── docs/                     # Documentation
└── README.md
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- No external dependencies required (uses only Python standard library)

### Installation
```bash
# Clone or download the project
cd nsu-audit-engine

# No pip install needed - uses standard library only!
```

## 📖 Usage

### Command Line Interface

Basic syntax:
```bash
python src/main.py --level <1|2|3> --transcript <csv_file> [options]
```

### Level 1: Credit Tally

Check earned credits and identify valid vs. invalid courses:

```bash
python src/main.py -l 1 -t data/test_cases/test_L1.csv
```

**Output:**
- Total earned credits
- Total attempted credits
- Courses passed/failed/withdrawn
- Retaken course count
- Detailed course-by-course breakdown

### Level 2: GPA Calculation

Calculate CGPA with NSU rules and handle waivers:

```bash
python src/main.py -l 2 -t data/test_cases/test_L2.csv
```

**With waivers:**
```bash
python src/main.py -l 2 -t data/test_cases/test_L2.csv --waive ENG102,BUS112
```

**Output:**
- CGPA (Cumulative Grade Point Average)
- Class standing (First/Second/Third Class)
- Honors status (Summa/Magna/Cum Laude)
- Probation warning (if CGPA < 2.0)
- Grade distribution
- Semester-wise GPA breakdown

### Level 3: Complete Graduation Audit

Perform full graduation eligibility check:

```bash
python src/main.py -l 3 \
  -t data/test_cases/test_L3_retakes.csv \
  -p data/programs/bba_program.md \
  --id 2014567890 \
  --name "Student Name"
```

**Using built-in program:**
```bash
python src/main.py -l 3 \
  -t data/test_cases/test_L3_retakes.csv \
  --program-type BBA
```

**Output:**
- ✓/✗ Graduation eligibility status
- Credit requirement check
- CGPA requirement check
- Missing mandatory courses
- Incomplete course groups
- Retake history
- Detailed deficiency report

### Additional Options

```bash
# Save report to file
python src/main.py -l 3 -t transcript.csv -p program.md -o report.txt

# Get detailed breakdown
python src/main.py -l 3 -t transcript.csv -p program.md --detailed

# Disable interactive prompts
python src/main.py -l 2 -t transcript.csv --no-interactive

# Show help
python src/main.py --help
```

## 📝 File Formats

### Transcript CSV Format

```csv
Course_Code,Credits,Grade,Semester
ENG102,3,A,Spring 2023
MAT116,0,B,Spring 2023
CSE115,4,A-,Summer 2023
HIS103,3,F,Summer 2023
HIS103,3,B+,Spring 2024
```

**Requirements:**
- Header row must include: `Course_Code`, `Credits`, `Grade`, `Semester`
- Course codes: Letters + numbers (e.g., CSE115, MAT120)
- Credits: Integer or float (0 for labs)
- Grade: NSU letter grades (A, A-, B+, B, B-, C+, C, C-, D+, D, F, W, I)
- Semester: "Term YYYY" format (e.g., "Spring 2023")

### Program Markdown Format

See `data/programs/bba_program.md` for detailed example.

Key sections:
- Program metadata (degree, credits, CGPA)
- Core courses (listed courses)
- Course groups (with "Choose X of Y" syntax)
- Waivable courses
- Special requirements

## 🧪 Testing

### Test Cases Provided

1. **test_L1.csv**: Tests credit tally engine
   - Includes retakes, failures, withdrawals
   - 0-credit courses
   - Mixed valid/invalid grades

2. **test_L2.csv**: Tests GPA calculation
   - Diverse grade distribution
   - One retaken course
   - Multiple semesters

3. **test_L3_retakes.csv**: Tests full audit
   - Multiple retakes (HIS103, ECO101, ACT201)
   - Complete BBA course sequence
   - All requirement types

### Running Tests

```bash
# Test Level 1
python src/main.py -l 1 -t data/test_cases/test_L1.csv

# Test Level 2
python src/main.py -l 2 -t data/test_cases/test_L2.csv

# Test Level 3
python src/main.py -l 3 -t data/test_cases/test_L3_retakes.csv --program-type BBA
```

## 🔧 Implementation Details

### NSU Grading Rules Implemented

1. **Grade Points:**
   - A = 4.0, A- = 3.7, B+ = 3.3, B = 3.0, B- = 2.7
   - C+ = 2.3, C = 2.0, C- = 1.7, D+ = 1.3, D = 1.0, F = 0.0

2. **CGPA Calculation:**
   - Formula: Total Quality Points / Total Credits Attempted
   - Only graded courses (A through F) count
   - 0-credit courses are excluded
   - W and I grades don't count

3. **Retake Logic:**
   - All attempts appear on transcript
   - Only best grade used in CGPA
   - F counts as 0.0 until retaken

4. **Credit Earning:**
   - Passing grades (A through D) earn credits
   - F, W, I do not earn credits

### Edge Cases Handled

- **Retaken Courses**: Identifies best attempt, uses only that grade
- **0-Credit Labs**: Tracked but excluded from CGPA
- **Failed Courses**: Counted as attempted but not earned
- **Withdrawn Courses**: Not counted at all
- **Course Waivers**: Excluded from requirements
- **Multiple Retakes**: Handles 3+ attempts correctly

## 🎓 Program Support

### Currently Supported Programs

1. **BBA (Business Administration)**
   - 126 credits required
   - Full course requirements implemented
   - Waivable courses: ENG102, BUS112
   - All major options supported

2. **CSE (Computer Science & Engineering)**
   - 130 credits required
   - Core math and major courses
   - Physics requirements included

### Adding New Programs

Create a markdown file in `data/programs/` following the format in `bba_program.md`, or extend `ProgramFactory` in `src/models/program.py`.

## 📊 Sample Output

### Level 1 Output
```
LEVEL 1: CREDIT TALLY REPORT
============================================================
Total Earned Credits:      28.0
Total Attempted Credits:   34.0

Course Statistics:
  ✓ Passed:                9
  ✗ Failed:                2
  ⊘ Withdrawn:             1
  ○ Zero-Credit Courses:   2
  ⟲ Retaken Courses:       1
============================================================
```

### Level 2 Output
```
LEVEL 2: GPA & WAIVER REPORT
============================================================
CGPA:                      3.42
Class Standing:            First Class
  🏆 Honors: Cum Laude

Total Quality Points:      102.60
Total GPA Credits:         30.0

Grade Distribution:
  A   (4.0): ██████ 6
  A-  (3.7): ████ 4
  B+  (3.3): ███ 3
  B   (3.0): ██ 2
============================================================
```

### Level 3 Output
```
======================================================================
GRADUATION AUDIT REPORT
======================================================================

Student: Test Student (2014567890)

Program: Business Administration

✓ ELIGIBLE TO GRADUATE

SUMMARY
----------------------------------------------------------------------
✓ Credits: 126.0 earned
✓ CGPA: 3.25
   Standing: First Class
✓ Required Courses: 45 completed
✓ Course Groups: 4 satisfied

RETAKEN COURSES
----------------------------------------------------------------------

HIS103:
  → C (Summer 2020)
  ✓ B+ (Spring 2021)
======================================================================
```

## 🏗️ Architecture & Design

### Design Principles

1. **Modularity**: Each level is an independent, testable module
2. **Type Safety**: Strong typing with dataclasses
3. **Error Handling**: Graceful failure with clear messages
4. **Testability**: Unit-testable components
5. **Extensibility**: Easy to add programs/rules

### Data Flow

```
CSV File → Parser → Transcript Model → Calculator → Report
MD File → Parser → Program Model → Audit Engine → Deficiency Report
```

## 🚦 Future Enhancements

This project is designed for future AI integration:

- RESTful API wrapper for AI agents
- JSON output format for machine processing
- Batch processing capabilities
- Real-time validation
- WebSocket streaming support

## 📄 License & Attribution

Created for NSU "Vibe Coding" course project.
Implements official NSU grading policies and degree requirements.

## 👨‍💻 Author

Built with professional software engineering standards, following Google's Python style guide and enterprise-grade architecture patterns.

---

**Note**: This is a learning project. For official graduation checks, always consult NSU's Office of the Registrar.
