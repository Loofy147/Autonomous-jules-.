"""
ledger_tool.py -- full-command hub peer, built on top of the new ledger.py
(build_entry / _find_contradictions returning (contradictions, warnings)).

The uploaded ledger_tool.py scoped itself to log/check/show on purpose, for
a fair comparison against ledger_mcp_server.py. This extends that same
approach to the other five CLI commands instead of losing them, using two
patterns depending on whether the underlying cmd_* function can sys.exit
in a state we'd actually hit at runtime:

  - log/check/show/init: no sys.exit reachable. log uses build_entry
    directly (raises ValueError, never sys.exit). check/show reimplement
    the read-only lookup directly, same as the uploaded files do, rather
    than calling cmd_check/cmd_show (which still print-and-return rather
    than returning structured data, and cmd_show specifically still
    sys.exits on an unknown key). init duplicates cmd_init's one
    exists-check as a plain return rather than routing through sys.exit.
  - digest/health/keys/stale: no sys.exit path was found in any of these
    in the current ledger.py (checked by reading, not assumed) given the
    ledger file already exists -- which this module guarantees on
    startup, same as the uploaded ledger_tool.py does. These are wrapped
    with stdout-capture and a defensive SystemExit catch anyway, as cheap
    insurance rather than because a path to it was found.
"""
import contextlib
import io
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # ledger.py lives one level up
import ledger as L
from tool_client import ToolClient

PATH = Path("ledger.json")


def _run_cli_report(fn, **kwargs):
    """For the four report-only commands: capture stdout, catch SystemExit
    defensively (belt-and-suspenders; no live path to it was found in any
    of the four, but a peer process dying on a report command would be a
    bad way to find out that assumption was wrong)."""
    args = SimpleNamespace(path=str(PATH), **kwargs)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = fn(args)
        return {"ok": (rc if isinstance(rc, int) else 0) == 0, "output": buf.getvalue()}
    except SystemExit as e:
        return {"ok": False, "output": buf.getvalue(), "error": str(e.code)}


async def ledger_tool(tool_id="ledger"):
    if not PATH.exists():
        L.save(PATH, {"project": "hub-demo", "created": L.datetime.now(L.timezone.utc).isoformat(),
                       "next_id": 1, "entries": [], "comparators": {}})

    client = ToolClient(tool_id, capabilities=["init", "log", "check", "digest", "health",
                                                 "show", "keys", "stale"])
    await client.connect()

    async def init(payload):
        project = payload["project"]
        force = payload.get("force", False)
        if PATH.exists() and not force:
            return {"ok": False, "error": f"{PATH} already exists. Use force=True to overwrite."}
        L.save(PATH, {"project": project, "created": L.datetime.now(L.timezone.utc).isoformat(),
                       "next_id": 1, "entries": [], "comparators": {}})
        return {"ok": True, "project": project}

    async def log(payload):
        data = L.load(PATH)
        warnings = []
        try:
            entry = L.build_entry(
                data, category=payload["category"], key=payload["key"], value=payload["value"],
                rationale=payload.get("rationale", ""), session=payload.get("session", ""),
                supersedes=payload.get("supersedes"), comparator=payload.get("comparator"),
                warn=warnings.append,
            )
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        L.save(PATH, data)
        return {"ok": True, "id": entry["id"], "warnings": warnings}

    async def check(payload):
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

    async def show(payload):
        data = L.load(PATH)
        entries = sorted((e for e in data["entries"] if e["key"] == payload["key"]), key=lambda x: x["id"])
        if not entries:
            return {"ok": False, "error": f"no entries for key '{payload['key']}'"}
        return {"ok": True, "entries": entries}

    async def digest(payload):
        return _run_cli_report(L.cmd_digest)

    async def health(payload):
        return _run_cli_report(L.cmd_health)

    async def keys(payload):
        return _run_cli_report(L.cmd_keys, threshold=payload.get("threshold", 0.80))

    async def stale(payload):
        return _run_cli_report(L.cmd_stale, days=payload.get("days", 30), category=payload.get("category"))

    client.on_invoke("init", init)
    client.on_invoke("log", log)
    client.on_invoke("check", check)
    client.on_invoke("show", show)
    client.on_invoke("digest", digest)
    client.on_invoke("health", health)
    client.on_invoke("keys", keys)
    client.on_invoke("stale", stale)
    await client.run()


if __name__ == "__main__":
    import asyncio
    from hub import main as run_hub

    async def standalone():
        hub_task = asyncio.create_task(run_hub())
        await asyncio.sleep(0.15)
        await ledger_tool()

    asyncio.run(standalone())
