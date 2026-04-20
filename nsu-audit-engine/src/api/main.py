from dotenv import load_dotenv
import os

# Load .env BEFORE any config imports read environment variables
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(_env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import sys

# Ensure the parent 'src' directory is in the path so Vercel correctly resolves 'api.routers'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routers import auth, audit, history
from api.routers.history import record_call

app = FastAPI(
    title="NSU Audit Engine API",
    description="Backend API for the Graduation Audit Engine. Provides endpoints for NSU email auth, document parsing, and audit calculations.",
    version="1.0.0",
)

# Allow cross-origin requests from any frontend (React, Flutter, etc.) during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request Logging Middleware ──────────────────────────────────────
@app.middleware("http")
async def log_requests(request, call_next):
    """Middleware that records every API call for the history showcase."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000

    # Try to extract user from Authorization header
    user = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            import jwt
            from auth.config import AuthConfig
            config = AuthConfig.from_env()
            payload = jwt.decode(
                auth_header.split(" ")[1],
                config.jwt_secret,
                algorithms=[config.jwt_algorithm],
                issuer="nsu-audit-engine",
            )
            user = payload.get("sub")
        except Exception:
            pass

    # Skip logging the history endpoint itself to avoid recursion
    path = request.url.path
    if not path.startswith("/api/v1/history"):
        record_call(
            method=request.method,
            path=path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user=user,
        )

    return response


@app.get("/")
async def root():
    return {
        "message": "Welcome to the NSU Audit Engine API",
        "docs_url": "/docs",
        "status": "online"
    }

from api.dependencies import verify_api_key
from fastapi import Depends

# Include routers
app.include_router(
    auth.router, 
    prefix="/api/v1/auth", 
    tags=["Authentication"], 
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    audit.router, 
    prefix="/api/v1/audit", 
    tags=["Audit & Transcripts"], 
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    history.router,
    prefix="/api/v1/history",
    tags=["API Call History"],
    dependencies=[Depends(verify_api_key)]
)

if __name__ == "__main__":
    import uvicorn
    # Use python -m api.main or run directly
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
