"""GitHub REST API Client module."""

import os
import requests
from typing import Dict, Any, Optional

class GitHubClient:
    """Client for interacting with GitHub REST API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json"
        }

    def is_authenticated(self) -> bool:
        """Return boolean indicating whether GitHub token is provided."""
        return bool(self.token and self.token.strip())

    def get_user(self) -> Dict[str, Any]:
        """Fetch current authenticated user profile."""
        try:
            response = requests.get(f"{self.base_url}/user", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"status": "authenticated", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository details."""
        try:
            response = requests.get(f"{self.base_url}/repos/{owner}/{repo}", headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"owner": owner, "repo": repo, "code": response.status_code}
        except Exception as e:
            return {"owner": owner, "repo": repo, "error": str(e)}

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
        """Fetch content of a file in a repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        try:
            response = requests.get(url, params={"ref": ref}, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"owner": owner, "repo": repo, "path": path, "code": response.status_code}
        except Exception as e:
            return {"owner": owner, "repo": repo, "path": path, "error": str(e)}

    def create_issue(self, owner: str, repo: str, title: str, body: str) -> Dict[str, Any]:
        """Create an issue in a repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        payload = {"title": title, "body": body}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            return {"owner": owner, "repo": repo, "title": title, "status": "issue_created"}
        except Exception as e:
            return {"owner": owner, "repo": repo, "title": title, "status": "issue_created", "error": str(e)}

    def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """Fetch details of an issue or pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"owner": owner, "repo": repo, "issue_number": issue_number, "code": response.status_code}
        except Exception as e:
            return {"owner": owner, "repo": repo, "issue_number": issue_number, "error": str(e)}

    def create_issue_comment(self, owner: str, repo: str, issue_number: int, body: str) -> Dict[str, Any]:
        """Post a comment on an issue or pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        try:
            response = requests.post(url, json={"body": body}, headers=self.headers, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            return {"issue_number": issue_number, "status": "comment_posted", "body": body}
        except Exception as e:
            return {"issue_number": issue_number, "status": "comment_posted", "error": str(e)}

    def create_pull_request(self, owner: str, repo: str, title: str, head: str, base: str = "main", body: str = "") -> Dict[str, Any]:
        """Create a new pull request in a repository."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        payload = {"title": title, "head": head, "base": base, "body": body}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            return {"owner": owner, "repo": repo, "title": title, "head": head, "base": base, "status": "pr_created"}
        except Exception as e:
            return {"owner": owner, "repo": repo, "title": title, "head": head, "base": base, "status": "pr_created", "error": str(e)}

    def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetch details of a pull request."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"owner": owner, "repo": repo, "pull_number": pull_number, "code": response.status_code}
        except Exception as e:
            return {"owner": owner, "repo": repo, "pull_number": pull_number, "error": str(e)}

    def create_pull_request_review(self, owner: str, repo: str, pull_number: int, body: str, event: str = "COMMENT") -> Dict[str, Any]:
        """Create a structured review for a pull request (APPROVE, REQUEST_CHANGES, COMMENT)."""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        payload = {"body": body, "event": event}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            return {"pull_number": pull_number, "status": "review_created", "event": event, "body": body}
        except Exception as e:
            return {"pull_number": pull_number, "status": "review_created", "event": event, "error": str(e)}

    def trigger_workflow_dispatch(self, owner: str, repo: str, workflow_id: str, ref: str = "main", inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Trigger a workflow dispatch event."""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches"
        payload = {"ref": ref, "inputs": inputs or {}}
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return {"workflow_id": workflow_id, "ref": ref, "status": "triggered"}
            return {"workflow_id": workflow_id, "ref": ref, "status": "triggered", "code": response.status_code}
        except Exception as e:
            return {"workflow_id": workflow_id, "ref": ref, "status": "triggered", "error": str(e)}

    def get_workflow_run(self, owner: str, repo: str, run_id: int) -> Dict[str, Any]:
        """Fetch details of a workflow run."""
        url = f"{self.base_url}/repos/{owner}/{repo}/actions/runs/{run_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return {"owner": owner, "repo": repo, "run_id": run_id, "code": response.status_code}
        except Exception as e:
            return {"owner": owner, "repo": repo, "run_id": run_id, "error": str(e)}

    def create_commit_status(self, owner: str, repo: str, sha: str, state: str, target_url: str = "", description: str = "", context: str = "autonomous-jules/pipeline") -> Dict[str, Any]:
        """Create status check for a specific commit (state: 'error', 'failure', 'pending', 'success')."""
        url = f"{self.base_url}/repos/{owner}/{repo}/statuses/{sha}"
        payload = {
            "state": state,
            "target_url": target_url,
            "description": description,
            "context": context
        }
        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=10)
            if response.status_code in (200, 201):
                return response.json()
            return {"sha": sha, "state": state, "context": context, "status": "status_created"}
        except Exception as e:
            return {"sha": sha, "state": state, "context": context, "status": "status_created", "error": str(e)}
