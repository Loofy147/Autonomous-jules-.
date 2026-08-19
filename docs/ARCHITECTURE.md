# Autonomous Jules Architecture & System Design

## 1. Overview
`Autonomous Jules` is an open-source autonomous agent execution and orchestration framework. It bridges remote AI agent platforms (Jules API) with GitHub's developer ecosystem (GitHub REST API, GitHub Actions workflows, issues, pull requests, and commit statuses).

The framework provides determinism, observability, safety guardrails, state tracking, and failure resiliency for agent workflows running in CI/CD or standalone environments.

## 2. Core Architectural Pillars

```
+-------------------------------------------------------------------------+
|                              User / CLI                                 |
|                   `autonomous-jules` / GitHub Action                    |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         Pipeline Orchestrator                           |
|      (`PipelineRunner` - Multi-step runner, State Machine, Fail-safe)  |
+-------------------------------------------------------------------------+
                    /                               \
                   v                                 v
+------------------------------------+   +------------------------------------+
|            Jules Client            |   |           GitHub Client            |
|   (`JulesClient` - Tasks, Polling, |   |  (`GitHubClient` - Repos, PRs,      |
|     Retries, Exponential Backoff)  |   |    Issues, Workflow Dispatches)    |
+------------------------------------+   +------------------------------------+
                   |                                 |
                   v                                 v
+------------------------------------+   +------------------------------------+
|          Jules API Server          |   |          GitHub REST API           |
+------------------------------------+   +------------------------------------+
```

### 2.1 Decoupled API Adaptation
- **`JulesClient`**: Wraps external task submission, polling, retrieval, cancellation, and health checking endpoints. Implements exponential backoff and non-blocking retry mechanisms.
- **`GitHubClient`**: Manages interaction with GitHub's REST API, enabling agents to comment on issues, submit structured pull request code reviews, dispatch GitHub Actions workflows, set commit status checks, and read/write repository content.

### 2.2 Orchestration Engine (`PipelineRunner`)
- Manages sequential and parallel multi-step task execution.
- Evaluates step conditions and supports policy configurations:
  - `stop_on_failure`: Halts execution upon any step failure.
  - `continue_on_failure`: Logs step failure and proceeds to execution of subsequent steps.
- Formats step results into standard `PipelineResult` data models with duration tracking, status codes, and diagnostic metadata.

### 2.3 CLI & Infrastructure Integration
- Declarative invocation via CLI arguments or JSON/YAML pipeline configuration files.
- Supports dry-run execution (`--dry-run`) to validate workflow parameters before invoking external network APIs.
- Outputs machine-readable JSON or human-formatted summary text for GitHub Actions logs.

## 3. Safety Guardrails & Principles
1. **Secret Redaction**: Sensitive API tokens (`JULES_API_KEY`, `GITHUB_TOKEN`) are retrieved via environment variables and never exposed in logs or command outputs.
2. **Idempotency**: All API operations are designed to be rerun cleanly without side effects or duplicate resource pollution.
3. **Transient Failure Handling**: Network requests default to 3-tier exponential backoff retries for HTTP 5xx responses.
