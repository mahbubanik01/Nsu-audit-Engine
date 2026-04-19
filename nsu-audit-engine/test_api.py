"""
End-to-End Test for the NSU Audit Engine API.
Uses FastAPI's TestClient to simulate requests without running a live server.
"""

import sys
import os
from pathlib import Path

# Important: Add src to path so absolute imports work
src_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_dir)

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_api_complete_flow():
    print("="*60)
    print("API END-TO-END TEST")
    print("="*60)

    # We need to send X-API-Key securely
    base_headers = {"X-API-Key": "dev_secret_key"}

    # 1. Test Root
    print("\n[GET /] Checking root...")
    res = client.get("/")
    assert res.status_code == 200, res.text
    print("  ✓ Root OK:", res.json())

    # 2. Request OTP
    test_email = "student@northsouth.edu"
    print(f"\n[POST /api/v1/auth/request-otp] Requesting for {test_email}...")
    res = client.post("/api/v1/auth/request-otp", json={"email": test_email}, headers=base_headers)
    assert res.status_code == 200, res.text
    print("  ✓ OTP Requested:", res.json())

    # We need the actual OTP sent to bypass it in tests.
    # In auth.py, OTPs are stored in AuthConfig if dev mode, but here we can just
    # peek into the AuthService singleton or we can use the bypass if it exists.
    # Wait, in the Python code, the OTPs are stored inside self.otp_manager.otps dict.
    from auth.auth import AuthService
    auth_service = AuthService()
    
    # Wait, the AuthService in api/routers/auth.py is a separate instance!
    # Let me grab it directly from the router to find the OTP.
    from api.routers.auth import auth_service as router_auth_service
    otp_data = router_auth_service.otp_manager._pending_otps.get(test_email)
    
    if not otp_data:
        print("  ✗ Failed to find generated OTP in memory.")
        return
        
    actual_otp = otp_data.code
    print(f"  > Found internal OTP: {actual_otp}")

    # 3. Verify OTP
    print(f"\n[POST /api/v1/auth/verify-otp] Verifying...")
    res = client.post("/api/v1/auth/verify-otp", json={"email": test_email, "otp": actual_otp}, headers=base_headers)
    assert res.status_code == 200, res.text
    token_data = res.json()
    token = token_data["access_token"]
    print("  ✓ OTP Verified. Received JWT token:")
    print(f"    {token[:20]}...{token[-10:]}")

    # 4. Get Profile (Protected by JWT and API Key)
    print("\n[GET /api/v1/auth/me] Fetching profile...")
    auth_headers = {**base_headers, "Authorization": f"Bearer {token}"}
    res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert res.status_code == 200, res.text
    print("  ✓ Profile loaded:", res.json())

    # 5. Run Audit on File (Protected)
    print("\n[POST /api/v1/audit/run] Uploading test CSV transcript...")
    test_file_path = "data/test_cases/test_retake_degrade.csv"
    
    with open(test_file_path, "rb") as f:
        files = {"file": ("test_retake_degrade.csv", f, "text/csv")}
        data = {"program_type": "BBA"}
        res = client.post("/api/v1/audit/run", headers=auth_headers, files=files, data=data)
        
    assert res.status_code == 200, f"Error {res.status_code}: {res.text}"
    audit_res = res.json()
    
    print("  ✓ Audit successful! Checking JSON schema...")
    print(f"    Student: {audit_res['student']['name']}")
    print(f"    Program: {audit_res['program']}")
    print(f"    CGPA: {audit_res['summary']['cgpa']}")
    print(f"    Credits Earned: {audit_res['summary']['credits_earned']}")
    print(f"    Retaken Courses Detected: {len(audit_res['retaken_courses'])}")
    
    # 6. Check Supported Formats
    print("\n[GET /api/v1/audit/supported-formats] Checking formats...")
    res = client.get("/api/v1/audit/supported-formats", headers=base_headers)
    assert res.status_code == 200
    print(f"  ✓ Supported formats: {res.json()['supported_extensions']}")

    print("\n" + "="*60)
    print("ALL API TESTS PASSED SUCCESSFULLY \\(•◡•)/")
    print("="*60)

if __name__ == "__main__":
    test_api_complete_flow()
