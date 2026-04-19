"""
Level 2: GPA Calculator & Waiver Handler
Calculates CGPA with NSU rules and handles course waivers
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from models.transcript import Transcript, CourseRecord
from models.grade import NSUGradeSystem


@dataclass
class GPAReport:
    """Report of GPA calculations"""
    cgpa: float
    total_quality_points: float
    total_gpa_credits: float  # Credits that count in GPA
    
    # Grade distribution
    grade_distribution: Dict[str, int]
    
    # Academic standing
    class_standing: str
    honor_status: Optional[str]
    is_on_probation: bool
    
    # Semester-wise GPA
    semester_gpas: Dict[str, float]
    
    # Waivers
    waived_courses: Set[str]
    
    def __str__(self) -> str:
        honor_line = f"  🏆 Honors: {self.honor_status}\n" if self.honor_status else ""
        probation_warning = "  ⚠️  ACADEMIC PROBATION\n" if self.is_on_probation else ""
        waived_line = f"  Waived Courses: {', '.join(sorted(self.waived_courses))}\n" if self.waived_courses else ""
        
        return f"""
LEVEL 2: GPA & WAIVER REPORT
{'=' * 60}
CGPA:                      {self.cgpa:.2f}
Class Standing:            {self.class_standing}
{honor_line}{probation_warning}
Total Quality Points:      {self.total_quality_points:.2f}
Total GPA Credits:         {self.total_gpa_credits:.1f}

{waived_line}Grade Distribution:
{GPACalculator._format_grade_distribution(self.grade_distribution)}
{'=' * 60}
"""


class GPACalculator:
    """
    Level 2: GPA Calculator with Waiver Handling
    
    Handles edge cases:
    1. 0-credit courses - excluded from GPA calculation
    2. W and I grades - don't count in GPA
    3. Retaken courses - only best grade counts
    4. F grades - count as 0.0 until retaken
    5. Course waivers - excluded from requirements
    """
    
    @staticmethod
    def calculate_cgpa(transcript: Transcript, waived_courses: Optional[Set[str]] = None) -> GPAReport:
        """
        Calculate CGPA according to NSU rules.
        
        NSU CGPA Rules:
        1. Only graded courses (A through F) count
        2. 0-credit courses are EXCLUDED
        3. For retakes, use BEST grade only
        4. F counts as 0.0 until course is retaken
        5. CGPA = Total Quality Points / Total Credits Attempted
        
        Args:
            transcript: Student transcript
            waived_courses: Set of course codes that are waived
            
        Returns:
            GPAReport with CGPA and details
        """
        if waived_courses is None:
            waived_courses = set()
        
        # Normalize waived courses
        waived_courses = {c.upper().strip() for c in waived_courses}
        
        # Get best attempts for all courses
        course_best_attempts = {}
        for course_code in transcript.get_unique_courses():
            # Skip waived courses
            if course_code in waived_courses:
                continue
            
            best = transcript.get_best_attempt(course_code)
            course_best_attempts[course_code] = best
        
        # Calculate CGPA using best attempts
        total_quality_points = 0.0
        total_credits = 0.0
        grade_distribution = {}
        
        for course_code, record in course_best_attempts.items():
            # Skip if doesn't count in GPA
            if not NSUGradeSystem.counts_in_gpa(record.grade):
                continue
            
            # Skip 0-credit courses
            if record.credits == 0:
                continue
            
            # Add to totals
            total_quality_points += record.quality_points
            total_credits += record.credits
            
            # Track grade distribution
            grade_distribution[record.grade] = grade_distribution.get(record.grade, 0) + 1
            
        # Calculate CGPA
        cgpa = total_quality_points / total_credits if total_credits > 0 else 0.0
        
        # Calculate Term GPAs (Semester GPAs) using ALL records from those semesters
        # This reflects actual performance in each term
        semester_data = {}
        for record in transcript.records:
            # Skip if doesn't count in GPA or is 0-credit
            if not NSUGradeSystem.counts_in_gpa(record.grade) or record.credits == 0:
                continue
            
            if record.semester not in semester_data:
                semester_data[record.semester] = {'points': 0.0, 'credits': 0.0}
            
            semester_data[record.semester]['points'] += record.quality_points
            semester_data[record.semester]['credits'] += record.credits
            
        # Calculate semester GPAs
        semester_gpas = {}
        for semester, data in semester_data.items():
            if data['credits'] > 0:
                semester_gpas[semester] = data['points'] / data['credits']
        
        # Determine academic standing
        class_standing = NSUGradeSystem.get_class_standing(cgpa)
        honor_status = NSUGradeSystem.get_honor_status(cgpa)
        is_on_probation = cgpa < 2.0
        
        return GPAReport(
            cgpa=cgpa,
            total_quality_points=total_quality_points,
            total_gpa_credits=total_credits,
            grade_distribution=grade_distribution,
            class_standing=class_standing,
            honor_status=honor_status,
            is_on_probation=is_on_probation,
            semester_gpas=semester_gpas,
            waived_courses=waived_courses
        )
    
    @staticmethod
    @staticmethod
    def _format_grade_distribution(distribution: Dict[str, int]) -> str:
        """Format grade distribution for display"""
        if not distribution:
            return "  No grades counted in GPA"
        
        lines = []
        # Sort by grade point (highest first)
        sorted_grades = sorted(
            distribution.items(),
            key=lambda x: NSUGradeSystem.get_grade_point(x[0]),
            reverse=True
        )
        
        for grade, count in sorted_grades:
            point = NSUGradeSystem.get_grade_point(grade)
            bar = '█' * count
            lines.append(f"  {grade:<3} ({point:.1f}): {bar} {count}")
        
        return "\n".join(lines)
    
    @staticmethod
    def get_semester_breakdown(report: GPAReport) -> str:
        """Get semester-by-semester GPA breakdown"""
        if not report.semester_gpas:
            return "No semester data available"
        
        lines = ["\nSEMESTER-WISE GPA"]
        lines.append("=" * 60)
        lines.append(f"{'Semester':<20} {'GPA':<10} {'Standing'}")
        lines.append("-" * 60)
        
        # Sort semesters chronologically
        term_order = {'Spring': 1, 'Summer': 2, 'Fall': 3}
        sorted_semesters = sorted(
            report.semester_gpas.items(),
            key=lambda x: (
                int(x[0].split()[1]),  # Year
                term_order.get(x[0].split()[0], 0)  # Term
            )
        )
        
        for semester, gpa in sorted_semesters:
            standing = NSUGradeSystem.get_class_standing(gpa)
            lines.append(f"{semester:<20} {gpa:<10.2f} {standing}")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    @staticmethod
    def prompt_for_waivers(waivable_courses: List[str]) -> Set[str]:
        """
        Interactive prompt for course waivers.
        Returns set of courses to waive.
        """
        if not waivable_courses:
            return set()
        
        print("\nWAIVER CHECK")
        print("=" * 60)
        print("The following courses can be waived:")
        for i, course in enumerate(waivable_courses, 1):
            print(f"  {i}. {course}")
        
        print("\nEnter course codes to waive (comma-separated), or press Enter to skip:")
        user_input = input("> ").strip()
        
        if not user_input:
            return set()
        
        # Parse input
        waived = set()
        for code in user_input.split(','):
            code = code.strip().upper()
            if code in waivable_courses:
                waived.add(code)
            else:
                print(f"Warning: '{code}' is not a waivable course")
        
        return waived


if __name__ == "__main__":
    from parsers.csv_parser import TranscriptParser
    import tempfile
    import os
    
    print("LEVEL 2: GPA Calculator Test")
    print("=" * 60)
    
    # Create test transcript
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_file = f.name
    
    try:
        TranscriptParser.create_sample_csv(test_file, include_edge_cases=True)
        transcript = TranscriptParser.parse_csv(test_file, program="BBA")
        
        print(f"Loaded transcript: {len(transcript)} records")
        
        # Calculate CGPA without waivers
        print("\n--- Without Waivers ---")
        report1 = GPACalculator.calculate_cgpa(transcript)
        print(report1)
        print(GPACalculator.get_semester_breakdown(report1))
        
        # Calculate CGPA with waivers
        print("\n--- With Waivers (ENG102, MAT116) ---")
        waived = {'ENG102', 'MAT116'}
        report2 = GPACalculator.calculate_cgpa(transcript, waived)
        print(report2)
        
        # Show difference
        print(f"\nImpact of Waivers:")
        print(f"  CGPA Change: {report1.cgpa:.3f} → {report2.cgpa:.3f}")
        print(f"  Credits Change: {report1.total_gpa_credits:.1f} → {report2.total_gpa_credits:.1f}")
        
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
