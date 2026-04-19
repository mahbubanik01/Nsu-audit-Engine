"""
Document Router
Unified document ingestion layer that auto-detects file type
and routes to the appropriate parser.

Supported: .csv, .pdf, .docx, .doc, .xlsx, .xls, .txt, .tsv, .json
"""

from typing import Optional
from pathlib import Path

from models.transcript import Transcript
from parsers.csv_parser import TranscriptParser


# Supported file extensions
SUPPORTED_EXTENSIONS = {
    ".csv", ".pdf", ".docx", ".doc",
    ".xlsx", ".xls",
    ".txt", ".tsv", ".json",
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp",
}

# Image extensions (subset)
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}


class DocumentRouter:
    """
    Auto-detects file type and routes to the correct parser.
    Returns a standardized Transcript object regardless of input format.
    """

    @staticmethod
    def parse(
        file_path: str,
        student_id: Optional[str] = None,
        student_name: Optional[str] = None,
        program: Optional[str] = None,
    ) -> Transcript:
        """
        Parse a transcript file of any supported format.

        Supported formats:
        - .csv   -> CSV parser
        - .pdf   -> PDF parser (pdfplumber)
        - .docx  -> DOCX parser (python-docx)
        - .doc   -> DOCX parser (limited)
        - .xlsx  -> Excel parser (openpyxl)
        - .xls   -> Excel parser (limited)
        - .txt   -> Plain text parser
        - .tsv   -> Tab-separated parser
        - .json  -> JSON parser

        Args:
            file_path: Path to transcript file
            student_id: Optional student ID
            student_name: Optional student name
            program: Optional program name

        Returns:
            Transcript object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If format is unsupported or parsing fails
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()

        if ext == ".csv":
            return TranscriptParser.parse_csv(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        elif ext == ".pdf":
            from parsers.pdf_parser import PDFParser

            return PDFParser.parse_pdf(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        elif ext in (".docx", ".doc"):
            from parsers.docx_parser import DOCXParser

            if ext == ".doc":
                print(
                    "Warning: .doc format has limited support. "
                    "Consider converting to .docx for best results."
                )

            return DOCXParser.parse_docx(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        elif ext in (".xlsx", ".xls"):
            from parsers.excel_parser import ExcelParser

            if ext == ".xls":
                print(
                    "Warning: .xls (legacy Excel) has limited support. "
                    "Consider converting to .xlsx for best results."
                )

            return ExcelParser.parse_excel(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        elif ext in (".txt", ".tsv"):
            from parsers.text_parser import TextParser

            return TextParser.parse_txt(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        elif ext == ".json":
            from parsers.text_parser import TextParser

            return TextParser.parse_json(
                file_path,
                student_id=student_id,
                student_name=student_name,
                program=program,
            )

        else:
            # Check if it's an image
            if ext in IMAGE_EXTENSIONS:
                from parsers.image_parser import ImageParser

                return ImageParser.parse_image(
                    file_path,
                    student_id=student_id,
                    student_name=student_name,
                    program=program,
                )
            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise ValueError(
                f"Unsupported file format: '{ext}'\n"
                f"Supported formats: {supported}"
            )

    @staticmethod
    def get_supported_formats() -> str:
        """Get a human-readable list of supported formats."""
        return (
            "Supported transcript formats:\n"
            "  .csv   - Comma-separated values (recommended)\n"
            "  .pdf   - PDF documents (requires pdfplumber)\n"
            "  .docx  - Word documents (requires python-docx)\n"
            "  .doc   - Legacy Word documents (limited support)\n"
            "  .xlsx  - Excel spreadsheets (requires openpyxl)\n"
            "  .xls   - Legacy Excel spreadsheets (limited support)\n"
            "  .txt   - Plain text transcripts\n"
            "  .tsv   - Tab-separated values\n"
            "  .json  - JSON formatted transcripts\n"
            "  .png   - Image files (requires Tesseract OCR)\n"
            "  .jpg   - JPEG images (requires Tesseract OCR)\n"
            "  .bmp   - Bitmap images (requires Tesseract OCR)\n"
            "  .tiff  - TIFF images (requires Tesseract OCR)\n"
            "  .webp  - WebP images (requires Tesseract OCR)"
        )

    @staticmethod
    def is_supported(file_path: str) -> bool:
        """Check if a file format is supported."""
        return Path(file_path).suffix.lower() in SUPPORTED_EXTENSIONS
