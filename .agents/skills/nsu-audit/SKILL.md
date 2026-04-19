---
name: nsu-audit
description: How to use the NSU Graduation Audit Engine MCP server to analyze student transcripts
---

# NSU Audit Engine Skill

This skill enables AI assistants to perform graduation audits for North South University students using the NSU Audit Engine MCP server.

## Prerequisites

1. **FastAPI backend** must be running at `http://localhost:8000` (or set `NSU_API_URL`)
2. **MCP server** must be configured in the client settings (see below)

### Starting the Backend

```bash
cd nsu-audit-engine/src
pip install -r ../requirements.txt
python -m api.main
```

### MCP Server Configuration

Add to your MCP settings:

```json
{
  "mcpServers": {
    "nsu-audit-engine": {
      "command": "python",
      "args": ["<project-root>/nsu-audit-engine/mcp-server/server.py"],
      "env": {
        "NSU_API_URL": "http://localhost:8000",
        "NSU_API_KEY": "MySuperSecretNSUKey2026!"
      }
    }
  }
}
```

## Workflow: Running a Graduation Audit

### Step 1: Authenticate

```
→ request_otp(email="student@northsouth.edu")
← "OTP sent to student@northsouth.edu" (or dev mode: OTP printed)
```

### Step 2: Verify OTP

```
→ verify_otp(email="student@northsouth.edu", otp="123456")
← { access_token: "eyJ...", user: { email: "student@northsouth.edu" } }
```

**Save the `access_token`** — you need it for all subsequent calls.

### Step 3: Upload Transcript & Run Audit

```
→ run_audit(file_path="/path/to/transcript.pdf", token="eyJ...", program_type="BBA")
← Full audit report with CGPA, credits, eligibility, deficiencies
```

**Supported file formats**: CSV, PDF, DOCX, XLSX, XLS, TXT, TSV, JSON, PNG, JPG, BMP, TIFF, WEBP

### Step 4 (Optional): Check Profile

```
→ get_profile(token="eyJ...")
← { email: "student@northsouth.edu", role: "student" }
```

## Tool Reference

| Tool | Parameters | Auth | Purpose |
|------|-----------|------|---------|
| `request_otp` | `email` (string) | No | Send OTP to NSU email |
| `verify_otp` | `email`, `otp` (strings) | No | Verify OTP → get JWT |
| `run_audit` | `file_path`, `token`, `program_type?` | JWT | Run graduation audit |
| `get_profile` | `token` | JWT | Get user info |
| `get_supported_formats` | none | No | List file formats |
| `get_api_history` | `limit?` (int) | No | View API call log |

## Error Handling

- **403**: Invalid API key → Check `NSU_API_KEY` env var
- **401**: Expired or invalid JWT → Re-authenticate with `request_otp` + `verify_otp`
- **400**: Bad file format or corrupt transcript → Try a different file format
- **500**: Backend error → Check the FastAPI server logs

## Supported Programs

- **BBA** — Bachelor of Business Administration (126 credits)
- **CSE** — Computer Science & Engineering (130 credits)
