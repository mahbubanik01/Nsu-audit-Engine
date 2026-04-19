"""
Program Requirements Model
Represents degree program requirements and rules
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class CourseGroup:
    """Group of courses with selection rules"""
    name: str
    courses: List[str]
    required_count: int  # How many from this group are required
    credits_per_course: int = 3  # Default credits per course
    
    def is_satisfied_by(self, completed_courses: Set[str]) -> tuple[bool, int]:
        """
        Check if requirements are satisfied.
        Returns: (is_satisfied, count_completed)
        """
        completed_in_group = [c for c in self.courses if c in completed_courses]
        count = len(completed_in_group)
        return (count >= self.required_count, count)
    
    def get_missing_count(self, completed_courses: Set[str]) -> int:
        """Get number of courses still needed from this group"""
        _, completed = self.is_satisfied_by(completed_courses)
        return max(0, self.required_count - completed)
    
    def __repr__(self) -> str:
        return f"CourseGroup({self.name}, {self.required_count}/{len(self.courses)} required)"


@dataclass
class ProgramRequirements:
    """Complete program degree requirements"""
    program_name: str
    degree: str
    total_credits_required: int
    minimum_cgpa: float = 2.0
    
    # Course requirements
    mandatory_courses: List[str] = field(default_factory=list)
    core_courses: List[str] = field(default_factory=list)
    course_groups: List[CourseGroup] = field(default_factory=list)
    
    # Major requirements
    major_core_courses: List[str] = field(default_factory=list)
    major_elective_count: int = 0
    major_elective_options: List[str] = field(default_factory=list)
    
    # Elective requirements
    free_elective_count: int = 0
    
    # Special rules
    waivable_courses: List[str] = field(default_factory=list)
    
    def get_all_mandatory_courses(self) -> List[str]:
        """Get all courses that MUST be completed"""
        mandatory = set()
        mandatory.update(self.mandatory_courses)
        mandatory.update(self.core_courses)
        mandatory.update(self.major_core_courses)
        return list(mandatory)
    
    def check_mandatory_completion(self, completed_courses: Set[str]) -> Dict[str, List[str]]:
        """
        Check which mandatory courses are missing.
        Returns dict categorizing missing courses.
        """
        missing = {
            'mandatory': [],
            'core': [],
            'major_core': []
        }
        
        for course in self.mandatory_courses:
            if course not in completed_courses:
                missing['mandatory'].append(course)
        
        for course in self.core_courses:
            if course not in completed_courses:
                missing['core'].append(course)
        
        for course in self.major_core_courses:
            if course not in completed_courses:
                missing['major_core'].append(course)
        
        return missing
    
    def check_course_groups(self, completed_courses: Set[str]) -> Dict[str, dict]:
        """
        Check status of all course groups.
        Returns dict with group status.
        """
        group_status = {}
        for group in self.course_groups:
            satisfied, completed_count = group.is_satisfied_by(completed_courses)
            missing_count = group.get_missing_count(completed_courses)
            group_status[group.name] = {
                'satisfied': satisfied,
                'completed': completed_count,
                'required': group.required_count,
                'missing': missing_count
            }
        return group_status
    
    def get_all_recognized_courses(self) -> Set[str]:
        """
        Get every course code the program recognizes — mandatory, core, major,
        group options, elective options, and waivable courses.
        Used to identify 'extra' courses the student took that aren't required.
        """
        recognized = set()
        recognized.update(self.mandatory_courses)
        recognized.update(self.core_courses)
        recognized.update(self.major_core_courses)
        recognized.update(self.major_elective_options)
        recognized.update(self.waivable_courses)
        for group in self.course_groups:
            recognized.update(group.courses)
        return recognized

    def is_course_waivable(self, course_code: str) -> bool:
        """Check if a course can be waived"""
        return course_code in self.waivable_courses
    
    def __repr__(self) -> str:
        return f"ProgramRequirements({self.program_name}, {self.total_credits_required} credits)"


class ProgramFactory:
    """Factory to create program requirements from structured data"""
    
    @staticmethod
    def create_bba_program() -> ProgramRequirements:
        """
        Create BBA program requirements based on NSU 143+ curriculum.
        Source: NSU BBA Curriculum Document
        """
        program = ProgramRequirements(
            program_name="Business Administration",
            degree="Bachelor of Business Administration (BBA)",
            total_credits_required=126,  # Excluding non-credit internship
            minimum_cgpa=2.0
        )
        
        # Mandatory/Waivable courses
        program.waivable_courses = ["ENG102", "BUS112"]
        program.mandatory_courses = []  # These are waivable, not mandatory
        
        # School Core (21 credits)
        program.core_courses = [
            "ECO101", "ECO104", "MIS107", "BUS251",
            "BUS172", "BUS173", "BUS135"
        ]
        
        # BBA Core (36 credits)
        bba_core = [
            "ACT201", "ACT202", "FIN254", "LAW200",
            "INB372", "MKT202", "MIS207", "MGT212",
            "MGT351", "MGT314", "MGT368", "MGT489"
        ]
        program.core_courses.extend(bba_core)
        
        # GED Courses (36 credits) - with choice groups
        ged_mandatory = ["ENG103", "ENG105", "PHI401", "HIS103"]
        program.core_courses.extend(ged_mandatory)
        
        # GED Choice Groups
        program.course_groups.append(
            CourseGroup(
                name="History Elective",
                courses=["HIS101", "HIS102", "HIS202", "HIS205"],
                required_count=1
            )
        )
        
        program.course_groups.append(
            CourseGroup(
                name="Political Science/Public Admin",
                courses=["POL101", "POL104", "PAD201"],
                required_count=1
            )
        )
        
        program.course_groups.append(
            CourseGroup(
                name="Social Science Elective",
                courses=["SOC101", "GEO205", "ANT101"],
                required_count=1
            )
        )
        
        program.course_groups.append(
            CourseGroup(
                name="Basic Sciences",
                courses=["BIO103", "ENV107", "PBH101", "PSY101", "PHY107", "CHE101"],
                required_count=3  # Choose 3
            )
        )
        
        # Major requirements (18 credits total: 4 core + 2 electives)
        # This would be customized based on student's chosen major
        # For now, we'll leave it flexible
        program.major_core_courses = []  # To be set based on major
        program.major_elective_count = 2
        program.major_elective_options = []  # To be set based on major
        
        # Free electives (9 credits = 3 courses)
        program.free_elective_count = 3
        
        return program
    
    @staticmethod
    def create_cse_program() -> ProgramRequirements:
        """
        Create CSE program requirements.
        This is a simplified version - would need full NSU CSE curriculum.
        """
        program = ProgramRequirements(
            program_name="Computer Science & Engineering",
            degree="Bachelor of Science (BS)",
            total_credits_required=130,
            minimum_cgpa=2.0
        )
        
        # Mandatory GED
        program.core_courses = ["ENG102", "ENG103", "HIS103", "PHI101"]
        
        # Core Math
        math_core = ["MAT116", "MAT120", "MAT250", "MAT350", "MAT361"]
        program.core_courses.extend(math_core)
        
        # Major Core
        cse_core = [
            "CSE115", "CSE173", "CSE215", "CSE225", "CSE231",
            "CSE311", "CSE323", "CSE327", "CSE331", "CSE332", "CSE425"
        ]
        program.core_courses.extend(cse_core)
        
        return program


if __name__ == "__main__":
    # Test the program model
    print("Program Requirements Test")
    print("=" * 50)
    
    bba = ProgramFactory.create_bba_program()
    print(f"\n{bba.program_name}")
    print(f"Total Credits: {bba.total_credits_required}")
    print(f"Core Courses: {len(bba.core_courses)}")
    print(f"Course Groups: {len(bba.course_groups)}")
    print(f"Waivable: {bba.waivable_courses}")
    
    print("\nCourse Groups:")
    for group in bba.course_groups:
        print(f"  {group.name}: Choose {group.required_count} from {len(group.courses)}")
    
    # Test with sample completion
    completed = {
        "ENG102", "ENG103", "ENG105", "PHI401", "HIS103", "HIS101",
        "POL101", "SOC101", "BIO103", "PSY101", "PHY107",
        "ECO101", "ECO104", "MIS107", "BUS251", "BUS172", "BUS173", "BUS135",
        "ACT201", "ACT202", "FIN254", "LAW200", "MKT202"
    }
    
    print("\n\nChecking completion with sample courses:")
    missing = bba.check_mandatory_completion(completed)
    print(f"Missing Core: {len(missing['core'])} courses")
    if missing['core']:
        print(f"  {missing['core'][:5]}...")  # Show first 5
    
    group_status = bba.check_course_groups(completed)
    print("\nCourse Group Status:")
    for name, status in group_status.items():
        check = "✓" if status['satisfied'] else "✗"
        print(f"  {check} {name}: {status['completed']}/{status['required']}")
