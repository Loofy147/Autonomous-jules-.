# Autonomous Jules

Autonomous agent runner and pipeline orchestration framework integrating Jules API with GitHub automated workflows.

## Overview
Autonomous Jules provides structured technical specifications, automated execution pipelines, GitHub Actions workflows, and operational guidance for running autonomous agents and managing GitHub workflows seamlessly.

## Documentation Index
- [System Architecture](docs/ARCHITECTURE.md)
- [Technical Specifications](docs/TECHNICAL_SPECIFICATIONS.md)
- [Pipelines and Workflows Guide](docs/PIPELINES_AND_WORKFLOWS.md)
- [Operational Guidance](docs/GUIDANCE.md)
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

### CLI Usage
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

## License
MIT
