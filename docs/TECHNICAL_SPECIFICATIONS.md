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
1. **Jules API Client (`JulesClient`)**: Handles authentication, request dispatching, rate limiting, status polling (`poll_task_until_complete`), task cancellation (`cancel_task`), listing tasks (`list_tasks`), and response parsing for Jules platform API endpoints.
2. **GitHub API Client (`GitHubClient`)**: Wraps REST interactions with GitHub API using Personal Access Tokens (PAT) or repository tokens for issues, pull requests, PR code reviews, workflow dispatch events, file content retrieval, and commit statuses (`create_commit_status`).
3. **Pipeline Runner (`PipelineRunner`)**: Coordinates task execution steps, workflow state tracking, artifact reporting, configurable step failure handling (`stop_on_failure` / `continue_on_failure`), and JSON/file configuration loading.
4. **Command Line Interface (`cli.py`)**: Entry point for developers and automated GitHub Actions runners supporting dry-run modes, custom output formats (JSON / formatted text), and argument parsing.

## 3. Data Models

### 3.1 Task Execution Config (`TaskConfig`)
- `task_id` (str): Unique identifier for a pipeline task.
- `action` (str): Action name (e.g., `run_agent`, `poll`, `cancel`, `github_comment`, `github_review`, `trigger_workflow`, `commit_status`, `get_file`).
- `params` (dict): Keyword parameters passed to target handler.
- `retry_count` (int): Max retry attempts for transient failures (default: 3).

### 3.2 Pipeline Result (`PipelineResult`)
- `status` (str): `SUCCESS`, `FAILED`, or `SKIPPED`.
- `execution_time` (float): Duration in seconds.
- `details` (dict): Detailed output from task steps.
- `errors` (list[str]): Error messages encountered during execution.

### 3.3 Pipeline Configuration (`PipelineConfig`)
- `name` (str): Pipeline execution name.
- `on_failure` (str): Failure execution policy (`stop_on_failure` or `continue_on_failure`).
- `steps` (list[TaskConfig]): Array of execution task configurations.

## 4. API Integration Specifications

### 4.1 Jules API
- **Base URL**: `https://api.jules.ai/v1` (or configured endpoint via `JULES_API_BASE_URL`)
- **Header**: `Authorization: Bearer <JULES_API_KEY>`
- **Core Operations**:
  - `get_status()`: Validates API connection and status.
  - `submit_task(payload: dict)`: Submits autonomous agent tasks.
  - `fetch_result(task_id: str)`: Polls or retrieves completion status.
  - `poll_task_until_complete(task_id: str, timeout: int, interval: int)`: Polls until terminal state.
  - `cancel_task(task_id: str)`: Cancels an in-progress agent task.
  - `list_tasks(limit: int)`: Retrieves listing of recent agent execution tasks.

### 4.2 GitHub REST API
- **Base URL**: `https://api.github.com`
- **Header**: `Authorization: Bearer <GITHUB_TOKEN>` / `Accept: application/vnd.github+json`
- **Core Operations**:
  - `get_user()`: Validates token authentication and current user profile.
  - `get_repo(owner: str, repo: str)`: Fetches repository metadata.
  - `get_file_content(owner: str, repo: str, path: str, ref: str)`: Fetches repository file content.
  - `create_issue(owner: str, repo: str, title: str, body: str)`: Creates a repository issue.
  - `create_issue_comment(owner: str, repo: str, issue_number: int, body: str)`: Posts status comments.
  - `get_pull_request(owner: str, repo: str, pull_number: int)`: Fetches pull request details.
  - `create_pull_request_review(owner: str, repo: str, pull_number: int, body: str, event: str)`: Creates structured code reviews (`APPROVE`, `REQUEST_CHANGES`, `COMMENT`).
  - `trigger_workflow_dispatch(owner: str, repo: str, workflow_id: str, ref: str, inputs: dict)`: Triggers workflow dispatch events.
  - `get_workflow_run(owner: str, repo: str, run_id: int)`: Fetches status of a workflow run.
  - `create_commit_status(owner: str, repo: str, sha: str, state: str, target_url: str, description: str, context: str)`: Sets status check on a commit.

## 5. Security & Credentials
- Credentials (`JULES_API_KEY`, `GITHUB_TOKEN`) must never be hardcoded or logged in plaintext.
- Read/Write repository permissions scope compliance as per GitHub PAT specifications.
- Environment variables are loaded dynamically with fallback defaults for sandbox testing.
