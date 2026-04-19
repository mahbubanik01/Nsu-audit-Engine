# NSU Audit Engine — MCP Server

Model Context Protocol server that exposes the NSU Audit Engine as AI-callable tools.

## Setup

```bash
cd mcp-server
pip install -r requirements.txt
```

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `NSU_API_URL` | `http://localhost:8000` | FastAPI backend URL |
| `NSU_API_KEY` | `dev_secret_key` | API key for authentication |

## Usage

### 1. Start the FastAPI backend
```bash
cd ../src
python -m api.main
```

### 2. Run the MCP server
```bash
python server.py
```

### 3. Configure in your AI assistant

Add to your MCP client configuration (e.g., `settings.json`):

```json
{
  "mcpServers": {
    "nsu-audit-engine": {
      "command": "python",
      "args": ["path/to/mcp-server/server.py"],
      "env": {
        "NSU_API_URL": "http://localhost:8000",
        "NSU_API_KEY": "dev_secret_key"
      }
    }
  }
}
```

## Available Tools

| Tool | Description | Auth Required |
|------|-------------|---------------|
| `request_otp` | Send OTP to an NSU email | No |
| `verify_otp` | Verify OTP, get JWT token | No |
| `run_audit` | Upload transcript + run audit | Yes (JWT) |
| `get_profile` | Get user profile | Yes (JWT) |
| `get_supported_formats` | List supported file types | No |
| `get_api_history` | View recent API calls | No |

## Example Workflow

```
1. request_otp(email="student@northsouth.edu")
2. verify_otp(email="student@northsouth.edu", otp="123456")
   → Returns: { access_token: "eyJ..." }
3. run_audit(file_path="/path/to/transcript.pdf", token="eyJ...", program_type="BBA")
   → Returns: Full graduation audit report
```
