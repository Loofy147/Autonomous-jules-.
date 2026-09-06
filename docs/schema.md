# Ledger schema and algorithms (matches ledger.py as shipped in this package)

## File format

`ledger.json`:

```json
{
  "project": "stratos-monorepo",
  "created": "2026-09-06T17:33:00+00:00",
  "next_id": 4,
  "entries": [
    {
      "id": 1,
      "timestamp": "2026-09-06T17:33:00+00:00",
      "category": "constant",
      "key": "D",
      "value": "1024",
      "rationale": "HRR vector dimensionality, locked after empirical iteration",
      "session": "s1",
      "supersedes": null
    }
  ],
  "comparators": {}
}
```

Entry fields:

| field | meaning |
|---|---|
| `id` | integer, assigned sequentially, never reused |
| `category` | one of `constant`, `decision`, `goal`, `constraint`, `finding`, `scope` |
| `key` | stable identifier used to match entries across time. Two entries are only ever compared if they share the exact same key string. |
| `value` | stored as a string; the tool does no type coercion |
| `rationale` | free text |
| `session` | free-text tag, used only for grouping in `health` — `id` order is what's authoritative, not this |
| `supersedes` | id of the prior entry (same key) this one explicitly overrides, or `null` |

Top-level field beyond `project`/`created`/`next_id`/`entries`:

| field | meaning |
|---|---|
| `comparators` | `{key: comparator_name}`. Missing keys default to `"exact"`. Set via `log --comparator ...`; persists until changed. Ledgers from before this field existed simply lack it — `load()` doesn't require it to be present. |

## Comparator registry

Two built-in comparators, chosen explicitly per key — never inferred from a value's shape:

- **`exact`** (default): plain string inequality.
- **`numeric_range`**: parses each value as a bare number (`"1024"`, treated as a zero-width point) or a `low-high` range (`"0.12-0.17"`; a leading `-` is treated as a sign, so `"-10--5"` parses as the range (-10, -5)). Two values are compatible if their ranges **overlap at all**, inclusive — this is overlap, not containment: `"0.12-0.17"` and `"0.15-0.30"` count as compatible under this comparator, even though neither contains the other. `nan`/`inf` are rejected as non-numeric rather than silently compared. If either value doesn't parse as numeric or range-shaped, the comparator returns "could not evaluate," and the caller falls back to `exact` and records a warning — it will not guess.

**Comparator lookup is retroactive and unversioned.** `_find_contradictions` looks up whatever is *currently* registered for a key, every time it runs — not what was registered when each entry was logged. Changing a key's comparator with a later `log --comparator ...` call changes how that key's *entire* history is judged on the next `check`/`digest`/`show`/`stale`, not just entries logged afterward. This is a deliberate simplification (no per-entry comparator versioning), documented here rather than hidden.

## `build_entry()` — the one place entry-construction logic lives

`cmd_log` (the CLI), the hub adapter, and the MCP adapter all call the same `build_entry(data, category, key, value, ...)` function rather than each re-deriving "what makes an entry valid." It mutates `data` in place and returns the new entry; it does not save to disk. On invalid input it **raises `ValueError`**, never `sys.exit` — that distinction matters for any wrapper that stays alive across multiple calls (a server, a hub peer): `sys.exit` ends the whole interpreter it's called from, not just the one request. `cmd_log` is the only caller that turns that `ValueError` back into a `sys.exit`, for ordinary CLI UX.

`build_entry` takes an optional `warn(message: str)` callback for three non-fatal cases, and defaults to printing to stderr if none is given:
1. `supersedes` names a real entry for the right key, but not the *current active* one — recorded anyway, but won't close an open conflict.
2. A key's comparator is changing from one value to another — flagged as retroactive (see above).
3. A `numeric_range` comparison couldn't evaluate both sides — falls back to `exact`, and says so.

A caller that passes its own `warn` (both adapters do, collecting into a list) gets these back as structured data instead of losing them to a stderr no one is reading.

## Contradiction algorithm (exact)

Implemented in `_find_contradictions(entries, comparators)` → `(contradictions, warnings)`. Entries are walked in `id` order. Per key, the tool tracks the most recent (`active`) entry. When a new entry `e` arrives for a key with an existing active entry `prev`:

- if `e.supersedes == prev.id` — closes any open conflict for that key, even one opened several entries ago
- otherwise, run that key's comparator on `(prev.value, e.value)`:
  - compatible → no conflict, `active` just updates
  - incompatible → opens (or extends) a conflict
  - comparator returned "can't evaluate" → warning appended, falls back to `exact`

The **origin** of a reported conflict is the start of an unresolved chain, not just the immediately preceding entry — if a key drifts `v1 → v2 → v3` with no supersede, the report is `(v1, v3)`, not `(v2, v3)`, so the original disagreement doesn't disappear from the report just because a third value arrived.

## Commands

- `init <project> [--force]`
- `log --category C --key K --value V [--rationale R] [--session S] [--supersedes ID] [--comparator {exact,numeric_range}]`
- `check` — exit 1 if any unresolved contradiction exists
- `digest` — markdown primer, latest value per key, grouped by category, contradicted keys marked
- `health` — entry/key counts, contradiction count, per-session activity, scope-change count with a note if ≥3
- `show --key K` — full history for one key with per-entry conflict-open/resolve annotations; exit 1 if that key currently has an open conflict, exit 1 (with a message, via `sys.exit`) if the key doesn't exist at all
- `keys [--threshold 0.80]` — two-tier near-duplicate scan (below)
- `stale [--days 30] [--category C]` — flags keys whose *active* entry hasn't been touched recently, optionally scoped to one category; cross-references `check` so a stale-and-contradicted key is marked as both

### `keys`: two-tier near-duplicate detection

1. **Normalize** (casefold, strip whitespace/underscore/hyphen) and flag exact matches — catches `D`/`d`, `C_safe`/`c-safe` at 100% confidence, independent of `--threshold`.
2. **Fuzzy**: `difflib.SequenceMatcher` ratio on the normalized forms, flagged above `--threshold` — catches actual misspellings like `eta`/`etta`.

Default threshold is **0.80**, chosen empirically, not guessed: legitimate root-sharing pairs (`sigma`/`sigma_sq`, `rho`/`rho_c`) scored in the same 0.83–0.86 band as real one-letter typos (`eta`/`etta`, `alpha`/`alpah`) when tested. No fixed threshold cleanly separates the two groups — 0.80 was chosen to miss zero of the tested real typos, accepting that some legitimately-distinct root-sharing keys will surface and need a quick manual dismissal.

This is spelling-similarity, not meaning-similarity: `D` and `hrr_dim` mean the same thing and will not be caught.

## What this deliberately does not do

- **No semantic matching.** Two keys for the same underlying fact are invisible to this tool unless `keys` happens to catch them as spelling-similar.
- **No automatic extraction from conversation text.** An entry exists only because something explicitly called `build_entry`.
- **No per-entry comparator history.** Comparator changes are retroactive over a key's whole history (see above) — this is a real, documented tradeoff, not an oversight.

## Adapters

Two things sit on top of this same `ledger.py`, both reusing `build_entry` / `_find_contradictions` directly rather than re-deriving validation logic:

- **`mcp_adapter/`** — exposes `ledger_log` / `ledger_check` / `ledger_show` as MCP tools (`mcp==2.1.1`). Verified against the real package via `mcp.client._memory.InMemoryTransport` and a real `ClientSession` — real `initialize`/`tools/list`/`tools/call`, not a stub.
- **`hub_adapter/`** — exposes all eight commands as RPC actions on a small WebSocket hub (vendored `hub.py`/`tool_client.py`). This is the heavier of the two: it pulls in a separate, custom orchestration prototype whose only real advantage over MCP is peer-to-peer tool invocation without an LLM deciding each hop. Keep it only if that property is actually load-bearing for what you're building; otherwise the MCP adapter alone covers normal usage with far less to maintain.
