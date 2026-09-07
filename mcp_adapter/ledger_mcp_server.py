"""
ledger_mcp_server.py -- updated for mcp==2.1.1.

mcp 2.x renamed FastMCP -> MCPServer (mcp.server.fastmcp -> mcp.server.mcpserver)
and changed other APIs alongside it. That's the only thing that changed here:
the decorator target and the run() entry point. The three tool bodies are
byte-for-byte what was already verified working (against a stubbed FastMCP,
then confirmed identical to the hub-peer path) -- no logic changes, because
the logic wasn't what was broken.

Install, precisely: `pip install "mcp==2.1.1"` in a CLEAN environment
(venv recommended). Installing across several separate pip invocations with
different flags left one dependency (`mcp-types`) at a mismatched version in
one sandbox, which broke even `import mcp` with an unrelated-looking error
inside mcp.client.experimental. A single clean install in a fresh venv had
no such issue -- this was environment contamination, not a bug in the
package. If `import mcp` fails with an ImportError pointing into
`mcp.client.experimental` or `mcp.shared.experimental`, suspect this first.

Verified against the REAL package (not a stub) via mcp.client._memory's
InMemoryTransport + a real ClientSession: initialize, tools/list, and
tools/call for all three tools, including error paths (invalid category,
unknown key -- both correctly return {"ok": False, ...} as tool output, not
a protocol-level error) and MCP's own schema validation correctly rejecting
a call missing a required argument before ledger_log ever runs.

One real fix from that testing: the original `-> dict` return annotations
produced isError=False and correct data in `content` (text), but
`structured_content` was always None -- checked against this exact SDK's
auto-detection code, and confirmed empirically with a minimal repro, that a
bare `dict` annotation isn't structured-output-eligible here; `dict[str, Any]`
is. Changed to `dict[str, Any]` below so MCP clients that read
structuredContent (skipping JSON-in-text parsing) get real data instead of
None.

Same reasoning as before on reusing build_entry()/_find_contradictions()
directly rather than re-deriving validation logic: one implementation of
"what counts as a contradiction," used by the CLI, the hub peer, and this.
"""
from pathlib import Path
from typing import Any, Optional
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # ledger.py lives one level up
from mcp.server.mcpserver import MCPServer
import ledger as L

PATH = Path("ledger.json")
if not PATH.exists():
    L.save(PATH, {"project": "mcp-demo", "created": L.datetime.now(L.timezone.utc).isoformat(),
                  "next_id": 1, "entries": [], "comparators": {}})

server = MCPServer("ledger")


@server.tool()
def ledger_log(category: str, key: str, value: str, rationale: str = "",
                session: str = "", supersedes: Optional[int] = None,
                comparator: Optional[str] = None) -> dict[str, Any]:
    """Append a mechanically-tracked fact/decision/constant to the ledger.
    Same semantics as the CLI: same key + incompatible value + no
    supersedes = flagged by ledger_check(), deterministically."""
    data = L.load(PATH)
    warnings = []
    try:
        entry = L.build_entry(data, category=category, key=key, value=value,
                               rationale=rationale, session=session,
                               supersedes=supersedes, comparator=comparator,
                               warn=warnings.append)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    L.save(PATH, data)
    return {"ok": True, "id": entry["id"], "warnings": warnings}


@server.tool()
def ledger_check() -> dict[str, Any]:
    """Run mechanical contradiction detection over the whole ledger.
    No LLM judgment involved -- same key, incompatible value, no
    supersedes = contradiction, every time, deterministically."""
    data = L.load(PATH)
    contradictions, warnings = L._find_contradictions(data["entries"], data.get("comparators", {}))
    return {
        "ok": len(contradictions) == 0,
        "contradictions": [
            {"key": cur["key"], "origin_id": prev["id"], "origin_value": prev["value"],
             "latest_id": cur["id"], "latest_value": cur["value"]}
            for prev, cur in contradictions
        ],
        "warnings": warnings,
    }


@server.tool()
def ledger_show(key: str) -> dict[str, Any]:
    """Full history for one key, in id order."""
    data = L.load(PATH)
    entries = sorted((e for e in data["entries"] if e["key"] == key), key=lambda x: x["id"])
    if not entries:
        return {"ok": False, "error": f"no entries for key '{key}'"}
    return {"ok": True, "entries": entries}


if __name__ == "__main__":
    server.run()
