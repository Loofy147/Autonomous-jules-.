"""Pipeline Orchestration and Runner module."""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from autonomous_jules.api_client import JulesClient
from autonomous_jules.github_client import GitHubClient


@dataclass
class TaskConfig:
    """Task Execution Configuration data model."""
    task_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 3


@dataclass
class PipelineResult:
    """Pipeline Result output data model."""
    status: str
    execution_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result dataclass to dictionary."""
        return {
            "status": self.status,
            "execution_time": self.execution_time,
            "details": self.details,
            "errors": self.errors,
        }


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

        elif action == "github_review":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            pull_number = int(params.get("pull_number", params.get("issue_number", 1)))
            body = params.get("body", "Autonomous Jules Structured Code Review")
            event = params.get("event", "COMMENT")
            review_res = self.github_client.create_pull_request_review(owner, repo, pull_number, body, event)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "review": review_res
            }

        elif action == "trigger_workflow":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            workflow_id = params.get("workflow_id", "pipeline.yml")
            ref = params.get("ref", "main")
            dispatch_res = self.github_client.trigger_workflow_dispatch(owner, repo, workflow_id, ref)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "dispatch": dispatch_res
            }

        else:
            return {
                "action": action,
                "status": "FAILED",
                "error": f"Unknown action: {action}",
                "duration": round(time.time() - start_time, 4)
            }
