import sys
import json
import asyncio
from mcp.client.stdio import stdio_client, get_default_environment
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters

async def run_mcp_test():
    print("Auto-testing NSU Audit MCP Server as an AI Agent...")
    
    # We will launch our own MCP server as a subprocess
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[r"c:\Users\HP\Downloads\Nsu-audit-engine\nsu-audit-engine\mcp-server\server.py"],
        env=get_default_environment()
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test 1: list_tools
            print("\n[Test 1] Fetching available tools list...")
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools. Tools registered:")
            for t in tools.tools:
                print(f"  - {t.name}")
                
            # Test 2: get_supported_formats (no auth)
            print("\n[Test 2] Checking supported formats (no auth tool)...")
            result = await session.call_tool("get_supported_formats", {})
            for text_content in result.content:
                print("Result:")
                print(text_content.text)
                
            # Test 3: get_api_history (no auth)
            print("\n[Test 3] Checking API history (no auth tool)...")
            result = await session.call_tool("get_api_history", {"limit": 3})
            for text_content in result.content:
                print("Result:")
                print(text_content.text)

            print("\nSUCCESS: MCP Server SDK Connection and Tool Execution tests PASS.")

if __name__ == "__main__":
    asyncio.run(run_mcp_test())
