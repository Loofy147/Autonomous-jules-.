"""
ledger_tool_demo.py -- proves ledger_tool.py works as a real hub peer,
same scenario already verified against ledger_mcp_server.py (log a
conflict, detect it, resolve it via supersedes, show history, and check
that error paths -- bad category, unknown key -- come back as clean
{"ok": False, ...} results over real RPC instead of hanging or crashing
the tool's message loop.
"""
import asyncio
import json

from hub import main as run_hub
from tool_client import ToolClient
from ledger_tool import ledger_tool, PATH


async def caller(done: asyncio.Event):
    client = ToolClient("caller", capabilities=[])
    await client.connect()
    await asyncio.sleep(0.15)

    print("--- log D=1024 ---")
    print(await client.invoke("ledger", "log", {"category": "constant", "key": "D", "value": "1024", "session": "s1"}))

    print("--- log D=512 (conflict, no supersede) ---")
    print(await client.invoke("ledger", "log", {"category": "constant", "key": "D", "value": "512", "session": "s9"}))

    print("--- check (expect 1 unresolved) ---")
    r = await client.invoke("ledger", "check", {})
    print(json.dumps(r, indent=2))

    print("--- resolve via supersedes ---")
    print(await client.invoke("ledger", "log",
          {"category": "constant", "key": "D", "value": "1024", "session": "s12", "supersedes": 2}))

    print("--- check (expect clean) ---")
    print(await client.invoke("ledger", "check", {}))

    print("--- show D ---")
    r = await client.invoke("ledger", "show", {"key": "D"})
    print(json.dumps(r, indent=2)[:400])

    print("--- invalid category (should be a clean ok:False over the wire, not a hang/crash) ---")
    print(await client.invoke("ledger", "log", {"category": "nonsense", "key": "X", "value": "1"}, timeout=3.0))

    print("--- unknown key for show ---")
    print(await client.invoke("ledger", "show", {"key": "does-not-exist"}))

    done.set()


async def main():
    hub_task = asyncio.create_task(run_hub())
    await asyncio.sleep(0.15)
    done = asyncio.Event()
    tools = [asyncio.create_task(ledger_tool()), asyncio.create_task(caller(done))]
    await done.wait()
    for t in tools:
        t.cancel()
    hub_task.cancel()
    await asyncio.gather(*tools, hub_task, return_exceptions=True)


if __name__ == "__main__":
    PATH.unlink(missing_ok=True)
    asyncio.run(main())
