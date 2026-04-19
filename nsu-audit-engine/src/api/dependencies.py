from fastapi import Header, HTTPException, status, Security
from fastapi.security.api_key import APIKeyHeader
from auth.auth import AuthService
import jwt
from auth.config import AuthConfig

config = AuthConfig.from_env()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    FastAPI dependency to verify API Key.
    Expects header: "X-API-Key: <token>"
    """
    # If API key is wrong or missing
    if api_key != config.nsu_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing X-API-Key"
        )
    return api_key

async def get_current_user(authorization: str = Header(None)) -> str:
    """
    FastAPI dependency to protect routes.
    Expects header: "Authorization: Bearer <token>"
    Returns the user's email if valid, otherwise raises HTTPException.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'"
        )
        
    token = parts[1]
    
    try:
        # We rely on the core JWT logic. We can decode it directly here
        payload = jwt.decode(
            token, 
            config.jwt_secret, 
            algorithms=[config.jwt_algorithm],
            issuer="nsu-audit-engine"
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token does not contain user email subject"
            )
        return email
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
