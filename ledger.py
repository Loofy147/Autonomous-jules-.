#!/usr/bin/env python3
"""
ledger.py - Adaptive Context Architect ledger tool

A file-based project ledger for tracking decisions, constants, goals, and
scope changes across long multi-session projects, with mechanical
contradiction detection (not vibes-based "metacognitive monitoring").

Design constraints this was built under:
- Claude's sandbox filesystem resets between tasks, and the memory system
  is a lossy summary. Anything that needs to survive across sessions has
  to be a plain file the user keeps in their own repo (e.g. the Stratos
  monorepo) and re-uploads or points Claude at each session.
- Contradiction detection here is purely mechanical: same key, different
  value under that key's registered comparator (exact string match by
  default), no explicit supersede link. It does not understand semantics.
  It will not catch a contradiction phrased in different words, and it
  WILL flag a false positive if you log the same fact with slightly
  different wording under a key using the default exact comparator.
  That's a real limitation, not a rounding error.

Storage: a single JSON file (default: ./ledger.json). Human-readable,
diffable, greppable, git-friendly.

Commands:
  init      Create a new ledger
  log       Append an entry (constant / decision / goal / constraint / finding / scope)
  check     Run contradiction detection, exit code 1 if unresolved contradictions exist
  digest    Print a compressed markdown primer to paste into a fresh session
  health    Print scope-creep / activity stats
  show      Print full history for a single key
  keys      Scan all keys for near-duplicates (difflib) -- catches key-naming drift
  stale     Flag keys whose active value hasn't been touched in N days
"""

import argparse
import difflib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = {"constant", "decision", "goal", "constraint", "finding", "scope"}

# ---------------------------------------------------------------------------
# Comparator registry
#
# A comparator decides whether two values logged under the same key count
# as "the same fact" for contradiction-detection purposes. Registered per
# key via `log --comparator ...`; default is "exact" for every key that
# never had one set, so existing ledgers and existing behavior are
# unchanged unless a comparator is explicitly registered.
#
# The lookup is done fresh every time `_find_contradictions` runs, using
# whatever is CURRENTLY registered for that key -- it is not versioned by
# entry id. That means changing a key's comparator is retroactive: it
# changes how that key's entire history is judged, not just entries
# logged after the change. This is a deliberate simplification (no
# per-entry comparator versioning) and is documented, not hidden.
#
# Each comparator is a function (a, b) -> True | False | None:
#   True  - values are compatible, not a contradiction
#   False - values conflict
#   None  - could not be evaluated (e.g. numeric_range against a
#           non-numeric string); caller falls back to exact string
#           comparison and records a warning instead of failing silently
#           or guessing.
# ---------------------------------------------------------------------------

_RANGE_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*-\s*(-?\d+(?:\.\d+)?)$")


def _parse_numeric(value):
    """Parse a value as a single point or a 'low-high' range.
    Returns (low, high) floats, or None if it's neither.
    A bare number is treated as a zero-width point (low == high)."""
    try:
        v = float(value)
        if v != v or v in (float("inf"), float("-inf")):
            return None  # nan/inf are valid floats but not meaningful
            # "points" here; letting them through silently (found via
            # test) would make 'inf'/'nan' values compare in ways no one
            # logging them would actually expect
        return (v, v)
    except (TypeError, ValueError):
        pass
    m = _RANGE_RE.match(value.strip()) if isinstance(value, str) else None
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2))
    return (min(a, b), max(a, b))


def _cmp_exact(a, b):
    return a == b


def _cmp_numeric_range(a, b):
    pa, pb = _parse_numeric(a), _parse_numeric(b)
    if pa is None or pb is None:
        return None
    return not (pa[1] < pb[0] or pb[1] < pa[0])  # ranges overlap, inclusive


COMPARATORS = {
    "exact": _cmp_exact,
    "numeric_range": _cmp_numeric_range,
}


def load(path: Path) -> dict:
    if not path.exists():
        sys.exit(f"error: no ledger at {path}. Run `init` first.")
    with open(path) as f:
        return json.load(f)


def save(path: Path, data: dict) -> None:
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def cmd_init(args):
    path = Path(args.path)
    if path.exists() and not args.force:
        sys.exit(f"error: {path} already exists. Use --force to overwrite.")
    data = {
        "project": args.project,
        "created": datetime.now(timezone.utc).isoformat(),
        "next_id": 1,
        "entries": [],
        "comparators": {},
    }
    save(path, data)
    print(f"initialized ledger for '{args.project}' at {path}")


def build_entry(data, category, key, value, rationale="", session="",
                 supersedes=None, comparator=None, warn=None):
    """
    Pure entry-construction logic, factored out of cmd_log so there is
    exactly one implementation shared by the CLI and any wrapper (MCP
    server, hub tool, etc.) instead of two copies that can silently
    drift apart.

    Mutates `data` in place (appends the entry, bumps next_id, updates
    data['comparators'] if `comparator` is given) and returns the new
    entry dict. Does NOT save to disk -- the caller owns that, same
    split as load/save already have.

    Raises ValueError -- never sys.exit -- on invalid input, specifically
    so this is safe to call from inside a long-running server's request
    handler. sys.exit ends the whole interpreter it's called from; a
    request handler that let that escape wouldn't just fail one request,
    it would take the request-serving loop down with it. This was found
    empirically, not assumed: an unguarded ledger.cmd_check() call
    against a missing path (cmd_check calls load(), which does
    sys.exit-on-missing-file, since it's the argparse-CLI entry point)
    escaped a bare `except Exception` inside a prototype tool-hub's
    invoke handler -- SystemExit is not an Exception subclass -- and
    wedged the whole demo process rather than failing just that one
    call. cmd_log (the CLI path) still gets to keep sys.exit-on-error
    UX; it just produces it itself now, by catching the ValueError this
    raises.

    `warn(message: str)` is called for non-fatal warnings (supersedes
    naming a non-active entry; comparator changing retroactively) --
    defaults to the CLI's existing stderr-print behavior if not given,
    so a caller that doesn't pass one still sees them rather than losing
    them silently.
    """
    if warn is None:
        warn = lambda w: print(w, file=sys.stderr)

    if category not in CATEGORIES:
        raise ValueError(f"category must be one of {sorted(CATEGORIES)}")

    if supersedes is not None:
        by_id = {e["id"]: e for e in data["entries"]}
        target = by_id.get(supersedes)
        if target is None:
            raise ValueError(f"supersedes id {supersedes} does not exist")
        if target["key"] != key:
            raise ValueError(
                f"#{supersedes} has key '{target['key']}', not '{key}' -- "
                f"supersedes must reference an entry with the same key"
            )
        same_key = [e for e in data["entries"] if e["key"] == key]
        active = max(same_key, key=lambda e: e["id"]) if same_key else None
        if active is not None and active["id"] != supersedes:
            warn(
                f"warning: #{supersedes} is not the current active entry "
                f"for key '{key}' (current active is #{active['id']}). "
                f"This will NOT close an existing conflict on '{key}' -- "
                f"only superseding the active entry (#{active['id']}) "
                f"does that. Recorded anyway, for the history."
            )

    if comparator is not None:
        if comparator not in COMPARATORS:
            raise ValueError(f"comparator must be one of {sorted(COMPARATORS)}")
        data.setdefault("comparators", {})
        existing = data["comparators"].get(key)
        if existing is not None and existing != comparator:
            warn(
                f"warning: key '{key}' comparator is changing from "
                f"'{existing}' to '{comparator}'. This is retroactive -- "
                f"it changes how this key's ENTIRE history is judged on "
                f"the next check/digest/health/show/stale, not just "
                f"entries logged from now on."
            )
        data["comparators"][key] = comparator

    entry = {
        "id": data["next_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "key": key,
        "value": value,
        "rationale": rationale or "",
        "session": session or "",
        "supersedes": supersedes,
    }
    data["entries"].append(entry)
    data["next_id"] += 1
    return entry


def cmd_log(args):
    path = Path(args.path)
    data = load(path)
    try:
        entry = build_entry(
            data, category=args.category, key=args.key, value=args.value,
            rationale=args.rationale, session=args.session,
            supersedes=args.supersedes, comparator=args.comparator,
            warn=lambda w: print(w, file=sys.stderr),
        )
    except ValueError as e:
        sys.exit(f"error: {e}")
    save(path, data)
    print(f"logged #{entry['id']} [{entry['category']}] {entry['key']} = {entry['value']}")




def _find_contradictions(entries, comparators=None):
    """
    Mechanical rule: walk entries in id order. For each key, track the
    current 'active' entry and whether that key currently has an
    unresolved conflict. A new entry for the same key with an
    incompatible value (per that key's comparator) opens a conflict
    UNLESS it explicitly supersedes the active (most recent) entry for
    that key, which clears it. Resolution is a state change, not a
    one-off event -- once cleared, the key goes back to clean, even
    though the old conflicting entries stay in the log for history.

    "Incompatible" is decided by the key's registered comparator (see
    COMPARATORS), defaulting to "exact" (plain string inequality) if the
    key has none registered -- see the module-level comment above the
    registry for the retroactive-lookup caveat. If a comparator can't
    evaluate a pair, the pair falls back to exact string comparison and a
    human-readable string is appended to the returned warnings list
    rather than failing silently.

    Two further subtleties, both confirmed by test runs and fixed here:

    1. Supersede-match is checked BEFORE the value-equality gate. Under
       the original ordering, re-affirming the current active value
       (e.value == prev.value) with a correct --supersedes never reached
       the resolution branch at all, so a pending conflict could never
       be closed by "yes, the current value is right" -- only by logging
       a *different* value. That's backwards from how people actually
       resolve these.
    2. The 'earlier' side of a reported pair is the ORIGIN of the
       unresolved chain, not just the immediately preceding entry. If a
       key drifts across three or more unsuperseded values in a row
       (v1 -> v2 -> v3), the origin (v1) would otherwise disappear from
       the report the moment v3 is logged, even though it was never
       reconciled with anything.

    Returns (contradictions, warnings):
      contradictions -- list of (origin_entry, latest_entry) still-unresolved pairs
      warnings       -- list of human-readable strings for comparator eval failures
    """
    comparators = comparators or {}
    active_by_key = {}
    pending_by_key = {}  # key -> (origin_entry, latest_entry) currently unresolved
    warnings = []
    for e in sorted(entries, key=lambda x: x["id"]):
        key = e["key"]
        prev = active_by_key.get(key)
        if prev is not None:
            if e["supersedes"] == prev["id"]:
                pending_by_key.pop(key, None)  # explicitly resolved
            else:
                cmp_name = comparators.get(key, "exact")
                cmp_fn = COMPARATORS.get(cmp_name, _cmp_exact)
                same = cmp_fn(prev["value"], e["value"])
                if same is None:
                    warnings.append(
                        f"key '{key}': comparator '{cmp_name}' could not evaluate "
                        f"#{prev['id']}={prev['value']!r} vs #{e['id']}={e['value']!r} "
                        f"-- fell back to exact string match"
                    )
                    same = _cmp_exact(prev["value"], e["value"])
                if not same:
                    origin, _ = pending_by_key.get(key, (prev, None))
                    pending_by_key[key] = (origin, e)
                # else: compatible per comparator -- leaves any existing
                # pending state untouched (not a resolution, not a new
                # divergence)
        active_by_key[key] = e
    return list(pending_by_key.values()), warnings


def cmd_check(args):
    path = Path(args.path)
    data = load(path)
    contradictions, warnings = _find_contradictions(data["entries"], data.get("comparators", {}))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if not contradictions:
        print("no unresolved contradictions")
        return 0
    print(f"{len(contradictions)} unresolved contradiction(s):\n")
    for prev, cur in contradictions:
        print(f"  key '{cur['key']}':")
        print(f"    #{prev['id']} ({prev['timestamp'][:10]}, session={prev['session'] or '?'}) = {prev['value']!r}  -- {prev['rationale']}")
        print(f"    #{cur['id']} ({cur['timestamp'][:10]}, session={cur['session'] or '?'}) = {cur['value']!r}  -- {cur['rationale']}")
        print(f"    -> not resolved. Log a new entry with --supersedes {cur['id']} once you know which value is right.\n")
    return 1



def get_digest(path: Path) -> dict:
    data = load(path)
    entries = sorted(data.get("entries", []), key=lambda x: x["id"])
    contradictions, warnings = _find_contradictions(entries, data.get("comparators", {}))
    contradicted_keys = {c[1]["key"] for c in contradictions}

    latest = {}
    for e in entries:
        latest[e["key"]] = e

    by_cat = {}
    for e in latest.values():
        by_cat.setdefault(e["category"], []).append(e)

    lines = []
    lines.append(f"# Context primer: {data['project']}")
    lines.append(f"_generated {datetime.now(timezone.utc).isoformat()[:19]}Z from {len(entries)} logged entries_\n")

    if contradictions:
        lines.append(f"## ⚠ {len(contradictions)} unresolved contradiction(s) — resolve before trusting these values")
        for prev, cur in contradictions:
            lines.append(f"- **{cur['key']}**: #{prev['id']}={prev['value']!r} vs #{cur['id']}={cur['value']!r} (unresolved)")
        lines.append("")

    cat_order = ["goal", "constraint", "constant", "decision", "finding", "scope"]
    cat_titles = {
        "goal": "Goals",
        "constraint": "Constraints",
        "constant": "Locked constants",
        "decision": "Decisions",
        "finding": "Findings",
        "scope": "Scope changes",
    }
    for cat in cat_order:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat_titles[cat]}")
        for e in sorted(by_cat[cat], key=lambda x: x["id"]):
            flag = " ⚠" if e["key"] in contradicted_keys else ""
            rationale = f" — {e['rationale']}" if e["rationale"] else ""
            lines.append(f"- `{e['key']}` = {e['value']}{flag}{rationale}")
        lines.append("")

    markdown = "\n".join(lines)
    return {
        "ok": True,
        "project": data.get("project", ""),
        "total_entries": len(entries),
        "contradictions_count": len(contradictions),
        "contradictions": [
            {
                "key": cur["key"],
                "origin_id": prev["id"],
                "origin_value": prev["value"],
                "latest_id": cur["id"],
                "latest_value": cur["value"],
            }
            for prev, cur in contradictions
        ],
        "warnings": warnings,
        "latest_entries": latest,
        "markdown": markdown
    }


def get_health(path: Path) -> dict:
    data = load(path)
    entries = data.get("entries", [])
    if not entries:
        return {
            "ok": True,
            "project": data.get("project", ""),
            "total_entries": 0,
            "distinct_keys": 0,
            "unresolved_contradictions": 0,
            "scope_entries": 0,
            "sessions": {},
            "warnings": []
        }
    contradictions, warnings = _find_contradictions(entries, data.get("comparators", {}))
    by_session = {}
    for e in entries:
        s = e["session"] or "(untagged)"
        by_session.setdefault(s, []).append(e)

    scope_entries = [e for e in entries if e["category"] == "scope"]
    keys = {e["key"] for e in entries}
    comparators = data.get("comparators", {})

    session_stats = {}
    for s, es in sorted(by_session.items()):
        scope_ct = sum(1 for e in es if e["category"] == "scope")
        session_stats[s] = {"total": len(es), "scope_changes": scope_ct}

    return {
        "ok": True,
        "project": data.get("project", ""),
        "total_entries": len(entries),
        "distinct_keys": len(keys),
        "unresolved_contradictions": len(contradictions),
        "scope_entries": len(scope_entries),
        "sessions_count": len(by_session),
        "session_stats": session_stats,
        "comparators_count": len(comparators),
        "comparators": list(comparators.keys()),
        "warnings": warnings
    }


def get_keys(path: Path, threshold: float = 0.80) -> dict:
    data = load(path)
    keys = sorted({e["key"] for e in data.get("entries", [])})
    if len(keys) < 2:
        return {
            "ok": True,
            "distinct_keys": len(keys),
            "exact_duplicates": [],
            "fuzzy_similar": []
        }

    norm = {k: _normalize_key(k) for k in keys}
    exact_dupes, fuzzy = [], []
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            if norm[k1] == norm[k2]:
                exact_dupes.append((k1, k2))
                continue
            ratio = difflib.SequenceMatcher(None, norm[k1], norm[k2]).ratio()
            if ratio >= threshold:
                fuzzy.append((k1, k2, round(ratio, 4)))
    fuzzy.sort(key=lambda x: -x[2])

    return {
        "ok": True,
        "distinct_keys": len(keys),
        "exact_duplicates": [{"key1": k1, "key2": k2} for k1, k2 in exact_dupes],
        "fuzzy_similar": [{"key1": k1, "key2": k2, "ratio": ratio} for k1, k2, ratio in fuzzy]
    }


def get_stale(path: Path, days: float = 30, category: str = None) -> dict:
    data = load(path)
    entries = data.get("entries", [])
    if not entries:
        return {
            "ok": True,
            "checked_keys": 0,
            "days": days,
            "stale_keys": [],
            "warnings": []
        }

    latest = {}
    for e in sorted(entries, key=lambda x: x["id"]):
        if category and e["category"] != category:
            continue
        latest[e["key"]] = e

    if not latest:
        return {
            "ok": True,
            "checked_keys": 0,
            "days": days,
            "stale_keys": [],
            "warnings": []
        }

    contradictions, warnings = _find_contradictions(entries, data.get("comparators", {}))
    contradicted_keys = {c[1]["key"] for c in contradictions}

    now = datetime.now(timezone.utc)
    stale = []
    for key, e in latest.items():
        try:
            ts = datetime.fromisoformat(e["timestamp"])
        except ValueError:
            warnings.append(f"key '{key}' has an unparseable timestamp, skipped")
            continue
        age_days = (now - ts).total_seconds() / 86400.0
        if age_days >= days:
            stale.append({
                "key": e["key"],
                "category": e["category"],
                "value": e["value"],
                "age_days": round(age_days, 1),
                "id": e["id"],
                "timestamp": e["timestamp"],
                "session": e["session"],
                "is_contradicted": e["key"] in contradicted_keys
            })
    stale.sort(key=lambda x: -x["age_days"])

    return {
        "ok": True,
        "checked_keys": len(latest),
        "days": days,
        "stale_keys": stale,
        "warnings": warnings
    }

def cmd_digest(args):
    path = Path(args.path)
    res = get_digest(path)
    for w in res.get("warnings", []):
        print(f"warning: {w}", file=sys.stderr)
    print(res["markdown"])
    return 0


def cmd_health(args):
    path = Path(args.path)
    res = get_health(path)
    if res["total_entries"] == 0:
        print("ledger is empty")
        return 0
    for w in res.get("warnings", []):
        print(f"warning: {w}", file=sys.stderr)

    print(f"project:              {res['project']}")
    print(f"total entries:        {res['total_entries']}")
    print(f"distinct keys:        {res['distinct_keys']}")
    print(f"unresolved contradictions: {res['unresolved_contradictions']}")
    print(f"scope-change entries: {res['scope_entries']}")
    print(f"sessions tagged:      {res['sessions_count']}")
    if res["comparators"]:
        print(f"keys with non-default comparator: {res['comparators_count']} ({', '.join(sorted(res['comparators']))})")
    print()
    print("entries per session:")
    for s, stats in sorted(res["session_stats"].items()):
        scope_ct = stats["scope_changes"]
        marker = f"  <- {scope_ct} scope change(s)" if scope_ct else ""
        print(f"  {s}: {stats['total']}{marker}")

    if res["scope_entries"] >= 3:
        print()
        print(f"note: {res['scope_entries']} scope-change entries logged total. "
              f"If most of these are recent, that's a real signal worth naming "
              f"to the user, not something to smooth over.")
    return 0


def cmd_show(args):
    path = Path(args.path)
    data = load(path)
    key = args.key
    entries = sorted((e for e in data["entries"] if e["key"] == key), key=lambda x: x["id"])
    if not entries:
        sys.exit(f"error: no entries found for key '{key}'")

    contradictions, warnings = _find_contradictions(data["entries"], data.get("comparators", {}))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    contradicted_keys = {c[1]["key"] for c in contradictions}
    comparator = data.get("comparators", {}).get(key, "exact")
    active = entries[-1]

    plural = "entry" if len(entries) == 1 else "entries"
    print(f"key '{key}' -- {len(entries)} {plural}, comparator={comparator}")
    print(f"status: {'UNRESOLVED CONTRADICTION' if key in contradicted_keys else 'clean'}")
    print()
    for e in entries:
        marker = " (active)" if e["id"] == active["id"] else ""
        sup = f"  [supersedes #{e['supersedes']}]" if e["supersedes"] is not None else ""
        print(f"  #{e['id']}{marker} -- {e['timestamp'][:10]} session={e['session'] or '?'} [{e['category']}]{sup}")
        print(f"      value:     {e['value']!r}")
        if e["rationale"]:
            print(f"      rationale: {e['rationale']}")
    return 1 if key in contradicted_keys else 0


def _normalize_key(k):
    """Fold away the cheapest sources of accidental key drift: case,
    and whitespace/underscore/hyphen variation. Does NOT touch actual
    spelling -- 'D' and 'hrr_dim' still normalize to different strings,
    by design; that gap is what the fuzzy (difflib) tier is for, and even
    that tier is spelling-similarity, not meaning-similarity."""
    return re.sub(r"[\s_-]+", "", k.strip().lower())


def cmd_keys(args):
    path = Path(args.path)
    res = get_keys(path, threshold=args.threshold)
    print(f"{res['distinct_keys']} distinct key(s)")
    if res['distinct_keys'] < 2:
        print("nothing to compare")
        return 0

    exact_dupes = res["exact_duplicates"]
    fuzzy = res["fuzzy_similar"]

    if not exact_dupes and not fuzzy:
        print("no near-duplicate keys found")
        return 0

    if exact_dupes:
        print(f"\n{len(exact_dupes)} pair(s) identical once case/spaces/underscores/hyphens "
              f"are stripped -- almost certainly the same fact under two spellings:")
        for pair in exact_dupes:
            print(f"  '{pair['key1']}'  <->  '{pair['key2']}'")

    if fuzzy:
        print(f"\n{len(fuzzy)} pair(s) similar but not identical (threshold={args.threshold}):")
        for item in fuzzy:
            print(f"  {item['ratio']:.2f}  '{item['key1']}'  <->  '{item['key2']}'")

    print("\nnote: spelling-similarity heuristic, not semantic understanding -- "
          "'D' and 'hrr_dim' mean the same thing and will NOT be caught; short "
          "unrelated keys can collide by chance. Review every pair by hand.")
    return 1


def cmd_stale(args):
    path = Path(args.path)
    res = get_stale(path, days=args.days, category=args.category)
    for w in res.get("warnings", []):
        print(f"warning: {w}", file=sys.stderr)

    if res["checked_keys"] == 0:
        scope = f" in category '{args.category}'" if args.category else ""
        print(f"no entries{scope}")
        return 0

    scope_note = f" in category '{args.category}'" if args.category else ""
    print(f"{res['checked_keys']} key(s) checked{scope_note}, staleness threshold = {args.days} day(s)")

    stale_keys = res["stale_keys"]
    if not stale_keys:
        print("no stale keys")
        return 0

    print(f"\n{len(stale_keys)} stale key(s):\n")
    for item in stale_keys:
        flag = "  ⚠ also has an unresolved contradiction" if item["is_contradicted"] else ""
        print(f"  '{item['key']}' [{item['category']}] = {item['value']!r} -- {item['age_days']:.1f}d old "
              f"(#{item['id']}, {item['timestamp'][:10]}, session={item['session'] or '?'}){flag}")
    return 1


def main():
    p = argparse.ArgumentParser(description="Adaptive Context Architect ledger")
    p.add_argument("--path", default="ledger.json", help="path to ledger JSON file")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="create a new ledger")
    sp.add_argument("project")
    sp.add_argument("--force", action="store_true")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("log", help="append an entry")
    sp.add_argument("--category", required=True, choices=sorted(CATEGORIES))
    sp.add_argument("--key", required=True)
    sp.add_argument("--value", required=True)
    sp.add_argument("--rationale", default="")
    sp.add_argument("--session", default="")
    sp.add_argument("--supersedes", type=int, default=None)
    sp.add_argument(
        "--comparator", choices=sorted(COMPARATORS), default=None,
        help="register how this key's values are compared for contradiction "
             "detection (default if never set: exact). Retroactive: applies "
             "to the key's whole history on the next check/digest/etc, not "
             "just entries logged after this."
    )
    sp.set_defaults(func=cmd_log)

    sp = sub.add_parser("check", help="detect unresolved contradictions")
    sp.set_defaults(func=cmd_check)

    sp = sub.add_parser("digest", help="print a compressed markdown context primer")
    sp.set_defaults(func=cmd_digest)

    sp = sub.add_parser("health", help="print scope-creep / activity stats")
    sp.set_defaults(func=cmd_health)

    sp = sub.add_parser("show", help="print full history for a single key")
    sp.add_argument("--key", required=True)
    sp.set_defaults(func=cmd_show)

    sp = sub.add_parser("keys", help="scan all keys for near-duplicates (difflib)")
    sp.add_argument(
        "--threshold", type=float, default=0.80,
        help="difflib similarity ratio in [0,1] above which a pair is "
             "flagged as fuzzy-similar (default: 0.80, chosen empirically -- "
             "see cmd_keys docstring for the tradeoff this can't fully "
             "resolve). Exact matches after case/separator normalization "
             "are always flagged regardless of this value."
    )
    sp.set_defaults(func=cmd_keys)

    sp = sub.add_parser("stale", help="flag keys whose active value is older than N days")
    sp.add_argument("--days", type=float, default=30, help="age threshold in days (default: 30)")
    sp.add_argument("--category", choices=sorted(CATEGORIES), default=None)
    sp.set_defaults(func=cmd_stale)

    args = p.parse_args()
    rc = args.func(args)
    sys.exit(rc if isinstance(rc, int) else 0)


if __name__ == "__main__":
    main()
