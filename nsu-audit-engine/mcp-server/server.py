"""
NSU Audit Engine — MCP Server
Exposes the audit engine's FastAPI endpoints as MCP tools
for AI assistants (Gemini, Claude, etc.).

Usage:
    python server.py                          # defaults to http://localhost:8000
    NSU_API_URL=https://my-api.com python server.py
"""

import os
import sys
import json
import base64
import asyncio
import mimetypes
from pathlib import Path
from typing import Optional

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ─── Configuration ──────────────────────────────────────────────────────────
API_BASE_URL = os.environ.get("NSU_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("NSU_API_KEY", "dev_secret_key")

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
                    "═" * 60,
                    "GRADUATION AUDIT RESULTS",
                    "═" * 60,
                    f"Student: {audit['student'].get('name', 'N/A')} ({audit['student'].get('id', 'N/A')})",
                    f"Program: {audit['program']}",
                    "",
                    f"{'✓ ELIGIBLE' if audit['summary']['is_eligible'] else '✗ NOT ELIGIBLE'} TO GRADUATE",
                    "",
                    f"CGPA:            {audit['summary']['cgpa']}",
                    f"Credits Earned:  {audit['summary']['credits_earned']}",
                    f"Credits Required: {audit['summary']['credits_required']}",
                    f"Records Parsed:  {audit['raw_records']}",
                    f"Retaken Courses: {len(audit['retaken_courses'])}",
                    "═" * 60,
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
                    text=f"Supported transcript formats:\n" + "\n".join(f"  • {ext}" for ext in sorted(formats)),
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
                return [TextContent(type="text", text=json.dumps(resp.json(), indent=2))]
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
