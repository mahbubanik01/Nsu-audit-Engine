"""
Level 1: Credit Tally Engine
Calculates total valid credits earned by a student
"""

from typing import Dict, List
from dataclasses import dataclass
from models.transcript import Transcript, CourseRecord
from models.grade import NSUGradeSystem


@dataclass
class CreditReport:
    """Report of credit calculations"""
    total_earned_credits: float
    total_attempted_credits: float
    courses_passed: int
    courses_failed: int
    courses_withdrawn: int
    zero_credit_courses: int
    retaken_courses: int
    
    # Detailed breakdown
    course_details: List[Dict] = None
    
    def __post_init__(self):
        if self.course_details is None:
            self.course_details = []
    
    def __str__(self) -> str:
        return f"""
LEVEL 1: CREDIT TALLY REPORT
{'=' * 60}
Total Earned Credits:      {self.total_earned_credits:.1f}
Total Attempted Credits:   {self.total_attempted_credits:.1f}

Course Statistics:
  ✓ Passed:                {self.courses_passed}
  ✗ Failed:                {self.courses_failed}
  ⊘ Withdrawn:             {self.courses_withdrawn}
  ○ Zero-Credit Courses:   {self.zero_credit_courses}
  ⟲ Retaken Courses:       {self.retaken_courses}
{'=' * 60}
"""


class CreditCalculator:
    """
    Level 1: Credit Tally Engine
    
    Handles edge cases:
    1. Retaken courses - only count credits once (from best attempt)
    2. Failed courses (F) - count as attempted but not earned
    3. Withdrawn courses (W) - don't count at all
    4. Zero-credit courses (labs) - track but don't affect totals
    """
    
    @staticmethod
    def calculate_credits(transcript: Transcript) -> CreditReport:
        """
        Calculate total valid credits from a transcript.
        
        Key Rules:
        - Only passing grades (A through D) earn credits
        - F grades are attempted but not earned
        - W and I grades don't count as attempted or earned
        - For retaken courses, only count the best attempt
        - 0-credit courses are tracked but don't contribute to totals
        
        Args:
            transcript: Student transcript
            
        Returns:
            CreditReport with detailed breakdown
        """
        # Track best attempt for each course
        course_best_attempts = {}
        retaken_course_codes = set()
        
        # First pass: identify retaken courses and find best attempts
        for course_code in transcript.get_unique_courses():
            attempts = transcript.get_course_history(course_code)
            
            if len(attempts) > 1:
                retaken_course_codes.add(course_code)
            
            best = transcript.get_best_attempt(course_code)
            course_best_attempts[course_code] = best
        
        # Second pass: calculate credits using best attempts only
        earned_credits = 0.0
        attempted_credits = 0.0
        courses_passed = 0
        courses_failed = 0
        courses_withdrawn = 0
        zero_credit_courses = 0
        course_details = []
        
        for course_code, record in course_best_attempts.items():
            detail = {
                'course_code': course_code,
                'credits': record.credits,
                'grade': record.grade,
                'semester': record.semester,
                'is_retake': course_code in retaken_course_codes,
                'earned': 0.0,
                'status': ''
            }
            
            # Zero-credit courses
            if record.credits == 0:
                zero_credit_courses += 1
                detail['status'] = 'Zero-Credit'
                detail['earned'] = 0.0
            
            # Withdrawn courses
            elif record.grade == 'W':
                courses_withdrawn += 1
                detail['status'] = 'Withdrawn'
                detail['earned'] = 0.0
            
            # Incomplete courses
            elif record.grade == 'I':
                detail['status'] = 'Incomplete'
                detail['earned'] = 0.0
            
            # Failed courses
            elif record.grade == 'F':
                courses_failed += 1
                attempted_credits += record.credits
                detail['status'] = 'Failed'
                detail['earned'] = 0.0
            
            # Passing grades
            elif NSUGradeSystem.is_passing_grade(record.grade):
                courses_passed += 1
                earned_credits += record.credits
                attempted_credits += record.credits
                detail['status'] = 'Passed'
                detail['earned'] = record.credits
            
            course_details.append(detail)
        
        return CreditReport(
            total_earned_credits=earned_credits,
            total_attempted_credits=attempted_credits,
            courses_passed=courses_passed,
            courses_failed=courses_failed,
            courses_withdrawn=courses_withdrawn,
            zero_credit_courses=zero_credit_courses,
            retaken_courses=len(retaken_course_codes),
            course_details=course_details
        )
    
    @staticmethod
    def get_detailed_breakdown(report: CreditReport) -> str:
        """Get detailed course-by-course breakdown"""
        lines = ["\nDETAILED CREDIT BREAKDOWN"]
        lines.append("=" * 80)
        lines.append(f"{'Course':<12} {'Cr':<4} {'Grade':<6} {'Status':<15} {'Earned':<8} {'Semester'}")
        lines.append("-" * 80)
        
        for detail in sorted(report.course_details, key=lambda x: x['course_code']):
            retake_mark = "⟲" if detail['is_retake'] else " "
            lines.append(
                f"{retake_mark}{detail['course_code']:<11} "
                f"{detail['credits']:<4.0f} "
                f"{detail['grade']:<6} "
                f"{detail['status']:<15} "
                f"{detail['earned']:<8.1f} "
                f"{detail['semester']}"
            )
        
        lines.append("=" * 80)
        return "\n".join(lines)
    
    @staticmethod
    def validate_for_graduation(earned_credits: float, required_credits: float) -> tuple[bool, str]:
        """
        Check if earned credits meet graduation requirement.
        
        Returns:
            (is_sufficient, message)
        """
        if earned_credits >= required_credits:
            return True, f"✓ Credit requirement met ({earned_credits:.1f}/{required_credits} credits)"
        else:
            deficit = required_credits - earned_credits
            return False, f"✗ Insufficient credits: need {deficit:.1f} more credits ({earned_credits:.1f}/{required_credits})"


if __name__ == "__main__":
    from parsers.csv_parser import TranscriptParser
    import tempfile
    import os
    
    print("LEVEL 1: Credit Calculator Test")
    print("=" * 60)
    
    # Create test transcript with edge cases
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_file = f.name
    
    try:
        TranscriptParser.create_sample_csv(test_file, include_edge_cases=True)
        transcript = TranscriptParser.parse_csv(test_file, program="BBA")
        
        print(f"Loaded transcript: {len(transcript)} records")
        print(f"Unique courses: {len(transcript.get_unique_courses())}")
        
        # Calculate credits
        report = CreditCalculator.calculate_credits(transcript)
        
        # Print report
        print(report)
        
        # Print detailed breakdown
        print(CreditCalculator.get_detailed_breakdown(report))
        
        # Check graduation requirement
        is_sufficient, msg = CreditCalculator.validate_for_graduation(
            report.total_earned_credits, 126
        )
        print(f"\nGraduation Check (126 credits required):")
        print(f"  {msg}")
        
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
