# Technical Specifications

## 1. Executive Summary & Overview
The **Autonomous Jules** system is an automated agent runner and pipeline orchestration framework designed to integrate Jules API capabilities with GitHub automated workflows, repository management, and continuous execution.

## 2. System Architecture
```
+------------------+         +----------------------------+         +-------------------+
|  GitHub Actions  | ------> | Autonomous Jules Orchestrator| ------> |   Jules API /     |
|   / Workflows    |         |        (CLI / Pipeline)    |         | External Services |
+------------------+         +----------------------------+         +-------------------+
                                           |
                                           v
                             +----------------------------+
                             |   GitHub API / Repository  |
                             +----------------------------+
```

### Components
1. **Jules API Client (`JulesClient`)**: Handles authentication, request dispatching, rate limiting, and response parsing for Jules platform API endpoints.
2. **GitHub API Client (`GitHubClient`)**: Wraps REST interactions with GitHub API using Personal Access Tokens (PAT) or fine-grained repository tokens.
3. **Pipeline Runner (`PipelineRunner`)**: Coordinates task execution steps, workflow state tracking, artifact reporting, and retry logic.
4. **Command Line Interface (`cli.py`)**: Entry point for developers and automated GitHub Actions runners.

## 3. Data Models

### 3.1 Task Execution Config (`TaskConfig`)
- `task_id` (str): Unique identifier for a pipeline task.
- `action` (str): Action name (e.g., `run_agent`, `sync_repo`, `trigger_workflow`).
- `params` (dict): Keyword parameters passed to target handler.
- `retry_count` (int): Max retry attempts for transient failures (default: 3).

### 3.2 Pipeline Result (`PipelineResult`)
- `status` (str): `SUCCESS`, `FAILED`, or `SKIPPED`.
- `execution_time` (float): Duration in seconds.
- `details` (dict): Detailed output from task steps.
- `errors` (list[str]): Error messages encountered during execution.

## 4. API Integration Specifications

### 4.1 Jules API
- **Base URL**: `https://api.jules.ai/v1` (or configured endpoint)
- **Header**: `Authorization: Bearer <JULES_API_KEY>`
- **Core Operations**:
  - `get_status()`: Validates API connection and status.
  - `submit_task(payload: dict)`: Submits autonomous agent tasks.
  - `fetch_result(task_id: str)`: Polls or retrieves completion status.

### 4.2 GitHub REST API
- **Base URL**: `https://api.github.com`
- **Header**: `Authorization: Bearer <GITHUB_TOKEN>` / `Accept: application/vnd.github+json`
- **Core Operations**:
  - `get_repository(owner: str, repo: str)`: Fetches repository metadata.
  - `create_issue_comment(owner: str, repo: str, issue_number: int, body: str)`: Posts status comments.
  - `create_pull_request_review(owner: str, repo: str, pull_number: int, body: str, event: str)`: Creates structured code reviews (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).
  - `trigger_workflow_dispatch(owner: str, repo: str, workflow_id: str, ref: str, inputs: dict)`: Triggers GitHub Actions workflow events.

## 5. Security & Credentials
- Credentials (`JULES_API_KEY`, `GITHUB_TOKEN`) must never be hardcoded or logged in plaintext.
- Read/Write repository permissions scope compliance as per GitHub PAT specifications.
- Environment variables are loaded dynamically with fallback defaults for sandbox testing.
