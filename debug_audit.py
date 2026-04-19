import sys
from pathlib import Path

# Add src to path
src_dir = Path(__file__).parent / "nsu-audit-engine" / "src"
sys.path.insert(0, str(src_dir))

from parsers.csv_parser import TranscriptParser
from calculators.audit_calculator import AuditCalculator
from models.program import ProgramFactory
from models.grade import NSUGradeSystem

def debug_his103():
    csv_path = "nsu-audit-engine/data/test_cases/test_retake_degrade.csv"
    transcript = TranscriptParser.parse_csv(csv_path)
    program = ProgramFactory.create_bba_program()
    
    # 1. Check Model
    best = transcript.get_best_attempt("HIS103")
    print(f"Transcript.get_best_attempt('HIS103'): {best.grade} from {best.semester}")
    
    # 2. Check Audit
    audit = AuditCalculator.perform_audit(transcript, program)
    
    # Find HIS103 in completed courses
    is_completed = "HIS103" in audit.completed_courses
    print(f"HIS103 in completed_courses: {is_completed}")
    
    # Find HIS103 in retake report data
    his_retakes = audit.retaken_courses.get("HIS103", [])
    print(f"Retake attempts for HIS103:")
    for att in his_retakes:
        print(f"  - {att['grade']} ({att['semester']}) [Is Best: {att.get('is_best')}]")
        
    # 3. Check GPA Calculation
    print("\nGPA Calculation check:")
    print(f"CGPA: {audit.gpa_report.cgpa}")
    print(f"Total Quality Points: {audit.gpa_report.total_quality_points}")
    print(f"Total GPA Credits: {audit.gpa_report.total_gpa_credits}")
    
    # Manual verification of HIS103 contribution
    grade_point = NSUGradeSystem.get_grade_point(best.grade)
    qp = best.credits * grade_point
    print(f"Manual check: {best.grade} point={grade_point}, credits={best.credits}, QP={qp}")

if __name__ == "__main__":
    debug_his103()
