"""
CSV Parser for Student Transcripts
Parses CSV files into Transcript objects
"""

import csv
from typing import Optional
from pathlib import Path
from models.transcript import Transcript, CourseRecord


class TranscriptParser:
    """Parser for CSV transcript files"""
    
    @staticmethod
    def parse_csv(file_path: str, student_id: Optional[str] = None,
                  student_name: Optional[str] = None,
                  program: Optional[str] = None) -> Transcript:
        """
        Parse a CSV file into a Transcript object.
        
        Expected CSV format:
        Course_Code,Credits,Grade,Semester
        ENG102,3,A,Spring 2023
        MAT116,0,B,Spring 2023
        ...
        
        Args:
            file_path: Path to CSV file
            student_id: Optional student ID
            student_name: Optional student name
            program: Optional program name
            
        Returns:
            Transcript object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If CSV format is invalid
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        transcript = Transcript(
            student_id=student_id,
            student_name=student_name,
            program=program
        )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            required_headers = {'Course_Code', 'Credits', 'Grade', 'Semester'}
            if not required_headers.issubset(set(reader.fieldnames or [])):
                raise ValueError(
                    f"CSV must contain headers: {required_headers}\n"
                    f"Found: {reader.fieldnames}"
                )
            
            line_num = 1
            for row in reader:
                line_num += 1
                try:
                    # Skip empty rows
                    if not any(row.values()):
                        continue
                    
                    record = CourseRecord(
                        course_code=row['Course_Code'],
                        credits=row['Credits'],
                        grade=row['Grade'],
                        semester=row['Semester']
                    )
                    transcript.add_record(record)
                    
                except (KeyError, ValueError) as e:
                    raise ValueError(
                        f"Error parsing line {line_num}: {e}\n"
                        f"Row data: {row}"
                    )
        
        if len(transcript) == 0:
            raise ValueError(f"No valid course records found in {file_path}")
        
        return transcript
    
    @staticmethod
    def validate_csv(file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate CSV file format without fully parsing.
        
        Returns:
            (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"File not found: {file_path}"
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Check headers
                required_headers = {'Course_Code', 'Credits', 'Grade', 'Semester'}
                if not required_headers.issubset(set(reader.fieldnames or [])):
                    return False, f"Missing required headers: {required_headers - set(reader.fieldnames or [])}"
                
                # Try to read first row
                try:
                    first_row = next(reader)
                    CourseRecord(
                        course_code=first_row['Course_Code'],
                        credits=first_row['Credits'],
                        grade=first_row['Grade'],
                        semester=first_row['Semester']
                    )
                except StopIteration:
                    return False, "CSV file is empty"
                except (KeyError, ValueError) as e:
                    return False, f"Invalid data format: {e}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    @staticmethod
    def create_sample_csv(file_path: str, include_edge_cases: bool = False):
        """
        Create a sample CSV file for testing.
        
        Args:
            file_path: Where to save the CSV
            include_edge_cases: Include retakes, failures, withdrawals
        """
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Course_Code', 'Credits', 'Grade', 'Semester'])
            
            # Basic courses
            writer.writerow(['ENG102', '3', 'A', 'Spring 2023'])
            writer.writerow(['MAT116', '0', 'B', 'Spring 2023'])  # 0-credit
            writer.writerow(['CSE115', '4', 'A-', 'Summer 2023'])
            writer.writerow(['CSE115L', '0', 'A', 'Summer 2023'])  # Lab
            
            if include_edge_cases:
                # Failed course
                writer.writerow(['HIS103', '3', 'F', 'Summer 2023'])
                # Retaken and passed
                writer.writerow(['HIS103', '3', 'B+', 'Spring 2024'])
                # Withdrawn
                writer.writerow(['CSE173', '3', 'W', 'Fall 2023'])
                # Another failure
                writer.writerow(['CSE225', '3', 'F', 'Fall 2024'])
                # Multiple retakes
                writer.writerow(['PHY107', '3', 'D', 'Fall 2023'])
                writer.writerow(['PHY107', '3', 'C+', 'Spring 2024'])
                writer.writerow(['PHY107', '3', 'B', 'Summer 2024'])


if __name__ == "__main__":
    import tempfile
    import os
    
    print("CSV Parser Test")
    print("=" * 50)
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_file = f.name
    
    try:
        # Create sample CSV
        TranscriptParser.create_sample_csv(test_file, include_edge_cases=True)
        print(f"Created test file: {test_file}")
        
        # Validate
        is_valid, error = TranscriptParser.validate_csv(test_file)
        print(f"\nValidation: {'✓ PASS' if is_valid else '✗ FAIL'}")
        if error:
            print(f"Error: {error}")
        
        # Parse
        transcript = TranscriptParser.parse_csv(
            test_file,
            student_id="2014567890",
            student_name="Test Student",
            program="BBA"
        )
        
        print(f"\n{transcript}")
        print(f"Total records: {len(transcript)}")
        print(f"Unique courses: {len(transcript.get_unique_courses())}")
        
        print("\nRetaken courses:")
        for code, attempts in transcript.get_retaken_courses().items():
            print(f"  {code}:")
            for att in attempts:
                print(f"    {att.grade} ({att.semester})")
        
        print("\nFirst 5 records:")
        for record in transcript.records[:5]:
            print(f"  {record}")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.unlink(test_file)
            print(f"\nCleaned up test file")
