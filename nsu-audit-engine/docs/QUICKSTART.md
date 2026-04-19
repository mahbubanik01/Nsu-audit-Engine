# Quick Start Guide

## Getting Started in 5 Minutes

### Step 1: Navigate to Project
```bash
cd nsu-audit-engine
```

### Step 2: Run Your First Audit

**Test Level 1 (Credits):**
```bash
python3 src/main.py -l 1 -t data/test_cases/test_L1.csv
```

**Test Level 2 (GPA):**
```bash
python3 src/main.py -l 2 -t data/test_cases/test_L2.csv --waive ENG102,BUS112 --no-interactive
```

**Test Level 3 (Full Audit):**
```bash
python3 src/main.py -l 3 -t data/test_cases/test_L3_retakes.csv --program-type BBA --id 2014567890 --name "Your Name"
```

## Creating Your Own Transcript

1. Create a CSV file with this format:
```csv
Course_Code,Credits,Grade,Semester
ENG102,3,A,Spring 2023
CSE115,4,A-,Summer 2023
HIS103,3,B+,Fall 2023
```

2. Run the audit:
```bash
python3 src/main.py -l 3 -t your_transcript.csv --program-type BBA
```

## Common Tasks

### Check If You Can Graduate
```bash
python3 src/main.py -l 3 -t your_transcript.csv --program-type BBA
```

Look for: "✓ ELIGIBLE TO GRADUATE" or "✗ NOT ELIGIBLE TO GRADUATE"

### Calculate Your CGPA
```bash
python3 src/main.py -l 2 -t your_transcript.csv
```

### See What Courses You're Missing
```bash
python3 src/main.py -l 3 -t your_transcript.csv --program-type BBA
```

Check the "DEFICIENCIES" section.

### Save Report to File
```bash
python3 src/main.py -l 3 -t your_transcript.csv --program-type BBA -o my_audit_report.txt
```

## Need Help?

```bash
python3 src/main.py --help
```

## Understanding the Output

### Level 1 Output
- **Total Earned Credits**: Credits you've actually earned (passed courses)
- **Total Attempted Credits**: All credits you tried (including failures)
- **⟲ Symbol**: Indicates a retaken course

### Level 2 Output
- **CGPA**: Your cumulative GPA (4.0 scale)
- **Class Standing**: First Class (3.0+), Second Class (2.5-2.99), Third Class (2.0-2.49)
- **🏆 Honors**: Cum Laude (3.5+), Magna (3.8+), Summa (3.9+)

### Level 3 Output
- **✓ ELIGIBLE**: You can graduate!
- **✗ NOT ELIGIBLE**: Check the DEFICIENCIES section to see what's missing
- **SUMMARY**: Quick overview of your status
- **DEFICIENCIES**: Exactly what you need to complete

## Pro Tips

1. **Use descriptive student info**:
   ```bash
   --id 2014567890 --name "Ahmed Rahman"
   ```

2. **Save detailed reports**:
   ```bash
   --detailed -o full_report.txt
   ```

3. **Check waivers**:
   ```bash
   --waive ENG102,BUS112
   ```

4. **Multiple tests**:
   ```bash
   python3 src/main.py -l 1 -t test1.csv -o report1.txt
   python3 src/main.py -l 1 -t test2.csv -o report2.txt
   python3 src/main.py -l 1 -t test3.csv -o report3.txt
   ```

## What Makes a Valid Transcript?

✅ **Must have**:
- Header row: `Course_Code,Credits,Grade,Semester`
- At least one course record
- Valid NSU grades (A, A-, B+, B, B-, C+, C, C-, D+, D, F, W, I)

✅ **Optional**:
- 0-credit courses (labs)
- Retaken courses (same course code multiple times)
- Waivable courses (ENG102, BUS112)

❌ **Invalid**:
- Missing headers
- Empty file
- Invalid grades
- Wrong date format

## Common Issues

**"File not found"**
- Check the file path is correct
- Use relative path from project root

**"Invalid CSV format"**
- Make sure you have the header row
- Check for typos in column names

**"Invalid grade"**
- Use NSU letter grades only
- Check for spaces or special characters

**"Missing required argument"**
- Level 3 needs `--program-type` or `--program`
