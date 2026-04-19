"""
NSU Course Catalog
Provides validation and metadata for courses across North South University.
Used to differentiate between program-specific courses, valid electives, and unrecognized codes.
"""

from typing import Set, List
import re


class CourseCatalog:
    """
    Catalog of known NSU course prefixes and validation rules.
    """
    
    # Common NSU Department Prefixes
    VALID_PREFIXES = {
        "ACT", "ANT", "BIO", "BUS", "CHE", "CSE", "ECO", "EEE", 
        "ENG", "ENV", "FIN", "GEO", "HIS", "HRM", "INB", "LAW", 
        "MAT", "MGT", "MIS", "MKT", "PAD", "PBH", "PHI", "PHY", 
        "POL", "PSY", "SOC", "BEN", "LBS", "OPM", "STR"
    }

    # Mapping prefixes to categories
    PREFIX_TO_CATEGORY = {
        # Business & Economics
        "ACT": "Business & Economics", "BUS": "Business & Economics", "ECO": "Business & Economics",
        "FIN": "Business & Economics", "HRM": "Business & Economics", "INB": "Business & Economics",
        "MGT": "Business & Economics", "MIS": "Business & Economics", "MKT": "Business & Economics",
        "OPM": "Business & Economics", "STR": "Business & Economics", "LBS": "Business & Economics",
        
        # Engineering & Computing
        "CSE": "Engineering & Computing", "EEE": "Engineering & Computing", 
        "MAT": "Engineering & Computing", "PHY": "Engineering & Computing",
        
        # Humanities & Arts
        "BEN": "Humanities & Arts", "ENG": "Humanities & Arts", "HIS": "Humanities & Arts", 
        "PHI": "Humanities & Arts", "GEO": "Humanities & Arts",
        
        # Social Sciences
        "ANT": "Social Sciences", "SOC": "Social Sciences", "PSY": "Social Sciences", 
        "POL": "Social Sciences", "PAD": "Social Sciences", "LAW": "Social Sciences",
        
        # Life & Pure Sciences
        "BIO": "Pure & Life Sciences", "CHE": "Pure & Life Sciences", 
        "ENV": "Pure & Life Sciences", "PBH": "Pure & Life Sciences"
    }

    # Course code regex: 2-4 letters followed by 3-4 digits, optional letter at end
    COURSE_RE = re.compile(r"^([A-Z]{2,4})(\d{3,4})[A-Z]?$")

    @classmethod
    def get_department_category(cls, course_code: str) -> str:
        """
        Get the department/area category for a course code.
        Example: CSE226 -> Engineering & Computing
        """
        match = cls.COURSE_RE.match(course_code.upper().strip())
        if not match:
            return "Other"
            
        prefix = match.group(1)
        return cls.PREFIX_TO_CATEGORY.get(prefix, "Other")

    @classmethod
    def is_valid_nsu_course(cls, course_code: str) -> bool:
        """
        Check if a course code follows NSU naming conventions and uses a known prefix.
        Example: CSE115 (Valid), HIS5010 (Invalid - too many digits for standard undergrad/general)
        """
        match = cls.COURSE_RE.match(course_code.upper().strip())
        if not match:
            return False
            
        prefix, digits = match.groups()
        
        # 1. Check prefix
        if prefix not in cls.VALID_PREFIXES:
            return False
            
        # 2. Check level (Standard undergrad is 100-499, some 500 for honors/grad)
        # HIS5010 is clearly suspicious for an undergraduate audit
        level = int(digits)
        if level > 699: # Allowing some buffer for grad courses but 5010 is way off
            return False
            
        if len(digits) > 3 and level > 699:
            return False
            
        return True

    @classmethod
    def get_all_known_courses(cls) -> Set[str]:
        """
        Internal helper to get a set of courses already defined in the system.
        """
        # This could be expanded to load from a JSON catalog
        return set()
