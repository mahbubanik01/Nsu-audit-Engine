"""
PDF Transcript Parser
Extracts transcript data from PDF files using pdfplumber.
"""

import re
from typing import Optional, List, Dict
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

from models.transcript import Transcript, CourseRecord


class PDFParser:
    """
    Parses PDF transcript files into Transcript objects.

    Handles:
    1. Table-based PDFs (most common for official transcripts)
    2. Text-based PDFs (fallback regex extraction)
    """

    # Common column header patterns
    HEADER_PATTERNS = {
        "course_code": re.compile(r"course[\s_]*(?:code|id|no)?", re.IGNORECASE),
        "credits": re.compile(r"credit(?:s)?|cr\.?|hours?", re.IGNORECASE),
        "grade": re.compile(r"grade|letter[\s_]*grade|mark", re.IGNORECASE),
        "semester": re.compile(r"semester|term|session|period", re.IGNORECASE),
    }

    # Course code pattern (e.g., CSE115, MAT120, ENG102L)
    COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4})\s?(\d{3,4}[A-Z]?)\b")
    # Grade pattern
    GRADE_RE = re.compile(r"\b(A\s?[-]?|B\s?[+-]?|C\s?[+-]?|D\s?[+]?|F|W|I)\b", re.IGNORECASE)

    # Semester pattern (e.g., "Spring 2023", "Fall 2024")
    SEMESTER_RE = re.compile(
        r"\b(Spring|Summer|Fall|Winter)\s+(\d{4})\b", re.IGNORECASE
    )

    @classmethod
    def parse_pdf(
        cls,
        file_path: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        program: Optional[str] = None,
    ) -> Transcript:
        """
        Parse a PDF transcript file.

        Strategy:
        1. Try table extraction first (most reliable)
        2. Fall back to text-based regex extraction

        Args:
            file_path: Path to PDF file
            student_id: Optional student ID
            student_name: Optional student name
            program: Optional program name

        Returns:
            Transcript object

        Raises:
            ImportError: If pdfplumber is not installed
            FileNotFoundError: If file doesn't exist
            ValueError: If no valid records found
        """
        if pdfplumber is None:
            raise ImportError(
                "pdfplumber is required for PDF parsing.\n"
                "Install it with: pip install pdfplumber"
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        transcript = Transcript(
            student_id=student_id,
            student_name=student_name,
            program=program,
        )

        # Try table extraction first
        records = cls._extract_from_tables(file_path)

        # Fall back to text extraction
        if not records:
            records = cls._extract_from_text(file_path)

        if not records:
            raise ValueError(
                f"Could not extract transcript data from {file_path}.\n"
                f"Ensure the PDF contains a table with columns:\n"
                f"  Course Code, Credits, Grade, Semester"
            )

        for record in records:
            transcript.add_record(record)

        return transcript

    @classmethod
    def _extract_from_tables(cls, file_path: str) -> List[CourseRecord]:
        """Extract records from PDF tables."""
        records = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if not tables:
                    continue

                for table in tables:
                    if not table or len(table) < 2:
                        continue

                    # Try to identify column mapping from header row
                    header_row = table[0]
                    col_map = cls._identify_columns(header_row)

                    if col_map:
                        # Structured table with identifiable headers
                        for row in table[1:]:
                            record = cls._parse_table_row(row, col_map)
                            if record:
                                records.append(record)
                    else:
                        # Try to parse without headers (positional)
                        for row in table:
                            record = cls._parse_row_positional(row)
                            if record:
                                records.append(record)

        return records

    @classmethod
    def _extract_from_text(cls, file_path: str) -> List[CourseRecord]:
        """
        Fallback: Extract records from raw PDF text using regex.
        Looks for patterns like: CSE115  3  A-  Spring 2023
        """
        records = []
        current_semester = None

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""

                for line in text.split("\n"):
                    line = line.strip()
                    if not line:
                        continue

                    # Check for semester header
                    sem_match = cls.SEMESTER_RE.search(line)
                    if sem_match:
                        current_semester = f"{sem_match.group(1).title()} {sem_match.group(2)}"

                    # Check for course record
                    course_match = cls.COURSE_CODE_RE.search(line)
                    grade_match = cls.GRADE_RE.search(line)

                    if course_match and grade_match:
                        course_code = f"{course_match.group(1)}{course_match.group(2)}".upper().replace(" ", "")
                        grade = grade_match.group(1).upper().replace(" ", "")

                        # Try to extract credits (number near course code)
                        credits = cls._extract_credits_from_line(line)

                        # Use line-level semester if found, otherwise current
                        semester = current_semester or "Unknown"
                        line_sem = cls.SEMESTER_RE.search(line)
                        if line_sem:
                            semester = f"{line_sem.group(1).title()} {line_sem.group(2)}"

                        try:
                            record = CourseRecord(
                                course_code=course_code,
                                credits=credits,
                                grade=grade,
                                semester=semester,
                            )
                            records.append(record)
                        except ValueError:
                            continue

        return records

    @classmethod
    def _identify_columns(cls, header_row: list) -> Optional[Dict[str, int]]:
        """Try to identify column indices from a header row."""
        if not header_row:
            return None

        col_map = {}
        for idx, cell in enumerate(header_row):
            if cell is None:
                continue
            cell_str = str(cell).strip()

            for field, pattern in cls.HEADER_PATTERNS.items():
                if pattern.search(cell_str) and field not in col_map:
                    col_map[field] = idx
                    break

        # Need at least course_code and grade
        if "course_code" in col_map and "grade" in col_map:
            return col_map
        return None

    @classmethod
    def _parse_table_row(
        cls, row: list, col_map: Dict[str, int]
    ) -> Optional[CourseRecord]:
        """Parse a table row using identified column mapping."""
        try:
            course_code = str(row[col_map["course_code"]] or "").strip().upper().replace(" ", "")
            code_match = cls.COURSE_CODE_RE.match(course_code)
            if not code_match:
                return None
            
            # Re-normalize just in case
            course_code = f"{code_match.group(1)}{code_match.group(2)}"

            grade = str(row[col_map.get("grade", -1)] or "").strip().upper().replace(" ", "")
            if not cls.GRADE_RE.match(grade):
                return None

            credits = 3.0  # default
            if "credits" in col_map:
                try:
                    credits = float(row[col_map["credits"]] or 3)
                except (ValueError, TypeError):
                    credits = 3.0

            semester = "Unknown"
            if "semester" in col_map:
                semester = str(row[col_map["semester"]] or "Unknown").strip()

            return CourseRecord(
                course_code=course_code,
                credits=credits,
                grade=grade,
                semester=semester,
            )
        except (IndexError, ValueError, TypeError):
            return None

    @classmethod
    def _parse_row_positional(cls, row: list) -> Optional[CourseRecord]:
        """Try to parse a row without header info (positional guessing)."""
        if not row or len(row) < 3:
            return None

        row_strs = [str(cell or "").strip() for cell in row]

        # Find course code
        course_code = None
        grade = None
        credits = 3.0
        semester = "Unknown"

        for cell in row_strs:
            c_match = cls.COURSE_CODE_RE.match(cell)
            if not course_code and c_match:
                course_code = f"{c_match.group(1)}{c_match.group(2)}".upper()
            elif not grade and cls.GRADE_RE.match(cell):
                grade = cell.upper().replace(" ", "")
            elif cls.SEMESTER_RE.search(cell):
                sem_m = cls.SEMESTER_RE.search(cell)
                semester = f"{sem_m.group(1).title()} {sem_m.group(2)}"
            else:
                try:
                    val = float(cell)
                    if 0 <= val <= 6:
                        credits = val
                except ValueError:
                    pass

        if course_code and grade:
            try:
                return CourseRecord(
                    course_code=course_code,
                    credits=credits,
                    grade=grade,
                    semester=semester,
                )
            except ValueError:
                return None
        return None

    @classmethod
    def _extract_credits_from_line(cls, line: str) -> float:
        """Extract credit hours from a text line."""
        # Look for a standalone number (0-6 range, typical credit values)
        numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", line)
        for num_str in numbers:
            val = float(num_str)
            if 0 <= val <= 6 and val != int(
                "".join(filter(str.isdigit, line.split()[0][:3])) or "0"
            ):
                return val
        return 3.0  # default
