"""
NSU Grade System Model
Implements the official NSU grading scale and rules
"""

from typing import Optional
from dataclasses import dataclass
from enum import Enum


class GradeType(Enum):
    """Grade types in NSU system"""
    LETTER = "letter"  # A, B+, C-, etc.
    FAIL = "fail"  # F
    WITHDRAW = "withdraw"  # W
    INCOMPLETE = "incomplete"  # I


@dataclass
class Grade:
    """Represents a single grade with its properties"""
    letter: str
    points: float
    counts_for_gpa: bool
    counts_for_credits: bool
    grade_type: GradeType


class NSUGradeSystem:
    """
    Official NSU Grading System
    Source: https://www.northsouth.edu/academic/grading-policy.html
    """
    
    # Official NSU Grade Scale
    GRADE_SCALE = {
        'A': Grade('A', 4.0, True, True, GradeType.LETTER),
        'A-': Grade('A-', 3.7, True, True, GradeType.LETTER),
        'B+': Grade('B+', 3.3, True, True, GradeType.LETTER),
        'B': Grade('B', 3.0, True, True, GradeType.LETTER),
        'B-': Grade('B-', 2.7, True, True, GradeType.LETTER),
        'C+': Grade('C+', 2.3, True, True, GradeType.LETTER),
        'C': Grade('C', 2.0, True, True, GradeType.LETTER),
        'C-': Grade('C-', 1.7, True, True, GradeType.LETTER),
        'D+': Grade('D+', 1.3, True, True, GradeType.LETTER),
        'D': Grade('D', 1.0, True, True, GradeType.LETTER),
        'F': Grade('F', 0.0, True, False, GradeType.FAIL),
        'W': Grade('W', 0.0, False, False, GradeType.WITHDRAW),
        'I': Grade('I', 0.0, False, False, GradeType.INCOMPLETE),
    }
    
    @classmethod
    def get_grade(cls, letter: str) -> Optional[Grade]:
        """Get grade object for a letter grade"""
        return cls.GRADE_SCALE.get(letter.upper())
    
    @classmethod
    def is_valid_grade(cls, letter: str) -> bool:
        """Check if grade is valid in NSU system"""
        return letter.upper() in cls.GRADE_SCALE
    
    @classmethod
    def is_passing_grade(cls, letter: str) -> bool:
        """Check if grade earns credits"""
        grade = cls.get_grade(letter)
        return grade is not None and grade.counts_for_credits
    
    @classmethod
    def get_grade_point(cls, letter: str) -> float:
        """Get numerical grade point for a letter"""
        grade = cls.get_grade(letter)
        return grade.points if grade else 0.0
    
    @classmethod
    def counts_in_gpa(cls, letter: str) -> bool:
        """Check if grade counts in GPA calculation"""
        grade = cls.get_grade(letter)
        return grade is not None and grade.counts_for_gpa
    
    @classmethod
    def compare_grades(cls, grade1: str, grade2: str) -> str:
        """
        Compare two grades and return the better one.
        Used for retake logic.
        """
        g1 = cls.get_grade(grade1)
        g2 = cls.get_grade(grade2)
        
        if g1 is None:
            return grade2
        if g2 is None:
            return grade1
        
        # Compare by points
        return grade1 if g1.points >= g2.points else grade2
    
    @classmethod
    def get_class_standing(cls, cgpa: float) -> str:
        """
        Determine class standing based on CGPA
        NSU Classification:
        - 3.00+ = First Class
        - 2.50-2.99 = Second Class
        - 2.00-2.49 = Third Class
        - <2.00 = Academic Probation
        """
        if cgpa >= 3.00:
            return "First Class"
        elif cgpa >= 2.50:
            return "Second Class"
        elif cgpa >= 2.00:
            return "Third Class"
        else:
            return "Academic Probation"
    
    @classmethod
    def get_honor_status(cls, cgpa: float) -> Optional[str]:
        """Get graduation honors if applicable"""
        if cgpa >= 3.90:
            return "Summa Cum Laude"
        elif cgpa >= 3.80:
            return "Magna Cum Laude"
        elif cgpa >= 3.50:
            return "Cum Laude"
        return None


if __name__ == "__main__":
    # Test the grade system
    print("NSU Grade System Test")
    print("=" * 50)
    
    test_grades = ['A', 'B+', 'C-', 'F', 'W']
    for g in test_grades:
        grade = NSUGradeSystem.get_grade(g)
        if grade:
            print(f"{g}: {grade.points} points, "
                  f"Counts GPA: {grade.counts_for_gpa}, "
                  f"Earns Credits: {grade.counts_for_credits}")
    
    print("\nGrade Comparison (Retake Logic):")
    print(f"F vs B: Best = {NSUGradeSystem.compare_grades('F', 'B')}")
    print(f"A- vs A: Best = {NSUGradeSystem.compare_grades('A-', 'A')}")
    
    print("\nClass Standing:")
    for cgpa in [3.85, 2.75, 2.25, 1.95]:
        print(f"CGPA {cgpa}: {NSUGradeSystem.get_class_standing(cgpa)}")
