# Pipelines and Workflows Guide

## 1. Overview
This document describes the continuous integration, continuous deployment (CI/CD), and operational workflow execution pipelines implemented in the Autonomous Jules system.

## 2. Declarative Pipeline Configuration
Pipelines can be configured declaratively using JSON files or python dictionaries.

Example `pipeline_config.json`:
```json
{
  "name": "Full Agent Verification Pipeline",
  "on_failure": "stop_on_failure",
  "steps": [
    {
      "task_id": "step1",
      "action": "status"
    },
    {
      "task_id": "step2",
      "action": "run_agent",
      "params": {
        "prompt": "Run code security audit"
      }
    },
    {
      "task_id": "step3",
      "action": "commit_status",
      "params": {
        "owner": "myorg",
        "repo": "myrepo",
        "sha": "abc1234",
        "state": "success",
        "context": "autonomous-jules/security-audit",
        "description": "Security audit passed"
      }
    }
  ]
}
```

## 3. CI Pipeline (`.github/workflows/ci.yml`)
The CI pipeline runs automatically on pull requests and commits to main branches.

### Stages
1. **Lint & Formatting**: Validates python syntax and code structure.
2. **Unit & Integration Testing**: Runs `pytest` suite across supported Python environments (3.10, 3.11, 3.12).
3. **Build & Package Verification**: Ensures package build configurations (`pyproject.toml`) compile without errors.

## 4. Autonomous Execution Pipeline (`.github/workflows/pipeline.yml`)
The execution pipeline triggers automated Jules agent tasks and repo automation workflows.

### Triggers
- `workflow_dispatch`: Manual trigger via GitHub interface or GitHub API.
- `schedule`: Periodic cron trigger for routine maintenance/health checks.
- `issue_comment`: Optional trigger on repo issue commands.

### Execution Steps
1. Checkout repository with full history.
2. Setup Python environment (3.12+).
3. Install dependencies (`pip install -e .`).
4. Execute `autonomous-jules run --action ...` or `autonomous-jules run --config-file ...` CLI command using secrets (`JULES_API_KEY`, `GITHUB_TOKEN`).
5. Upload execution logs and task artifacts.

## 5. Error Handling & Recovery
- **Transient Network Retries**: Retries failed REST requests up to 3 times with exponential backoff.
- **Workflow Failures**: Emits structured log output and returns non-zero status code to fail CI jobs cleanly.
- **Dry Run Mode**: Supports `--dry-run` to simulate task execution without making live API requests.
