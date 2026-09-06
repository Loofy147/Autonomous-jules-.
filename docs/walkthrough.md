# Example walkthrough (actual output, captured from this exact package)

```
$ python3 ledger.py init "stratos-monorepo"
initialized ledger for 'stratos-monorepo' at ledger.json

$ python3 ledger.py log --category constant --key D --value 1024 \
    --rationale "HRR vector dimensionality, locked after empirical iteration" --session s1
logged #1 [constant] D = 1024

$ python3 ledger.py log --category constant --key D --value 512 \
    --rationale "re-derived during H-BPE tokenizer work, did not cross-check" --session s9
logged #2 [constant] D = 512

$ python3 ledger.py check
1 unresolved contradiction(s):

  key 'D':
    #1 (2026-09-06, session=s1) = '1024'  -- HRR vector dimensionality, locked after empirical iteration
    #2 (2026-09-06, session=s9) = '512'  -- re-derived during H-BPE tokenizer work, did not cross-check
    -> not resolved. Log a new entry with --supersedes 2 once you know which value is right.

(exit code 1)

$ python3 ledger.py log --category constant --key D --value 1024 \
    --rationale "confirmed 1024 correct; 512 in H-BPE was a different, mislabeled dimension" \
    --session s12 --supersedes 2
logged #3 [constant] D = 1024

$ python3 ledger.py check
no unresolved contradictions
(exit code 0)
```

## `show --key` — full history with conflict annotations

Note the flag form: `--key`, not a positional argument.

```
$ python3 ledger.py show --key D
key 'D' -- 3 entries, comparator=exact
status: clean

  #1 -- 2026-09-06 session=s1 [constant]
      value:     '1024'
      rationale: HRR vector dimensionality, locked after empirical iteration
  #2 -- 2026-09-06 session=s9 [constant]
      value:     '512'
      rationale: re-derived during H-BPE tokenizer work, did not cross-check
  #3 (active) -- 2026-09-06 session=s12 [constant]  [supersedes #2]
      value:     '1024'
      rationale: confirmed 1024 correct; 512 in H-BPE was a different, mislabeled dimension
```

## `numeric_range` comparator

```
$ python3 ledger.py log --category goal --key moaziz-scope \
    --value "backprop-free micro-agent architecture for ARC-AGI-3" --session s1
logged #4 [goal] moaziz-scope = backprop-free micro-agent architecture for ARC-AGI-3

$ python3 ledger.py log --category constant --key eta --value "0.12-0.17" \
    --rationale "learning rate range from convergence sweeps" --session s3 --comparator numeric_range
logged #5 [constant] eta = 0.12-0.17

$ python3 ledger.py log --category constant --key eta --value 0.15 \
    --rationale "specific value used in run 7" --session s10
logged #6 [constant] eta = 0.15
```

`0.15` falls inside `0.12-0.17`, so this does **not** open a conflict — confirmed by `digest` below showing `eta` with no ⚠ marker.

## `digest` — the primer for a fresh session

```
$ python3 ledger.py digest
# Context primer: stratos-monorepo
_generated 2026-09-06T17:33:57Z from 6 logged entries_

## Goals
- `moaziz-scope` = backprop-free micro-agent architecture for ARC-AGI-3

## Locked constants
- `D` = 1024 — confirmed 1024 correct; 512 in H-BPE was a different, mislabeled dimension
- `eta` = 0.15 — specific value used in run 7
```

This is meant to be pasted at the top of a new session as an anchor, instead of relying on memory or re-summarizing from scratch.

## Adapters: same data, two other transports

Both adapters below point at a ledger.json in their own working directory (not the one used above) and expose the same core actions — `log`, `check`, `show` at minimum. Full verified behavior (including the two real bugs this took to get right: a bare `dict` return annotation silently dropping MCP's `structuredContent`, and a stale-registration bug in the hub's peer registry) is documented in each adapter's own file and in `docs/schema.md`'s Adapters section — not repeated here to avoid the two copies drifting.

```
$ cd hub_adapter && python3 ledger_tool_demo.py     # needs: pip install websockets
$ cd mcp_adapter  && python3 test_mcp_real.py        # needs: pip install mcp==2.1.1 (clean venv recommended)
```
