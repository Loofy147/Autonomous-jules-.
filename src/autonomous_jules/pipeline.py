"""Pipeline Orchestration and Runner module."""

import time
from typing import Dict, Any, Optional
from autonomous_jules.api_client import JulesClient
from autonomous_jules.github_client import GitHubClient

class PipelineRunner:
    """Orchestrates multi-step workflow actions."""

    def __init__(self, jules_client: Optional[JulesClient] = None, github_client: Optional[GitHubClient] = None):
        self.jules_client = jules_client or JulesClient()
        self.github_client = github_client or GitHubClient()

    def run_step(self, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a single workflow step."""
        params = params or {}
        start_time = time.time()

        if action == "status":
            jules_status = self.jules_client.get_status()
            github_status = self.github_client.get_user()
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "jules": jules_status,
                "github": github_status
            }

        elif action == "run_agent":
            task_res = self.jules_client.submit_task(params)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "task": task_res
            }

        elif action == "github_comment":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            issue_number = int(params.get("issue_number", 1))
            body = params.get("body", "Autonomous Jules Pipeline Notification")
            comment_res = self.github_client.create_issue_comment(owner, repo, issue_number, body)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "comment": comment_res
            }

        else:
            return {
                "action": action,
                "status": "FAILED",
                "error": f"Unknown action: {action}",
                "duration": round(time.time() - start_time, 4)
            }
