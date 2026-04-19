"""
Text / TSV / JSON Transcript Parser
Handles plain-text, tab-separated, and JSON transcript formats.
"""

import re
import json
import csv
from typing import Optional, List
from pathlib import Path
from io import StringIO

from models.transcript import Transcript, CourseRecord


class TextParser:
    """
    Parses text-based transcript files: .txt, .tsv, .json
    """

    COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{3,4}[A-Z]?)\b")
    GRADE_RE = re.compile(r"\b(A|A-|B\+|B|B-|C\+|C|C-|D\+|D|F|W|I)\b")
    SEMESTER_RE = re.compile(
        r"\b(Spring|Summer|Fall|Winter)\s+(\d{4})\b", re.IGNORECASE
    )

    @classmethod
    def parse_txt(
        cls,
        file_path: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        program: Optional[str] = None,
    ) -> Transcript:
        """Parse a plain text or TSV transcript."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        transcript = Transcript(
            student_id=student_id,
            student_name=student_name,
            program=program,
        )

        ext = path.suffix.lower()

        if ext == ".tsv":
            records = cls._parse_tsv(content)
        else:
            records = cls._parse_text(content)

        if not records:
            raise ValueError(
                f"Could not extract transcript data from {file_path}.\n"
                f"Expected format: Course_Code  Credits  Grade  Semester\n"
                f"Each line should contain a course code and grade."
            )

        for record in records:
            transcript.add_record(record)

        return transcript

    @classmethod
    def parse_json(
        cls,
        file_path: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        program: Optional[str] = None,
    ) -> Transcript:
        """
        Parse a JSON transcript.

        Expected formats:
        1. Array of objects: [{"course_code": "CSE115", "credits": 3, "grade": "A", "semester": "Fall 2023"}, ...]
        2. Object with records key: {"records": [...], "student_id": "...", "student_name": "..."}
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle wrapper object
        if isinstance(data, dict):
            student_id = student_id or data.get("student_id")
            student_name = student_name or data.get("student_name")
            program = program or data.get("program")
            records_data = data.get("records", data.get("courses", []))
        elif isinstance(data, list):
            records_data = data
        else:
            raise ValueError("JSON must be an array of records or an object with a 'records' key.")

        transcript = Transcript(
            student_id=student_id,
            student_name=student_name,
            program=program,
        )

        # Flexible key mapping
        code_keys = ["course_code", "code", "course", "courseCode", "Course_Code"]
        credit_keys = ["credits", "credit", "credit_hours", "cr", "Credits"]
        grade_keys = ["grade", "letter_grade", "Grade"]
        semester_keys = ["semester", "term", "session", "Semester"]

        for item in records_data:
            if not isinstance(item, dict):
                continue

            course_code = None
            for key in code_keys:
                if key in item:
                    course_code = str(item[key]).strip()
                    break

            grade = None
            for key in grade_keys:
                if key in item:
                    grade = str(item[key]).strip()
                    break

            if not course_code or not grade:
                continue

            credits = 3.0
            for key in credit_keys:
                if key in item:
                    try:
                        credits = float(item[key])
                    except (ValueError, TypeError):
                        pass
                    break

            semester = "Unknown"
            for key in semester_keys:
                if key in item:
                    semester = str(item[key]).strip()
                    break

            try:
                record = CourseRecord(
                    course_code=course_code,
                    credits=credits,
                    grade=grade,
                    semester=semester,
                )
                transcript.add_record(record)
            except ValueError:
                continue

        if len(transcript) == 0:
            raise ValueError(
                f"No valid records found in {file_path}.\n"
                f"Expected JSON format: "
                f'[{{"course_code": "CSE115", "credits": 3, "grade": "A", "semester": "Fall 2023"}}]'
            )

        return transcript

    @classmethod
    def _parse_tsv(cls, content: str) -> List[CourseRecord]:
        """Parse tab-separated content."""
        records = []
        reader = csv.reader(StringIO(content), delimiter="\t")

        rows = list(reader)
        if not rows:
            return records

        # Try to identify header
        header = [h.strip().lower() for h in rows[0]]
        col_map = {}
        for idx, h in enumerate(header):
            if "course" in h or "code" in h:
                col_map["course_code"] = idx
            elif "credit" in h or "cr" in h or "hour" in h:
                col_map["credits"] = idx
            elif "grade" in h or "mark" in h:
                col_map["grade"] = idx
            elif "semester" in h or "term" in h:
                col_map["semester"] = idx

        start = 1 if col_map else 0

        for row in rows[start:]:
            if not row or all(not cell.strip() for cell in row):
                continue

            if col_map and "course_code" in col_map and "grade" in col_map:
                try:
                    course_code = row[col_map["course_code"]].strip()
                    grade = row[col_map["grade"]].strip()
                    credits = float(row[col_map.get("credits", -1)]) if "credits" in col_map else 3.0
                    semester = row[col_map.get("semester", -1)].strip() if "semester" in col_map else "Unknown"

                    if cls.COURSE_CODE_RE.match(course_code) and cls.GRADE_RE.match(grade):
                        records.append(CourseRecord(
                            course_code=course_code,
                            credits=credits,
                            grade=grade,
                            semester=semester,
                        ))
                except (IndexError, ValueError):
                    continue
            else:
                # Positional fallback
                record = cls._parse_line("\t".join(row))
                if record:
                    records.append(record)

        return records

    @classmethod
    def _parse_text(cls, content: str) -> List[CourseRecord]:
        """Parse plain text content line by line."""
        records = []
        current_semester = None

        for line in content.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for semester header
            sem_match = cls.SEMESTER_RE.search(line)
            if sem_match and not cls.COURSE_CODE_RE.search(line):
                current_semester = f"{sem_match.group(1).title()} {sem_match.group(2)}"
                continue

            record = cls._parse_line(line, current_semester)
            if record:
                records.append(record)
                # Update semester if found inline
                if sem_match:
                    current_semester = f"{sem_match.group(1).title()} {sem_match.group(2)}"

        return records

    @classmethod
    def _parse_line(cls, line: str, current_semester: str = None) -> Optional[CourseRecord]:
        """Try to extract a course record from a single line."""
        course_match = cls.COURSE_CODE_RE.search(line)
        grade_match = cls.GRADE_RE.search(line)

        if not course_match or not grade_match:
            return None

        course_code = course_match.group(1)
        grade = grade_match.group(1)

        # Extract credits
        credits = 3.0
        numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", line)
        for num_str in numbers:
            val = float(num_str)
            if 0 < val <= 6 and num_str not in course_code:
                credits = val
                break

        # Extract semester
        semester = current_semester or "Unknown"
        sem_m = cls.SEMESTER_RE.search(line)
        if sem_m:
            semester = f"{sem_m.group(1).title()} {sem_m.group(2)}"

        try:
            return CourseRecord(
                course_code=course_code,
                credits=credits,
                grade=grade,
                semester=semester,
            )
        except ValueError:
            return None
