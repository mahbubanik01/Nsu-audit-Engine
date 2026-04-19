"""
API Call History Router
Exposes logged API requests for monitoring and showcase purposes.
"""

from fastapi import APIRouter
from typing import Optional
import datetime

router = APIRouter()

# In-memory call log (capped at 500 entries)
call_log: list = []
MAX_LOG_SIZE = 500


def record_call(method: str, path: str, status_code: int, duration_ms: float, user: Optional[str] = None):
    """Record an API call into the in-memory log."""
    entry = {
        "id": len(call_log) + 1,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2),
        "user": user,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    call_log.append(entry)
    # Cap the log size
    if len(call_log) > MAX_LOG_SIZE:
        call_log.pop(0)


@router.get("/")
async def get_call_history(limit: int = 50, method: Optional[str] = None, path_contains: Optional[str] = None):
    """
    Returns the most recent API call history.
    Supports optional filters by HTTP method and path substring.
    """
    results = list(reversed(call_log))  # newest first

    if method:
        results = [r for r in results if r["method"] == method.upper()]
    if path_contains:
        results = [r for r in results if path_contains.lower() in r["path"].lower()]

    return {
        "total_logged": len(call_log),
        "showing": min(limit, len(results)),
        "calls": results[:limit]
    }
