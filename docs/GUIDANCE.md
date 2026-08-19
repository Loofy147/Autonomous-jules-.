# Operational Guidance & Best Practices

## 1. Quickstart Guide

### Environment Setup
Export environment variables before running the pipeline locally or in CI:

```bash
export JULES_API_KEY="<your_jules_api_key>"
export GITHUB_TOKEN="<your_github_token>"
```

### Installation
```bash
pip install -e .
```

### Execution Commands
```bash
# Check status of API connections
autonomous-jules status

# Run a pipeline task directly
autonomous-jules run --action run_agent --param query="Run diagnostics"

# Run a multi-step pipeline from configuration file
autonomous-jules run --config-file pipeline.json --output-format json

# Execute dry-run mode
autonomous-jules run --action run_agent --param query="Run diagnostics" --dry-run

# Poll a task until completion
autonomous-jules poll --task-id task_simulated_123 --timeout 30

# Cancel a task
autonomous-jules cancel --task-id task_simulated_123

# Set a GitHub commit status check
autonomous-jules commit-status --owner myorg --repo myrepo --sha HEAD --state success --context autonomous-jules/check
```

## 2. GitHub Credentials & Permissions
Ensure repository permissions match required access scopes:
- **Actions**: Read / Write
- **Code & Commit Statuses**: Read / Write
- **Pull Requests & Issues**: Read / Write
- **Workflows & Dependabot**: Read / Write

## 3. Best Practices
1. **Secret Security**: Never log environment tokens or API keys to standard output or log files.
2. **Idempotency**: Ensure pipeline actions are safe to rerun on failure.
3. **Dry-Run Validation**: Test pipeline configurations using `--dry-run` before applying changes in production repositories.
4. **Testing**: Run `python3 -m pytest` locally before opening pull requests.
