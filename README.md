# Autonomous Jules

Autonomous agent runner and pipeline orchestration framework integrating Jules API with GitHub automated workflows and deterministic context decision ledgers.

## Overview
Autonomous Jules provides structured technical specifications, automated execution pipelines, GitHub Actions workflows, operational guidance, and a mechanical context decision ledger for running autonomous agents and managing multi-session agent states seamlessly.

## Documentation Index
- [System Architecture](docs/ARCHITECTURE.md)
- [Technical Specifications](docs/TECHNICAL_SPECIFICATIONS.md)
- [Pipelines and Workflows Guide](docs/PIPELINES_AND_WORKFLOWS.md)
- [Operational Guidance](docs/GUIDANCE.md)
- [Ledger Schema & Comparators](docs/schema.md)
- [Ledger End-to-End Walkthrough](docs/walkthrough.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## Quickstart

### Prerequisites
- Python 3.10+
- `pip`

### Local Setup
```bash
# Install package locally
pip install -e .

# Run test suite
python3 -m pytest
```

### CLI & Pipeline Usage
```bash
# Check connectivity status for Jules API & GitHub
autonomous-jules status

# Execute a single pipeline task
autonomous-jules run --action run_agent --param query="Initialize system check"

# Execute a declarative multi-step pipeline from a JSON file
autonomous-jules run --config-file pipeline.json --output-format json

# Run dry-run execution
autonomous-jules run --action run_agent --param query="System audit" --dry-run
```

## Context Decision Ledger System

The framework includes a mechanical file-based ledger (`ledger.py`) for tracking decisions, constants, goals, constraints, findings, and scope changes across long multi-session projects. Contradiction detection is purely deterministic (same key, incompatible value, no explicit supersede link).

### Pipeline Ledger Actions
- `ledger_init`: Initialize a project ledger file (`ledger.json`).
- `ledger_log`: Record an entry (`category`, `key`, `value`, `rationale`, `session`, `supersedes`, `comparator`).
- `ledger_check`: Perform deterministic contradiction detection (`fail_on_contradiction`).
- `ledger_digest`: Generate compressed context primer for session initialization.
- `ledger_health`: Summarize scope-creep and session activity stats.
- `ledger_show`: Display complete history for a specific key.
- `ledger_keys`: Scan for spelling-similar key naming drift.
- `ledger_stale`: Flag keys whose active values have not been updated within N days.

### Core CLI Quickstart
```bash
python3 ledger.py init "my-project"
python3 ledger.py log --category constant --key D --value 1024 --session s1
python3 ledger.py check          # exit code 1 if unresolved contradictions exist
python3 ledger.py digest         # paste this at the top of a fresh session
```

### Integration Adapters
- **MCP Adapter (`mcp_adapter/`)**: Exposes ledger tools over Model Context Protocol (`mcp==2.1.1`).
- **Hub Adapter (`hub_adapter/`)**: Exposes ledger operations over WebSocket RPC for peer-to-peer execution.

## Showcase & Examples

Run the end-to-end interactive showcase demonstration script to see Jules API Client, GitHub Client, Pipeline Runner, and CLI integration in action:

```bash
# Execute the full showcase demonstration
python3 examples/showcase_demo.py

# Run the declarative showcase pipeline configuration via CLI
autonomous-jules run --config-file examples/showcase_pipeline.json --dry-run
```

## License
MIT
