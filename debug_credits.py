import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "nsu-audit-engine" / "src"
sys.path.insert(0, str(src_dir))

from parsers.csv_parser import TranscriptParser
from calculators.credit_calculator import CreditCalculator

def debug_credit_details():
    csv_path = "nsu-audit-engine/data/test_cases/test_retake_degrade.csv"
    transcript = TranscriptParser.parse_csv(csv_path)
    report = CreditCalculator.calculate_credits(transcript)
    
    for detail in report.course_details:
        if detail['course_code'] == 'HIS103':
            print(f"HIS103 Detail in CreditReport:")
            print(f"  Grade: {detail['grade']}")
            print(f"  Earned: {detail['earned']}")
            print(f"  Semester: {detail['semester']}")

if __name__ == "__main__":
    debug_credit_details()
