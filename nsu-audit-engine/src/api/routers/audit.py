import os
import tempfile
import json
from dataclasses import asdict
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from typing import Dict, Any

from api.schemas import AuditResponse
from api.dependencies import get_current_user
from parsers.document_router import DocumentRouter
from calculators.audit_calculator import AuditCalculator
from models.program import ProgramFactory
import datetime

USER_AUDITS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "user_audits.json"
)

def _save_audit(email: str, audit_data: dict):
    audits = {}
    if os.path.exists(USER_AUDITS_FILE):
        try:
            with open(USER_AUDITS_FILE, "r") as f:
                audits = json.load(f)
        except Exception:
            pass
            
    if email not in audits:
        audits[email] = []
        
    # Add timestamp
    audit_data["scan_timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    audits[email].append(audit_data)
    
    try:
        os.makedirs(os.path.dirname(USER_AUDITS_FILE), exist_ok=True)
        with open(USER_AUDITS_FILE, "w") as f:
            json.dump(audits, f, indent=2)
    except Exception:
        pass # Ignore file write errors on Vercel

router = APIRouter()

@router.get("/supported-formats")
async def get_supported_formats():
    """Returns a list of supported document extensions."""
    from parsers.document_router import SUPPORTED_EXTENSIONS
    return {"supported_extensions": list(SUPPORTED_EXTENSIONS)}

@router.post("/run", response_model=AuditResponse)
async def run_audit(
    file: UploadFile = File(...),
    program_type: str = Form("BBA"),
    email: str = Depends(get_current_user)
):
    """
    Upload a transcript file, parse it, and return a full graduation audit report.
    This route is protected and requires a valid JWT token.
    """
    # Create a temporary file to save the upload
    _, ext = os.path.splitext(file.filename)
    if not ext:
        ext = ".csv"
        
    ext = ext.lower()
    from parsers.document_router import SUPPORTED_EXTENSIONS
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {ext}. Supported formats: {', '.join(SUPPORTED_EXTENSIONS)}"
        )

    # We use a NamedTemporaryFile so we can pass the path to the DocumentRouter
    fd, temp_path = tempfile.mkstemp(suffix=ext)
    os.close(fd)
    
    try:
        # Write the uploaded bytes to the temp file
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # 1. Parse Document
        try:
            print(f"[API] Parsing document: {file.filename} (Size: {len(content)} bytes)")
            transcript = DocumentRouter.parse(temp_path, program=program_type.upper())
            print(f"[API] Successfully parsed {len(transcript)} course records.")
        except Exception as e:
            print(f"[API] Parsing failed: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")
            
        if len(transcript) == 0:
            print(f"[API] No records found in document.")
            raise HTTPException(status_code=400, detail="No valid course records found in document.")

        # 2. Run Audit
        try:
            program_enum = program_type.upper()
            print(f"[API] Running audit for program: {program_enum}")
            if program_enum == "BBA":
                program_obj = ProgramFactory.create_bba_program()
            elif program_enum == "CSE":
                program_obj = ProgramFactory.create_cse_program()
            else:
                raise ValueError(f"Unknown program type: {program_enum}")
                
            report = AuditCalculator.perform_audit(transcript, program_obj)
            print(f"[API] Audit complete. Credits earned: {report.total_credits_earned}")
        except Exception as e:
            print(f"[API] Audit calculation failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to calculate audit: {str(e)}")

        # 3. Format Response
        # Convert dataclass to dict to easily serialize with FastAPI
        report_dict = asdict(report)
        
        # Structure the response
        response = {
            "student": {
                "id": report_dict.get("student_id") or "Unknown",
                "name": report_dict.get("student_name") or "Unknown"
            },
            "program": report_dict.get("program") or program_type.upper(),
            "summary": {
                "is_eligible": report_dict.get("is_eligible", False),
                "cgpa": report_dict.get("cgpa", 0.0),
                "credits_earned": report_dict.get("total_credits_earned", 0.0),
                "credits_required": report_dict.get("total_credits_required", 124.0)
            },
            "deficiencies": report_dict.get("deficiencies", {}),
            "retaken_courses": [],
            "semester_breakdown": [],
            "extra_courses": [],
            "unrecognized_courses": [],
            "raw_records": len(transcript)
        }
        
        # Add retaken courses info nicely
        retaken = transcript.get_retaken_courses()
        for course_code in retaken:
            attempts = retaken[course_code]
            best = transcript.get_best_attempt(course_code)
            
            response["retaken_courses"].append({
                "course_code": course_code,
                "best_attempt": {"grade": best.grade, "semester": best.semester, "credits": best.credits},
                "all_attempts": [{"grade": a.grade, "semester": a.semester} for a in attempts]
            })
            
        # Add semester breakdown
        semesters = {}
        for r in transcript.records:
            semesters.setdefault(r.semester, []).append(r)
            
        for sem, records in semesters.items():
            sem_gpa = report_dict.get("gpa_report", {}).get("semester_gpas", {}).get(sem, 0.0)
            response["semester_breakdown"].append({
                "semester": sem,
                "gpa": sem_gpa,
                "courses": [{"code": r.course_code, "grade": r.grade, "credits": r.credits} for r in records]
            })

        # Add extra / non-required courses
        response["extra_courses"] = report_dict.get("extra_courses", [])
        response["unrecognized_courses"] = report_dict.get("unrecognized_courses", [])

        # Save the audit to history
        _save_audit(email, response)

        return response
        
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/history")
async def get_audit_history(email: str = Depends(get_current_user)):
    """Retrieve all previously saved audits for the current user."""
    audits = {}
    if os.path.exists(USER_AUDITS_FILE):
        try:
            with open(USER_AUDITS_FILE, "r") as f:
                audits = json.load(f)
        except Exception:
            pass
    return {"audits": list(reversed(audits.get(email, [])))}
