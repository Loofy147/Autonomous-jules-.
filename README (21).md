# ledger — mechanical decision/context ledger for long AI-assisted sessions

A file-based ledger for tracking decisions, constants, goals, and scope
changes across long multi-session projects, with **mechanical** contradiction
detection — same key, incompatible value, no explicit supersede = flagged,
every time, deterministically. No LLM judgment, no semantic matching. That's
a real limitation (it won't catch a contradiction phrased in different words)
and a real feature (every flag is explainable in one sentence, and it costs
nothing to run).

## Layout

```
ledger.py              <- the whole core. stdlib only, zero dependencies.
docs/
  schema.md            <- file format, comparator registry, algorithms, exact command list
  walkthrough.md        <- real captured CLI output, not invented examples
mcp_adapter/            <- OPTIONAL: exposes ledger.py as MCP tools
  ledger_mcp_server.py
  test_mcp_real.py       <- real protocol test (InMemoryTransport + ClientSession), not a stub
  requirements.txt       <- mcp==2.1.1
hub_adapter/            <- OPTIONAL, heavier: exposes ledger.py on a custom WebSocket hub
  ledger_tool.py
  ledger_tool_demo.py
  hub.py, tool_client.py <- vendored hub runtime this adapter depends on
  requirements.txt       <- websockets
```

`ledger.py` needs nothing else to run. The two adapters are separate,
optional integration surfaces on top of it — pick the one that matches how
you actually want to reach the ledger, or neither and just use the CLI.

## Quickstart (core CLI)

```
python3 ledger.py init "my-project"
python3 ledger.py log --category constant --key D --value 1024 --session s1
python3 ledger.py check          # exit 1 if anything's unresolved
python3 ledger.py digest         # paste this at the top of a fresh session
```

Full command reference, the comparator registry, and exactly what the tool
does and doesn't catch: `docs/schema.md`. A real, captured end-to-end run:
`docs/walkthrough.md`.

## Adapters

**MCP** (`mcp_adapter/`): the lighter option. Standards-based, works with any
MCP host. Currently exposes `log`/`check`/`show` — extend
`ledger_mcp_server.py` the same way `hub_adapter/ledger_tool.py` extends to
all eight if you need `digest`/`health`/`keys`/`stale`/`init` over MCP too.
Install in a **clean/isolated environment**:

```
cd mcp_adapter && pip install -r requirements.txt && python3 ledger_mcp_server.py
```

**Hub** (`hub_adapter/`): exposes all eight commands over a small custom
WebSocket RPC hub. Its one real advantage over MCP is peer-to-peer tool
invocation without an LLM deciding each hop — genuinely useful if that's
something you need, genuinely extra maintenance if it isn't. Worth a
deliberate choice, not a default.

```
cd hub_adapter && pip install -r requirements.txt && python3 ledger_tool_demo.py
```

## On whether this is worth building further

Short version, longer version was given in conversation: the ledger core is
the real, worthwhile asset — narrow, solves an actual problem, and the
mechanical/deterministic positioning is a genuine (if niche) differentiator
against the mostly-semantic competition in this space (Spec Kit, Drift,
Kiro, etc.). The hub adapter is the weaker half — it duplicates ground MCP
already standardizes, and is worth keeping only if peer-to-peer tool
invocation without an LLM in the loop is actually load-bearing for what
you're building elsewhere (Neurogolf, red-team agent, DCS-Net). If it isn't,
the MCP adapter alone is probably enough, and the hub adapter is optional
weight rather than a foundation.

## Verified, not claimed

Every behavior described above has been run, not just written:
- Full CLI regression (init/log/check/show/keys/stale, including the
  `numeric_range` comparator) from this exact package layout.
- The hub adapter's full demo, from `hub_adapter/`, against the vendored
  hub/tool_client — includes error paths (invalid category, unknown key)
  coming back clean over RPC rather than hanging or crashing.
- The MCP adapter against the **real** `mcp==2.1.1` package via
  `InMemoryTransport` + a real `ClientSession` — real `initialize`,
  `tools/list`, `tools/call`, including MCP's own schema validation
  correctly rejecting a call missing a required argument before
  `ledger_log` ever runs.

Two real bugs were caught and fixed in the course of building this, both
documented at the point they were found rather than smoothed over: a
stale-connection registry bug in the hub (fixed in `hub.py`), and a bare
`dict` return annotation silently dropping MCP's `structuredContent` (fixed
in `ledger_mcp_server.py` by annotating `dict[str, Any]` instead).
