"""
Image / OCR Transcript Parser
Uses Tesseract OCR (via pytesseract) + Pillow to extract text from
photos/screenshots of transcripts, then delegates to TextParser.

Supported: .png, .jpg, .jpeg, .bmp, .tiff, .webp
Requires: pip install pytesseract Pillow
          + Tesseract OCR installed on the system
"""

import re
from typing import Optional
from pathlib import Path

from models.transcript import Transcript, CourseRecord


class ImageParser:
    """
    Parses transcript images via OCR.
    1. Image → grayscale → threshold
    2. OCR to extract raw text
    3. Regex extraction of course records
    """

    COURSE_CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{3,4}[A-Z]?)\b")
    GRADE_RE = re.compile(r"\b(A|A-|B\+|B|B-|C\+|C|C-|D\+|D|F|W|I)\b")
    SEMESTER_RE = re.compile(
        r"\b(Spring|Summer|Fall|Winter)\s+(\d{4})\b", re.IGNORECASE
    )

    @classmethod
    def parse_image(
        cls,
        file_path: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        program: Optional[str] = None,
    ) -> Transcript:
        """
        Parse a transcript image using OCR.

        Args:
            file_path: Path to image file
            student_id: Optional student ID
            student_name: Optional student name
            program: Optional program type

        Returns:
            Transcript object with extracted records
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Try to import OCR dependencies
        try:
            from PIL import Image, ImageFilter
            import pytesseract
            
            # Configure Tesseract path (Windows specific path found on user system)
            tesseract_exe = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if Path(tesseract_exe).exists():
                pytesseract.pytesseract.tesseract_cmd = tesseract_exe
                
        except ImportError:
            raise ImportError(
                "OCR requires 'pytesseract' and 'Pillow'.\n"
                "Install with: pip install pytesseract Pillow\n"
                "Also install Tesseract OCR on your system:\n"
                "  Windows: https://github.com/UB-Mannheim/tesseract/wiki\n"
                "  Linux: sudo apt install tesseract-ocr\n"
                "  Mac: brew install tesseract"
            )

        # Load and preprocess image
        img = Image.open(file_path)

        # Convert to grayscale
        img = img.convert("L")

        # Apply sharpening for better OCR
        img = img.filter(ImageFilter.SHARPEN)

        # Threshold to pure black/white for cleaner OCR
        threshold = 140
        img = img.point(lambda p: 255 if p > threshold else 0, mode="1")

        # Run OCR
        try:
            raw_text = pytesseract.image_to_string(img, config="--psm 6")
        except Exception as e:
            raise RuntimeError(
                f"OCR failed: {e}\n"
                "Make sure Tesseract is installed and in your PATH.\n"
                "  Windows: https://github.com/UB-Mannheim/tesseract/wiki"
            )

        if not raw_text or not raw_text.strip():
            raise ValueError(
                "OCR could not extract any text from the image.\n"
                "Ensure the image is clear and contains readable text."
            )

        print(f"[OCR] Extracted {len(raw_text)} characters from image.")

        # Parse extracted text for course records
        transcript = Transcript(
            student_id=student_id,
            student_name=student_name,
            program=program,
        )

        records = cls._parse_ocr_text(raw_text)

        if not records:
            raise ValueError(
                f"OCR extracted text but could not find course records.\n"
                f"Extracted text preview:\n{raw_text[:500]}\n...\n"
                f"Expected format: COURSE_CODE  CREDITS  GRADE  SEMESTER"
            )

        for record in records:
            transcript.add_record(record)

        print(f"[OCR] Extracted {len(records)} course records from image.")
        return transcript

    @classmethod
    def _parse_ocr_text(cls, text: str) -> list:
        """Parse OCR-extracted text line by line to find course records."""
        records = []
        current_semester = None

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Check for semester header
            sem_match = cls.SEMESTER_RE.search(line)
            if sem_match and not cls.COURSE_CODE_RE.search(line):
                current_semester = (
                    f"{sem_match.group(1).title()} {sem_match.group(2)}"
                )
                continue

            # Try to extract course record
            course_match = cls.COURSE_CODE_RE.search(line)
            grade_match = cls.GRADE_RE.search(line)

            if not course_match or not grade_match:
                continue

            course_code = course_match.group(1)
            grade = grade_match.group(1)

            # Extract credits (look for small numbers)
            credits = 3.0
            numbers = re.findall(r"\b(\d+(?:\.\d+)?)\b", line)
            for num_str in numbers:
                val = float(num_str)
                if 0 < val <= 6 and num_str not in course_code:
                    credits = val
                    break

            # Extract semester from line or use current
            semester = current_semester or "Unknown"
            if sem_match:
                semester = (
                    f"{sem_match.group(1).title()} {sem_match.group(2)}"
                )

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
