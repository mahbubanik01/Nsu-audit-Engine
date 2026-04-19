from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Dict, Any

from api.schemas import OTPRequest, OTPVerify, TokenResponse, GoogleAuthVerify
from api.dependencies import get_current_user
from auth.auth import AuthService
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

router = APIRouter()
auth_service = AuthService()

@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(data: OTPRequest):
    """
    Request an OTP for an NSU email address.
    """
    success, message = auth_service.request_otp(data.email)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(data: OTPVerify):
    """
    Verify the OTP and return a JWT access token.
    """
    success, token, message = auth_service.verify_and_issue_token(data.email, data.otp)
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return TokenResponse(
        access_token=token,
        user={"email": data.email}
    )

@router.post("/google", response_model=TokenResponse)
async def verify_google_auth(data: GoogleAuthVerify):
    """
    Verify Google ID Token from Frontend.
    Ensures the user belongs to North South University.
    Returns standard JWT session token.
    """
    try:
        # Verify the token with Google
        idinfo = id_token.verify_oauth2_token(
            data.credential, google_requests.Request(), data.client_id
        )
        email = idinfo.get("email", "")
        
        if not email.endswith("@northsouth.edu"):
            raise HTTPException(
                status_code=403, 
                detail="Only @northsouth.edu accounts are allowed."
            )
            
        # Issue our own backend JWT
        token = auth_service.token_manager.issue_token(email)
        return TokenResponse(
            access_token=token,
            user={"email": email, "name": idinfo.get("name"), "picture": idinfo.get("picture")}
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid Google token: {str(e)}")

@router.get("/me")
async def get_my_profile(email: str = Depends(get_current_user)):
    """
    Get the currently logged-in user profile using the JWT token.
    """
    return {
        "email": email,
        "domain": "northsouth.edu",
        "role": "student"
    }
