"""
Markdown Parser for Program Requirements
Parses markdown files into ProgramRequirements objects
"""

import re
from typing import List, Optional
from pathlib import Path
from models.program import ProgramRequirements, CourseGroup


class MarkdownParser:
    """Parser for markdown program requirement files"""
    
    @staticmethod
    def parse_markdown(file_path: str) -> ProgramRequirements:
        """
        Parse a markdown file into ProgramRequirements.
        
        Expected format:
        # Program Name
        - Degree: Bachelor of Science
        - Total Credits: 130
        - Minimum CGPA: 2.0
        
        ## Mandatory Courses
        - ENG102
        - ENG103
        
        ## Core Courses
        - CSE115
        - CSE173
        
        etc.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Program file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Initialize program
        program = ProgramRequirements(
            program_name="Unknown",
            degree="Unknown",
            total_credits_required=0
        )
        
        # Extract program name (first # heading)
        name_match = re.search(r'^#\s+(?:Program:\s+)?(.+)$', content, re.MULTILINE)
        if name_match:
            program.program_name = name_match.group(1).strip()
        
        # Extract degree
        degree_match = re.search(r'-\s*Degree:\s*(.+)$', content, re.MULTILINE)
        if degree_match:
            program.degree = degree_match.group(1).strip()
        
        # Extract total credits
        credits_match = re.search(r'-\s*Total Credits(?:\s+Required)?:\s*(\d+)', content, re.MULTILINE)
        if credits_match:
            program.total_credits_required = int(credits_match.group(1))
        
        # Extract minimum CGPA
        cgpa_match = re.search(r'-\s*Minimum CGPA:\s*([\d.]+)', content, re.MULTILINE)
        if cgpa_match:
            program.minimum_cgpa = float(cgpa_match.group(1))
        
        # Extract course lists
        program.mandatory_courses = MarkdownParser._extract_course_list(
            content, r'##\s+Mandatory(?:\s+GED)?(?:\s+Courses)?'
        )
        
        program.core_courses = MarkdownParser._extract_course_list(
            content, r'##\s+Core(?:\s+Courses)?'
        )
        
        # Also check for specific core types
        core_math = MarkdownParser._extract_course_list(
            content, r'##\s+Core Math'
        )
        if core_math:
            program.core_courses.extend(core_math)
        
        program.major_core_courses = MarkdownParser._extract_course_list(
            content, r'##\s+Major Core'
        )
        
        # Extract waivable courses
        program.waivable_courses = MarkdownParser._extract_course_list(
            content, r'##\s+Waivable(?:\s+Courses)?'
        )
        
        # Extract course groups (if any)
        program.course_groups = MarkdownParser._extract_course_groups(content)
        
        return program
    
    @staticmethod
    def _extract_course_list(content: str, section_pattern: str) -> List[str]:
        """
        Extract list of courses from a markdown section.
        
        Looks for patterns like:
        ## Section Name
        - COURSE123
        - COURSE456
        """
        # Find the section
        section_match = re.search(
            section_pattern + r'(.+?)(?=^##|\Z)',
            content,
            re.MULTILINE | re.DOTALL
        )
        
        if not section_match:
            return []
        
        section_content = section_match.group(1)
        
        # Extract course codes (letters followed by numbers)
        # Handles formats like: CSE115, MAT-120, ENG 102
        courses = re.findall(
            r'\b([A-Z]{2,4}[-\s]?\d{3,4}[A-Z]?)\b',
            section_content
        )
        
        # Normalize course codes (remove spaces/hyphens)
        normalized = [c.replace('-', '').replace(' ', '') for c in courses]
        
        return normalized
    
    @staticmethod
    def _extract_course_groups(content: str) -> List[CourseGroup]:
        """
        Extract course groups with choice requirements.
        
        Looks for patterns like:
        ## Group Name (Choose 2 of 4)
        - COURSE1
        - COURSE2
        - COURSE3
        - COURSE4
        """
        groups = []
        
        # Find all sections with choice requirements
        pattern = r'##\s+(.+?)\s*\(Choose\s+(\d+)(?:\s+of\s+\d+)?\)(.+?)(?=^##|\Z)'
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            group_name = match.group(1).strip()
            required_count = int(match.group(2))
            section_content = match.group(3)
            
            # Extract courses
            courses = re.findall(
                r'\b([A-Z]{2,4}[-\s]?\d{3,4}[A-Z]?)\b',
                section_content
            )
            normalized = [c.replace('-', '').replace(' ', '') for c in courses]
            
            if normalized:
                groups.append(CourseGroup(
                    name=group_name,
                    courses=normalized,
                    required_count=required_count
                ))
        
        return groups
    
    @staticmethod
    def create_sample_markdown(file_path: str, program_type: str = "BBA"):
        """
        Create a sample markdown file for testing.
        
        Args:
            file_path: Where to save the markdown
            program_type: "BBA" or "CSE"
        """
        if program_type == "BBA":
            content = """# Program: Business Administration

- Degree: Bachelor of Business Administration (BBA)
- Total Credits Required: 126
- Minimum CGPA: 2.0

## Waivable Courses
- ENG102
- BUS112

## Core Courses
### School Core
- ECO101
- ECO104
- MIS107
- BUS251
- BUS172
- BUS173
- BUS135

### BBA Core
- ACT201
- ACT202
- FIN254
- LAW200
- INB372
- MKT202
- MIS207
- MGT212
- MGT351
- MGT314
- MGT368
- MGT489

## Mandatory GED
- ENG103
- ENG105
- PHI401
- HIS103

## History Elective (Choose 1 of 4)
- HIS101
- HIS102
- HIS202
- HIS205

## Political Science (Choose 1 of 3)
- POL101
- POL104
- PAD201

## Social Science (Choose 1 of 3)
- SOC101
- GEO205
- ANT101

## Basic Sciences (Choose 3 of 6)
- BIO103
- ENV107
- PBH101
- PSY101
- PHY107
- CHE101

## Major Core
(To be specified based on chosen major)

## Notes
- Students must complete 18 credits (6 courses) in their chosen major
- 4 major core courses + 2 major electives
- 3 free elective courses (9 credits)
- Internship is 4 credits but non-counting for graduation total
"""
        else:  # CSE
            content = """# Program: Computer Science & Engineering

- Degree: Bachelor of Science (BS)
- Total Credits Required: 130
- Minimum CGPA: 2.0

## Mandatory GED
- ENG102
- ENG103
- HIS103
- PHI101

## Core Math
- MAT116
- MAT120
- MAT250
- MAT350
- MAT361

## Major Core
- CSE115
- CSE173
- CSE215
- CSE225
- CSE231
- CSE311
- CSE323
- CSE327
- CSE331
- CSE332
- CSE425

## Notes
- All core courses must be completed
- Additional electives required to meet 130 credit total
"""
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)


if __name__ == "__main__":
    import tempfile
    import os
    
    print("Markdown Parser Test")
    print("=" * 50)
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        test_file = f.name
    
    try:
        # Create sample markdown
        MarkdownParser.create_sample_markdown(test_file, "BBA")
        print(f"Created test file: {test_file}")
        
        # Parse
        program = MarkdownParser.parse_markdown(test_file)
        
        print(f"\n{program}")
        print(f"Program: {program.program_name}")
        print(f"Degree: {program.degree}")
        print(f"Total Credits: {program.total_credits_required}")
        print(f"Minimum CGPA: {program.minimum_cgpa}")
        
        print(f"\nWaivable: {len(program.waivable_courses)} courses")
        print(f"  {program.waivable_courses}")
        
        print(f"\nCore: {len(program.core_courses)} courses")
        print(f"  First 5: {program.core_courses[:5]}")
        
        print(f"\nMandatory GED: {len(program.mandatory_courses)} courses")
        print(f"  {program.mandatory_courses}")
        
        print(f"\nCourse Groups: {len(program.course_groups)}")
        for group in program.course_groups:
            print(f"  {group}")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"\nCleaned up test file")
