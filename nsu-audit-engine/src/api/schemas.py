from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class OTPRequest(BaseModel):
    email: str

class OTPVerify(BaseModel):
    email: str
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

class GoogleAuthVerify(BaseModel):
    credential: str
    client_id: str

class AuditResponse(BaseModel):
    student: Dict[str, Any]
    program: str
    summary: Dict[str, Any]
    deficiencies: Dict[str, Any]
    retaken_courses: List[Dict[str, Any]]
    semester_breakdown: List[Dict[str, Any]]
    raw_records: int
