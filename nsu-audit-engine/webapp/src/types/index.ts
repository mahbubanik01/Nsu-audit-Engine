export interface UserProfile {
  email: string;
  name?: string;
  picture?: string;
  domain?: string;
  role?: string;
}

export interface AuthContextType {
  token: string | null;
  user: UserProfile | null;
  login: (token: string, user: UserProfile) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

export interface AuditSummary {
  is_eligible: boolean;
  cgpa: number;
  credits_earned: number;
  credits_required: number;
}

export interface AuditDeficiencies {
  missing_mandatory: string[];
  missing_core: string[];
  missing_major_core: string[];
  unsatisfied_groups: Record<string, any>;
  credit_deficit: number;
  cgpa_deficit: number;
}

export interface CourseAttempt {
  grade: string;
  semester: string;
  credits?: number;
}

export interface RetakenCourse {
  course_code: string;
  best_attempt: CourseAttempt;
  all_attempts: CourseAttempt[];
}

export interface SemesterCourse {
  code: string;
  grade: string;
  credits: number;
}

export interface SemesterBreakdown {
  semester: string;
  gpa: number;
  courses: SemesterCourse[];
}

export interface ExtraCourse {
  course_code: string;
  credits: number;
  grade: string;
  semester: string;
  category?: string;
}

export interface AuditResponse {
  student: {
    id: string;
    name: string;
  };
  program: string;
  summary: AuditSummary;
  deficiencies: AuditDeficiencies;
  retaken_courses: RetakenCourse[];
  semester_breakdown: SemesterBreakdown[];
  extra_courses: ExtraCourse[];
  unrecognized_courses: ExtraCourse[];
  raw_records: number;
  scan_timestamp?: string;
}
