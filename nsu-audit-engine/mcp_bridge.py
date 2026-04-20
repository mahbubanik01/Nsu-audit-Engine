import sys
import json
import asyncio
import os
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

async def call_mcp_tool(tool_name, arguments):
    # Path to the server script
    server_script = r"c:\Users\HP\Downloads\Nsu-audit-engine\nsu-audit-engine\mcp-server\server.py"
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python mcp_bridge.py <tool_name> [json_args]")
        sys.exit(1)
        
    tool = sys.argv[1]
    
    # Try to parse JSON from the rest of the arguments
    raw_args = " ".join(sys.argv[2:])
    if not raw_args:
        args = {}
    else:
        try:
            # Handle cases where PowerShell strips quotes: {limit: 10} -> {"limit": 10}
            if raw_args.startswith('{') and '"' not in raw_args:
                import re
                raw_args = re.sub(r'(\w+):', r'"\1":', raw_args)
            args = json.loads(raw_args)
        except Exception:
            # Fallback: try to interpret as simple key=value pairs
            args = {}
            for part in sys.argv[2:]:
                if '=' in part:
                    k, v = part.split('=', 1)
                    try:
                        args[k] = json.loads(v)
                    except:
                        args[k] = v
    
    try:
        res = asyncio.run(call_mcp_tool(tool, args))
        # Print only the text content
        for content in res.content:
            if hasattr(content, 'text'):
                print(content.text)
            else:
                print(content)
    except Exception as e:
        print(f"Error calling MCP: {e}", file=sys.stderr)
        sys.exit(1)
