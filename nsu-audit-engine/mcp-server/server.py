"""
NSU Audit Engine — MCP Server
Exposes the audit engine's FastAPI endpoints as MCP tools
for AI assistants (Gemini, Claude, etc.).

Usage:
    python server.py                          # defaults to http://localhost:8000
    NSU_API_URL=https://my-api.com python server.py
"""

import io
import os
import sys
import json
import base64
import asyncio
import mimetypes
import datetime
from pathlib import Path
from typing import Optional

# Force UTF-8 for Windows compatibility with special characters (✓, ✗, ═, etc.)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ─── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("NSU_API_URL", "https://nsu-audit-engine.vercel.app")
API_KEY = os.environ.get("NSU_API_KEY", "MySuperSecretNSUKey2026!")

DEFAULT_HEADERS = {
    "X-API-Key": API_KEY,
}

# ─── MCP Server ─────────────────────────────────────────────────────────────
server = Server("nsu-audit-engine")


def _auth_headers(token: Optional[str] = None) -> dict:
    """Build headers with optional Bearer token."""
    headers = dict(DEFAULT_HEADERS)
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ─── Tool Definitions ───────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="request_otp",
            description=(
                "Request a one-time password (OTP) for an NSU email address. "
                "Only @northsouth.edu emails are accepted. "
                "The OTP will be sent to the email (or printed in dev mode)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "NSU email address (e.g. student@northsouth.edu)",
                    }
                },
                "required": ["email"],
            },
        ),
        Tool(
            name="verify_otp",
            description=(
                "Verify an OTP and receive a JWT access token. "
                "Use the token for subsequent authenticated requests."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "NSU email address used to request the OTP",
                    },
                    "otp": {
                        "type": "string",
                        "description": "The 6-digit OTP code",
                    },
                },
                "required": ["email", "otp"],
            },
        ),
        Tool(
            name="run_audit",
            description=(
                "Upload a student transcript file and run a full graduation audit. "
                "Supports: CSV, PDF, DOCX, XLSX, TXT, TSV, JSON, and image files. "
                "Returns eligibility status, CGPA, credits, deficiencies, and retake history. "
                "Requires a valid JWT token from verify_otp."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the transcript file on disk",
                    },
                    "program_type": {
                        "type": "string",
                        "enum": ["BBA", "CSE"],
                        "description": "Degree program type (default: BBA)",
                        "default": "BBA",
                    },
                    "token": {
                        "type": "string",
                        "description": "JWT access token from verify_otp",
                    },
                },
                "required": ["file_path", "token"],
            },
        ),
        Tool(
            name="get_profile",
            description=(
                "Get the authenticated user's profile information. "
                "Requires a valid JWT token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "JWT access token",
                    }
                },
                "required": ["token"],
            },
        ),
        Tool(
            name="get_supported_formats",
            description=(
                "List all file formats supported for transcript upload. "
                "No authentication required."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_api_history",
            description=(
                "Get recent API call history for monitoring. "
                "Shows method, path, status code, duration, and user."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Max number of entries to return (default: 20)",
                        "default": 20,
                    }
                },
            },
        ),
        Tool(
            name="get_user_audit_history",
            description=(
                "Get the authenticated user's past graduation scans/audits. "
                "Requires a valid JWT token."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "token": {
                        "type": "string",
                        "description": "JWT access token from verify_otp",
                    }
                },
                "required": ["token"],
            },
        ),
    ]


# ─── Tool Handlers ──────────────────────────────────────────────────────────

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    async with httpx.AsyncClient(base_url=API_BASE_URL, timeout=60.0) as client:

        # ── request_otp ─────────────────────────────────────────────
        if name == "request_otp":
            email = arguments["email"]
            resp = await client.post(
                "/api/v1/auth/request-otp",
                json={"email": email},
                headers=DEFAULT_HEADERS,
            )
            if resp.status_code == 200:
                return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── verify_otp ──────────────────────────────────────────────
        elif name == "verify_otp":
            resp = await client.post(
                "/api/v1/auth/verify-otp",
                json={"email": arguments["email"], "otp": arguments["otp"]},
                headers=DEFAULT_HEADERS,
            )
            if resp.status_code == 200:
                data = resp.json()
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "status": "authenticated",
                        "access_token": data["access_token"],
                        "user": data["user"],
                        "note": "Save this access_token for subsequent tool calls.",
                    }, indent=2),
                )]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── run_audit ───────────────────────────────────────────────
        elif name == "run_audit":
            file_path = arguments["file_path"]
            token = arguments["token"]
            program_type = arguments.get("program_type", "BBA")

            path = Path(file_path)
            if not path.exists():
                return [TextContent(type="text", text=f"Error: File not found: {file_path}")]

            mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

            with open(file_path, "rb") as f:
                files = {"file": (path.name, f, mime_type)}
                data = {"program_type": program_type}
                resp = await client.post(
                    "/api/v1/audit/run",
                    headers=_auth_headers(token),
                    files=files,
                    data=data,
                )

            if resp.status_code == 200:
                audit = resp.json()
                # Format a human-readable summary alongside the raw JSON
                summary_lines = [
                    "=" * 60,
                    "GRADUATION AUDIT RESULTS",
                    "=" * 60,
                    f"Student: {audit['student'].get('name', 'N/A')} ({audit['student'].get('id', 'N/A')})",
                    f"Program: {audit['program']}",
                    "",
                    f"{'[PASS] ELIGIBLE' if audit['summary']['is_eligible'] else '[FAIL] NOT ELIGIBLE'} TO GRADUATE",
                    "",
                    f"CGPA:            {audit['summary']['cgpa']}",
                    f"Credits Earned:  {audit['summary']['credits_earned']}",
                    f"Credits Required: {audit['summary']['credits_required']}",
                    f"Records Parsed:  {audit['raw_records']}",
                    f"Retaken Courses: {len(audit['retaken_courses'])}",
                    "=" * 60,
                    "",
                    "Full JSON response:",
                    json.dumps(audit, indent=2),
                ]
                return [TextContent(type="text", text="\n".join(summary_lines))]

            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── get_profile ─────────────────────────────────────────────
        elif name == "get_profile":
            token = arguments["token"]
            resp = await client.get(
                "/api/v1/auth/me",
                headers=_auth_headers(token),
            )
            if resp.status_code == 200:
                return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── get_supported_formats ────────────────────────────────────
        elif name == "get_supported_formats":
            resp = await client.get(
                "/api/v1/audit/supported-formats",
                headers=DEFAULT_HEADERS,
            )
            if resp.status_code == 200:
                formats = resp.json().get("supported_extensions", [])
                return [TextContent(
                    type="text",
                    text=f"Supported transcript formats:\n" + "\n".join(f"  - {ext}" for ext in sorted(formats)),
                )]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── get_api_history ──────────────────────────────────────────
        elif name == "get_api_history":
            limit = arguments.get("limit", 20)
            resp = await client.get(
                "/api/v1/history/",
                headers=DEFAULT_HEADERS,
                params={"limit": limit},
            )
            if resp.status_code == 200:
                data = resp.json()
                calls = data.get("calls", [])
                
                # Format a human-readable summary alongside the raw JSON
                summary_lines = [
                    "=" * 80,
                    "API CALL HISTORY (TELEMETRY)",
                    "=" * 80,
                    f"Total Logged: {data.get('total_logged', 0)}",
                    f"Showing:      {data.get('showing', 0)}",
                    "-" * 80,
                    f"{'METHOD':<8} | {'ENDPOINT':<40} | {'STATUS':<6} | {'LATENCY':<10} | {'TIME'}",
                    "-" * 80,
                ]
                
                for call in calls:
                    method = call.get("method", "UNK")
                    path = call.get("path", "")
                    if len(path) > 37:
                        path = path[:34] + "..."
                    status = str(call.get("status_code", 0))
                    latency = f"{call.get('duration_ms', 0):.0f}ms"
                    
                    # Convert ISO timestamp to a simpler format
                    try:
                        ts = datetime.datetime.fromisoformat(call.get("timestamp", "").replace("Z", "+00:00"))
                        time_str = ts.strftime("%H:%M:%S")
                    except Exception:
                        time_str = call.get("timestamp", "")
                    
                    summary_lines.append(f"{method:<8} | {path:<40} | {status:<6} | {latency:<10} | {time_str}")
                    
                summary_lines.extend([
                    "=" * 80,
                    "",
                    "Raw JSON response:",
                    json.dumps(data, indent=2)
                ])
                
                return [TextContent(type="text", text="\n".join(summary_lines))]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── get_user_audit_history ──────────────────────────────────
        elif name == "get_user_audit_history":
            token = arguments["token"]
            resp = await client.get(
                "/api/v1/audit/history",
                headers=_auth_headers(token),
            )
            if resp.status_code == 200:
                data = resp.json()
                audits = data.get("audits", [])
                
                summary_lines = [
                    "=" * 80,
                    "USER AUDIT HISTORY (PAST SCANS)",
                    "=" * 80,
                    f"Total Scans Found: {len(audits)}",
                    "-" * 80,
                    f"{'STUDENT NAME':<20} | {'PROGRAM':<7} | {'CGPA':<5} | {'ELIGIBILITY':<12} | {'TIME'}",
                    "-" * 80,
                ]
                
                for a in audits:
                    student = a.get("student", {}).get("name", "Unknown")
                    if len(student) > 19: student = student[:16] + "..."
                    prog = a.get("program", "UNK")
                    cgpa = f"{a.get('summary', {}).get('cgpa', 0.0):.2f}"
                    elig = "Eligible" if a.get("summary", {}).get("is_eligible", False) else "Not Eligible"
                    
                    try:
                        ts = datetime.datetime.fromisoformat(a.get("scan_timestamp", "").replace("Z", "+00:00"))
                        time_str = ts.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        time_str = a.get("scan_timestamp", "Recent")[:16]
                        
                    summary_lines.append(f"{student:<20} | {prog:<7} | {cgpa:<5} | {elig:<12} | {time_str}")
                
                summary_lines.extend([
                    "=" * 80,
                    "",
                    "Raw JSON response:",
                    json.dumps(data, indent=2)
                ])
                return [TextContent(type="text", text="\n".join(summary_lines))]
            return [TextContent(type="text", text=f"Error {resp.status_code}: {resp.text}")]

        # ── Unknown tool ─────────────────────────────────────────────
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ─── Entry Point ─────────────────────────────────────────────────────────────

async def main():
    """Run the MCP server over stdio."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
