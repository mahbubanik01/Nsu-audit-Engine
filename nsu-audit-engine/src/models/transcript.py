"""
Transcript Data Model
Represents a student's academic transcript
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict
from .grade import NSUGradeSystem


@dataclass
class CourseRecord:
    """Single course record from transcript"""
    course_code: str
    credits: float
    grade: str
    semester: str
    
    def __post_init__(self):
        """Validate and normalize data"""
        self.course_code = self.course_code.strip().upper()
        # Remove spaces in grade (e.g., "A -" -> "A-")
        self.grade = self.grade.strip().upper().replace(" ", "")
        self.semester = self.semester.strip()
        
        try:
            self.credits = float(self.credits)
        except ValueError:
            raise ValueError(f"Invalid credits value: {self.credits}")
    
    @property
    def is_passing(self) -> bool:
        """Check if this course was passed"""
        return NSUGradeSystem.is_passing_grade(self.grade)
    
    @property
    def earned_credits(self) -> float:
        """Get credits earned (0 if failed/withdrawn)"""
        return self.credits if self.is_passing else 0.0
    
    @property
    def quality_points(self) -> float:
        """Calculate quality points for this course"""
        if not NSUGradeSystem.counts_in_gpa(self.grade):
            return 0.0
        if self.credits == 0:
            return 0.0
        return self.credits * NSUGradeSystem.get_grade_point(self.grade)
    
    @property
    def attempted_credits(self) -> float:
        """
        Credits attempted for GPA calculation
        W and I don't count as attempted
        0-credit courses don't count in GPA
        """
        if not NSUGradeSystem.counts_in_gpa(self.grade):
            return 0.0
        if self.credits == 0:
            return 0.0
        return self.credits
    
    def __repr__(self) -> str:
        return f"CourseRecord({self.course_code}, {self.credits}cr, {self.grade}, {self.semester})"


@dataclass
class Transcript:
    """Student's complete academic transcript"""
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    program: Optional[str] = None
    records: List[CourseRecord] = field(default_factory=list)
    
    def add_record(self, record: CourseRecord):
        """Add a course record to transcript"""
        self.records.append(record)
    
    def get_course_history(self, course_code: str) -> List[CourseRecord]:
        """
        Get all attempts of a specific course.
        Returns list sorted by semester (chronologically).
        """
        return [r for r in self.records if r.course_code == course_code]
    
    def get_best_attempt(self, course_code: str) -> Optional[CourseRecord]:
        """
        Get the best attempt of a course (for retake logic).
        Returns the record with the highest grade.
        """
        attempts = self.get_course_history(course_code)
        if not attempts:
            return None
        
        # Find best grade
        best = attempts[0]
        for attempt in attempts[1:]:
            if NSUGradeSystem.compare_grades(attempt.grade, best.grade) == attempt.grade:
                best = attempt
        
        return best
    
    def get_unique_courses(self) -> Set[str]:
        """Get set of unique course codes attempted"""
        return {r.course_code for r in self.records}
    
    def get_retaken_courses(self) -> Dict[str, List[CourseRecord]]:
        """
        Get all courses that were retaken.
        Returns dict: {course_code: [list of attempts]}
        """
        course_counts = defaultdict(list)
        for record in self.records:
            course_counts[record.course_code].append(record)
        
        return {code: attempts for code, attempts in course_counts.items() 
                if len(attempts) > 1}
    
    def get_records_by_semester(self, semester: str) -> List[CourseRecord]:
        """Get all records for a specific semester"""
        return [r for r in self.records if r.semester == semester]
    
    def get_all_semesters(self) -> List[str]:
        """Get list of all semesters in chronological order"""
        semesters = list(set(r.semester for r in self.records))
        # Sort by year and term (Spring < Summer < Fall)
        term_order = {'Spring': 1, 'Summer': 2, 'Fall': 3}
        return sorted(semesters, key=lambda s: (
            int(s.split()[1]),  # Year
            term_order.get(s.split()[0], 0)  # Term
        ))
    
    def __len__(self) -> int:
        """Number of course records"""
        return len(self.records)
    
    def __repr__(self) -> str:
        return f"Transcript(student={self.student_id}, courses={len(self.records)})"


if __name__ == "__main__":
    # Test the transcript model
    print("Transcript Model Test")
    print("=" * 50)
    
    t = Transcript(student_id="2014567890", student_name="Test Student", program="BBA")
    
    # Add some test records
    t.add_record(CourseRecord("ENG102", 3, "A", "Spring 2023"))
    t.add_record(CourseRecord("MAT116", 0, "B", "Spring 2023"))
    t.add_record(CourseRecord("CSE115", 4, "A-", "Summer 2023"))
    t.add_record(CourseRecord("HIS103", 3, "F", "Summer 2023"))
    t.add_record(CourseRecord("HIS103", 3, "B+", "Spring 2024"))  # Retake
    t.add_record(CourseRecord("PHY107", 3, "C+", "Fall 2023"))
    t.add_record(CourseRecord("CSE173", 3, "W", "Fall 2023"))  # Withdrawn
    
    print(f"Total records: {len(t)}")
    print(f"Unique courses: {len(t.get_unique_courses())}")
    print(f"\nRetaken courses:")
    for code, attempts in t.get_retaken_courses().items():
        print(f"  {code}:")
        for att in attempts:
            print(f"    - {att.grade} ({att.semester})")
        best = t.get_best_attempt(code)
        print(f"    Best: {best.grade}")
    
    print(f"\nSemesters: {t.get_all_semesters()}")
    
    print(f"\nCourse details:")
    for record in t.records[:3]:
        print(f"  {record.course_code}: {record.credits}cr, Grade {record.grade}")
        print(f"    Passing: {record.is_passing}")
        print(f"    Earned: {record.earned_credits}cr")
        print(f"    Quality Points: {record.quality_points}")
        print(f"    Attempted (for GPA): {record.attempted_credits}cr")
