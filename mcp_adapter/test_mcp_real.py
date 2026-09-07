"""
test_mcp_real.py -- the test the last pass couldn't do: a real ClientSession
talking to a real MCPServer over real MCP protocol messages (initialize,
tools/list, tools/call), using the SDK's own InMemoryTransport instead of a
stand-in FastMCP. Same scenario as ledger_tool_demo.py (the hub-peer test),
for a fair before/after and hub/MCP comparison.
"""
import asyncio
import json
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client._memory import InMemoryTransport

Path("ledger.json").unlink(missing_ok=True)
import ledger_mcp_server as server_module


def unwrap(result):
    """CallToolResult -> the actual dict my tool functions returned.
    structuredContent carries it; content is the text fallback MCP also
    generates. isError=True would mean the tool function raised, which
    none of these should do -- they return {"ok": False, ...} instead."""
    return {"isError": result.is_error, "structured": result.structured_content,
            "content": [getattr(c, "text", c) for c in result.content]}


async def main():
    transport = InMemoryTransport(server_module.server)
    async with transport as (read, write):
        async with ClientSession(read, write) as session:
            init_result = await session.initialize()
            print(f"--- initialize ---\nserver: {init_result.server_info.name} "
                  f"protocol={init_result.protocol_version}\n")

            tools = await session.list_tools()
            print(f"--- tools/list ---\n{[t.name for t in tools.tools]}\n")

            print("--- log D=1024 ---")
            r = await session.call_tool("ledger_log", {"category": "constant", "key": "D",
                                                          "value": "1024", "session": "s1"})
            print(unwrap(r))

            print("--- log D=512 (conflict, no supersede) ---")
            r = await session.call_tool("ledger_log", {"category": "constant", "key": "D",
                                                          "value": "512", "session": "s9"})
            print(unwrap(r))

            print("--- check (expect 1 unresolved) ---")
            r = await session.call_tool("ledger_check", {})
            print(json.dumps(unwrap(r), indent=2))

            print("--- resolve via supersedes ---")
            r = await session.call_tool("ledger_log", {"category": "constant", "key": "D",
                                                          "value": "1024", "session": "s12", "supersedes": 2})
            print(unwrap(r))

            print("--- check (expect clean) ---")
            r = await session.call_tool("ledger_check", {})
            print(unwrap(r))

            print("--- show D ---")
            r = await session.call_tool("ledger_show", {"key": "D"})
            print(json.dumps(unwrap(r), indent=2)[:400])

            print("--- invalid category (real protocol error path, not a stub) ---")
            r = await session.call_tool("ledger_log", {"category": "nonsense", "key": "X", "value": "1"})
            print(unwrap(r))

            print("--- unknown key for show ---")
            r = await session.call_tool("ledger_show", {"key": "does-not-exist"})
            print(unwrap(r))

            print("--- malformed call: missing required 'value' arg (tests MCP's OWN schema validation) ---")
            try:
                r = await session.call_tool("ledger_log", {"category": "constant", "key": "Y"})
                print(unwrap(r))
            except Exception as e:
                print(f"raised {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
