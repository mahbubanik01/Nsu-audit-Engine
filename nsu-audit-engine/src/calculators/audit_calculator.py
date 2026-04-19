"""
Level 3: Graduation Audit & Deficiency Reporter
Complete graduation eligibility check against program requirements
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from models.grade import NSUGradeSystem
from models.transcript import Transcript
from models.program import ProgramRequirements
from models.catalog import CourseCatalog
from calculators.credit_calculator import CreditCalculator, CreditReport
from calculators.gpa_calculator import GPACalculator, GPAReport


@dataclass
class DeficiencyReport:
    """Report of missing requirements"""
    missing_mandatory: List[str] = field(default_factory=list)
    missing_core: List[str] = field(default_factory=list)
    missing_major_core: List[str] = field(default_factory=list)
    unsatisfied_groups: Dict[str, dict] = field(default_factory=dict)
    credit_deficit: float = 0.0
    cgpa_deficit: float = 0.0


@dataclass
class AuditReport:
    """Complete graduation audit report"""
    # Basic info
    student_id: Optional[str]
    student_name: Optional[str]
    program_name: str
    
    # Graduation eligibility
    can_graduate: bool
    deficiencies: DeficiencyReport
    
    # Sub-reports
    credit_report: CreditReport
    gpa_report: GPAReport
    
    # Course tracking
    completed_courses: Set[str]
    retaken_courses: Dict[str, List[dict]]
    extra_courses: List[dict] = field(default_factory=list)
    unrecognized_courses: List[dict] = field(default_factory=list)
    
    def __str__(self) -> str:
        status = "✓ ELIGIBLE TO GRADUATE" if self.can_graduate else "✗ NOT ELIGIBLE TO GRADUATE"
        status_line = f"\n{status}\n"
        
        student_info = ""
        if self.student_id or self.student_name:
            student_info = f"\nStudent: {self.student_name or 'N/A'} ({self.student_id or 'N/A'})\n"
        
        return f"""
{'=' * 70}
GRADUATION AUDIT REPORT
{'=' * 70}{student_info}
Program: {self.program_name}
{status_line}
{self._format_summary()}

{self._format_deficiencies()}

{self._format_retakes()}
{self._format_extras()}
{self._format_unrecognized()}
{'=' * 70}
"""
    
    def _format_summary(self) -> str:
        """Format summary section"""
        lines = ["SUMMARY"]
        lines.append("-" * 70)
        
        # Credits
        credit_check = "✓" if self.deficiencies.credit_deficit == 0 else "✗"
        lines.append(f"{credit_check} Credits: {self.credit_report.total_earned_credits:.1f} earned")
        if self.deficiencies.credit_deficit > 0:
            lines.append(f"   Need {self.deficiencies.credit_deficit:.1f} more credits")
        
        # CGPA
        cgpa_check = "✓" if self.deficiencies.cgpa_deficit == 0 else "✗"
        lines.append(f"{cgpa_check} CGPA: {self.gpa_report.cgpa:.2f}")
        if self.deficiencies.cgpa_deficit > 0:
            lines.append(f"   Need {self.deficiencies.cgpa_deficit:.2f} higher CGPA")
        lines.append(f"   Standing: {self.gpa_report.class_standing}")
        
        # Courses
        total_missing = (len(self.deficiencies.missing_mandatory) +
                        len(self.deficiencies.missing_core) +
                        len(self.deficiencies.missing_major_core))
        course_check = "✓" if total_missing == 0 else "✗"
        lines.append(f"{course_check} Required Courses: {len(self.completed_courses)} completed")
        if total_missing > 0:
            lines.append(f"   Missing {total_missing} required courses")
        
        # Groups
        unsat_count = sum(1 for g in self.deficiencies.unsatisfied_groups.values()
                         if not g['satisfied'])
        group_check = "✓" if unsat_count == 0 else "✗"
        lines.append(f"{group_check} Course Groups: {len(self.deficiencies.unsatisfied_groups) - unsat_count} satisfied")
        if unsat_count > 0:
            lines.append(f"   {unsat_count} groups incomplete")
        
        return "\n".join(lines)
    
    def _format_deficiencies(self) -> str:
        """Format deficiencies section"""
        if self.can_graduate:
            return "No deficiencies - all requirements met!"
        
        lines = ["\nDEFICIENCIES"]
        lines.append("-" * 70)
        
        # Missing courses
        if self.deficiencies.missing_mandatory:
            lines.append("\nMissing Mandatory GED Courses:")
            for course in sorted(self.deficiencies.missing_mandatory):
                lines.append(f"  • {course}")
        
        if self.deficiencies.missing_core:
            lines.append("\nMissing Core Courses:")
            for course in sorted(self.deficiencies.missing_core):
                lines.append(f"  • {course}")
        
        if self.deficiencies.missing_major_core:
            lines.append("\nMissing Major Core Courses:")
            for course in sorted(self.deficiencies.missing_major_core):
                lines.append(f"  • {course}")
        
        # Unsatisfied groups
        unsat_groups = {name: info for name, info in self.deficiencies.unsatisfied_groups.items()
                       if not info['satisfied']}
        if unsat_groups:
            lines.append("\nIncomplete Course Groups:")
            for name, info in unsat_groups.items():
                lines.append(f"  • {name}: {info['completed']}/{info['required']} completed")
                lines.append(f"    Need {info['missing']} more course(s)")
        
        return "\n".join(lines)
    
    def _format_retakes(self) -> str:
        """Format retaken courses section with extreme clarity"""
        if not self.retaken_courses:
            return ""
        
        lines = ["\nRETAKEN COURSES (GPA Impact)"]
        lines.append("-" * 70)
        lines.append("Note: Only the [COUNTED] attempt contributes to your CGPA.")
        
        for course_code in sorted(self.retaken_courses.keys()):
            attempts = self.retaken_courses[course_code]
            lines.append(f"\n{course_code}:")
            
            for i, attempt in enumerate(attempts, 1):
                is_last = (i == len(attempts))
                symbol = "  " if is_last else "→ "
                
                status_marker = ""
                if attempt.get('is_best'):
                    status_marker = " [COUNTED IN CGPA]"
                
                lines.append(f"  {symbol}{attempt['grade']} ({attempt['semester']}){status_marker}")
            
            # Show final status clearly
            final = attempts[-1]
            pass_status = "Passed" if NSUGradeSystem.is_passing_grade(final['grade']) else "Failed"
            lines.append(f"  - Latest Attempt Result: {final['grade']} ({pass_status})")
        
        return "\n".join(lines)

    def _format_extras(self) -> str:
        """Format extra / non-required courses section grouped by category"""
        if not self.extra_courses:
            return ""
        
        lines = ["\nEXTRA / NON-REQUIRED COURSES"]
        lines.append("-" * 70)
        lines.append("These courses contribute to your credits and CGPA but are not")
        lines.append("part of your program's mandatory, core, or group requirements.")
        
        # Group by category
        categories = {}
        for c in self.extra_courses:
            cat = c.get('category', 'Other')
            categories.setdefault(cat, []).append(c)
            
        for cat, courses in sorted(categories.items()):
            lines.append(f"\n[{cat.upper()}]")
            lines.append(f"{'Course':<12} {'Credits':<8} {'Grade':<8} {'Semester'}")
            lines.append("-" * 45)
            for c in sorted(courses, key=lambda x: x['course_code']):
                lines.append(f"{c['course_code']:<12} {c['credits']:<8.1f} {c['grade']:<8} {c['semester']}")
        
        lines.append(f"\nTotal extra courses: {len(self.extra_courses)}")
        total_extra_credits = sum(c['credits'] for c in self.extra_courses)
        lines.append(f"Total extra credits: {total_extra_credits:.1f}")
        return "\n".join(lines)

    def _format_unrecognized(self) -> str:
        """Format unrecognized / invalid courses section"""
        if not self.unrecognized_courses:
            return ""
        
        lines = ["\nUNRECOGNIZED / INVALID COURSES"]
        lines.append("-" * 70)
        lines.append("!!! WARNING: These course codes do not follow standard NSU")
        lines.append("conventions or use unknown prefixes. Please check manually.")
        lines.append("")
        lines.append(f"{'Course':<12} {'Credits':<8} {'Grade':<8} {'Semester'}")
        lines.append("-" * 50)
        for c in sorted(self.unrecognized_courses, key=lambda x: x['course_code']):
            lines.append(f"{c['course_code']:<12} {c['credits']:<8.1f} {c['grade']:<8} {c['semester']}")
        lines.append(f"\nTotal unrecognized: {len(self.unrecognized_courses)}")
        return "\n".join(lines)


class AuditCalculator:
    """
    Level 3: Graduation Audit Engine
    
    Performs complete graduation check:
    1. Verify credit requirements
    2. Verify CGPA requirements
    3. Check all mandatory courses
    4. Check course group requirements
    5. Handle retakes properly
    6. Generate deficiency report
    """
    
    @staticmethod
    def perform_audit(transcript: Transcript,
                     program: ProgramRequirements,
                     waived_courses: Optional[Set[str]] = None) -> AuditReport:
        """
        Perform complete graduation audit.
        
        Args:
            transcript: Student transcript
            program: Program requirements
            waived_courses: Set of waived courses
            
        Returns:
            Complete audit report
        """
        if waived_courses is None:
            waived_courses = set()
        
        # 1. First, identify and separate unrecognized courses based on catalog
        # Standard undergrad is 100-499, HIS5010 is clearly suspicious
        passed_attempts = {}
        for r in transcript.records:
            if r.is_passing and r.course_code not in waived_courses:
                # Keep the best attempt for each course
                best = transcript.get_best_attempt(r.course_code)
                passed_attempts[r.course_code] = best

        unrecognized_codes = {
            code for code in passed_attempts 
            if not CourseCatalog.is_valid_nsu_course(code)
        }
        
        # 2. Run sub-calculations using ONLY valid courses for Audit accuracy
        # Create a filtered transcript for calculators to ensure anomalies don't count
        from models.transcript import CourseRecord # Local import if needed
        legit_records = [r for r in transcript.records if r.course_code not in unrecognized_codes]
        filtered_transcript = Transcript(
            student_id=transcript.student_id,
            student_name=transcript.student_name,
            program=transcript.program,
            records=legit_records
        )
        
        gpa_report = GPACalculator.calculate_cgpa(filtered_transcript, waived_courses)
        
        # 3. Identify how valid courses are used
        recognized = program.get_all_recognized_courses()
        completed_courses = set(passed_attempts.keys())
        
        # Courses satisfying specific requirements
        used_for_program = set()
        for code in completed_courses:
            if code in recognized:
                used_for_program.add(code)
        
        # Courses not in specific requirements
        unused = sorted(
            [code for code in completed_courses if code not in used_for_program],
            key=lambda x: passed_attempts[x].semester, # Prefer earlier/certain order
            reverse=True
        )
        
        # Categorize unused into Free Electives, Extras, and Unrecognized
        extra_courses = []
        unrecognized_courses = []
        
        # In a general audit, all VALID NSU courses contribute to the degree total
        # but we still categorize them for clarity.
        for code in unused:
            best = passed_attempts[code]
            course_data = {
                'course_code': code,
                'credits': best.credits,
                'grade': best.grade,
                'semester': best.semester,
            }
            
            if not CourseCatalog.is_valid_nsu_course(code):
                unrecognized_courses.append(course_data)
            else:
                course_data['category'] = CourseCatalog.get_department_category(code)
                # Count valid extras toward program credits for general audit
                extra_courses.append(course_data)
                used_for_program.add(code)
        
        # 4. Calculate graduation-specific credits (Valid courses only)
        program_credits = sum(passed_attempts[c].credits for c in used_for_program)
        
        # 5. Check requirements against program_credits
        deficiencies = DeficiencyReport()
        if program_credits < program.total_credits_required:
            deficiencies.credit_deficit = program.total_credits_required - program_credits
        
        # 6. Check CGPA requirement (usually on all passed courses, but can be adjusted)
        if gpa_report.cgpa < program.minimum_cgpa:
            deficiencies.cgpa_deficit = program.minimum_cgpa - gpa_report.cgpa
        
        # 7. Check mandatory courses
        missing = program.check_mandatory_completion(used_for_program)
        deficiencies.missing_mandatory = [c for c in missing['mandatory'] if c not in waived_courses]
        deficiencies.missing_core = [c for c in missing['core'] if c not in waived_courses]
        deficiencies.missing_major_core = [c for c in missing['major_core'] if c not in waived_courses]
        
        # 8. Check course groups
        deficiencies.unsatisfied_groups = program.check_course_groups(used_for_program)
        
        # 9. Determine if can graduate
        can_graduate = (
            deficiencies.credit_deficit <= 0 and
            deficiencies.cgpa_deficit <= 0 and
            not deficiencies.missing_mandatory and
            not deficiencies.missing_core and
            not deficiencies.missing_major_core and
            all(g['satisfied'] for g in deficiencies.unsatisfied_groups.values())
        )
        
        # Wrap everything in a special credit report for the audit
        audit_credit_report = CreditReport(
            total_earned_credits=program_credits, # ONLY program-contributing credits
            total_attempted_credits=sum(a.credits for a in transcript.records),
            courses_passed=len([c for c in used_for_program if passed_attempts[c].credits > 0]),
            courses_failed=len([r for r in transcript.records if r.grade == 'F']),
            courses_withdrawn=len([r for r in transcript.records if r.grade == 'W']),
            zero_credit_courses=len([c for c in used_for_program if passed_attempts[c].credits == 0]),
            retaken_courses=len(transcript.get_retaken_courses()),
            course_details=[
                {
                    'course_code': c, 
                    'credits': passed_attempts[c].credits, 
                    'grade': passed_attempts[c].grade, 
                    'semester': passed_attempts[c].semester,
                    'earned': passed_attempts[c].credits
                } for c in sorted(used_for_program)
            ]
        )
        
        # Track retakes
        term_order = {'Spring': 1, 'Summer': 2, 'Fall': 3}
        retaken = {}
        for course_code, attempts in transcript.get_retaken_courses().items():
            best_attempt = transcript.get_best_attempt(course_code)
            sorted_attempts = sorted(
                attempts, 
                key=lambda x: (int(x.semester.split()[1]), term_order.get(x.semester.split()[0], 0))
            )
            retaken[course_code] = [
                {
                    'grade': att.grade,
                    'semester': att.semester,
                    'credits': att.credits,
                    'is_best': att == best_attempt
                } for att in sorted_attempts
            ]
        
        return AuditReport(
            student_id=transcript.student_id,
            student_name=transcript.student_name,
            program_name=program.program_name,
            can_graduate=can_graduate,
            deficiencies=deficiencies,
            credit_report=audit_credit_report,
            gpa_report=gpa_report,
            completed_courses=used_for_program,
            retaken_courses=retaken,
            extra_courses=extra_courses,
            unrecognized_courses=unrecognized_courses
        )
    
    @staticmethod
    def generate_detailed_report(audit: AuditReport) -> str:
        """Generate comprehensive detailed report with course-by-course justification"""
        lines = [str(audit)]
        
        # Add Graduation Requirement Justification
        lines.append("\nGRADUATION REQUIREMENT JUSTIFICATION")
        lines.append("=" * 80)
        lines.append(f"{'Course':<12} {'Credits':<8} {'Grade Used':<12} {'Semester'}")
        lines.append("-" * 80)
        
        # We need to find which attempt was used for each passed course
        # This information is inside the CreditReport.course_details
        for detail in sorted(audit.credit_report.course_details, key=lambda x: x['course_code']):
            if detail['earned'] > 0:
                lines.append(
                    f"{detail['course_code']:<12} "
                    f"{detail['credits']:<8.1f} "
                    f"{detail['grade']:<12} "
                    f"{detail['semester']}"
                )
        lines.append("=" * 80)
        
        # Add semester GPA breakdown (Now shows Term GPAs)
        from calculators.gpa_calculator import GPACalculator
        lines.append("\n" + GPACalculator.get_semester_breakdown(audit.gpa_report))
        lines.append("Note: Term GPAs reflect performance in that semester. CGPA uses best attempts.")
        
        return "\n".join(lines)


if __name__ == "__main__":
    from parsers.csv_parser import TranscriptParser
    from models.program import ProgramFactory
    import tempfile
    import os
    
    print("LEVEL 3: Audit Calculator Test")
    print("=" * 70)
    
    # Create test transcript
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        test_file = f.name
    
    try:
        TranscriptParser.create_sample_csv(test_file, include_edge_cases=True)
        transcript = TranscriptParser.parse_csv(
            test_file,
            student_id="2014567890",
            student_name="Test Student",
            program="BBA"
        )
        
        # Create BBA program
        program = ProgramFactory.create_bba_program()
        
        # Perform audit
        audit = AuditCalculator.perform_audit(transcript, program)
        
        # Print reports
        print(audit)
        
        print("\n\nDETAILED REPORT:")
        print(AuditCalculator.generate_detailed_report(audit))
        
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
