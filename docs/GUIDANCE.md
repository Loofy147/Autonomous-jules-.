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

# Run a pipeline task
autonomous-jules run --action run_agent --param query="Run diagnostics"

# Submit a structured review on a pull request
autonomous-jules run --action github_review --param owner=myorg --param repo=myrepo --param pull_number=42 --param body="LGTM" --param event=APPROVE

# Trigger a workflow dispatch
autonomous-jules run --action trigger_workflow --param owner=myorg --param repo=myrepo --param workflow_id=pipeline.yml
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
3. **Testing**: Run `pytest` locally before opening pull requests.
