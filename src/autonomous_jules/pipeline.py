"""Pipeline Orchestration and Runner module."""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Union
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
class PipelineConfig:
    """Pipeline Configuration data model."""
    name: str = "Autonomous Jules Pipeline"
    on_failure: str = "stop_on_failure"  # "stop_on_failure" or "continue_on_failure"
    steps: List[TaskConfig] = field(default_factory=list)


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
    """Orchestrates single-step and multi-step workflow actions."""

    def __init__(self, jules_client: Optional[JulesClient] = None, github_client: Optional[GitHubClient] = None):
        self.jules_client = jules_client or JulesClient()
        self.github_client = github_client or GitHubClient()

    def run_step(self, action: str, params: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a single workflow step."""
        params = params or {}
        start_time = time.time()

        if dry_run:
            return {
                "action": action,
                "status": "SUCCESS",
                "dry_run": True,
                "duration": round(time.time() - start_time, 4),
                "params": params
            }

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

        elif action == "poll":
            task_id = params.get("task_id", "task_simulated_123")
            timeout = int(params.get("timeout", 60))
            poll_res = self.jules_client.poll_task_until_complete(task_id, timeout=timeout)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "task": poll_res
            }

        elif action == "cancel":
            task_id = params.get("task_id", "task_simulated_123")
            cancel_res = self.jules_client.cancel_task(task_id)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "cancel": cancel_res
            }

        elif action == "list_tasks":
            limit = int(params.get("limit", 10))
            list_res = self.jules_client.list_tasks(limit=limit)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "tasks": list_res
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

        elif action in ("commit_status", "create_commit_status"):
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            sha = params.get("sha", "HEAD")
            state = params.get("state", "success")
            description = params.get("description", "Pipeline status check")
            context = params.get("context", "autonomous-jules/pipeline")
            target_url = params.get("target_url", "")
            status_res = self.github_client.create_commit_status(owner, repo, sha, state, target_url, description, context)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "commit_status": status_res
            }

        elif action == "get_file":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            path = params.get("path", "README.md")
            ref = params.get("ref", "main")
            file_res = self.github_client.get_file_content(owner, repo, path, ref)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "file": file_res
            }

        elif action == "create_issue":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            title = params.get("title", "Autonomous Jules Pipeline Issue")
            body = params.get("body", "Issue created automatically by pipeline execution.")
            issue_res = self.github_client.create_issue(owner, repo, title, body)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "issue": issue_res
            }

        else:
            return {
                "action": action,
                "status": "FAILED",
                "error": f"Unknown action: {action}",
                "duration": round(time.time() - start_time, 4)
            }

    def run_pipeline(self, pipeline_config: Union[PipelineConfig, Dict[str, Any], str], dry_run: bool = False) -> PipelineResult:
        """Run a multi-step pipeline specified by PipelineConfig, dict, or JSON file path."""
        start_time = time.time()
        errors: List[str] = []
        step_results: List[Dict[str, Any]] = []

        if isinstance(pipeline_config, str):
            with open(pipeline_config, "r", encoding="utf-8") as f:
                data = json.load(f)
            config = self._dict_to_config(data)
        elif isinstance(pipeline_config, dict):
            config = self._dict_to_config(pipeline_config)
        else:
            config = pipeline_config

        pipeline_status = "SUCCESS"

        for task_cfg in config.steps:
            res = self.run_step(task_cfg.action, task_cfg.params, dry_run=dry_run)
            step_results.append({
                "task_id": task_cfg.task_id,
                "action": task_cfg.action,
                "result": res
            })

            if res.get("status") == "FAILED":
                errors.append(f"Step '{task_cfg.task_id}' ({task_cfg.action}) failed: {res.get('error')}")
                pipeline_status = "FAILED"
                if config.on_failure == "stop_on_failure":
                    break

        duration = round(time.time() - start_time, 4)
        return PipelineResult(
            status=pipeline_status,
            execution_time=duration,
            details={
                "pipeline_name": config.name,
                "on_failure": config.on_failure,
                "steps": step_results
            },
            errors=errors
        )

    def _dict_to_config(self, data: Dict[str, Any]) -> PipelineConfig:
        """Convert dictionary to PipelineConfig model."""
        name = data.get("name", "Autonomous Jules Pipeline")
        on_failure = data.get("on_failure", "stop_on_failure")
        steps_raw = data.get("steps", [])

        steps = []
        for idx, s in enumerate(steps_raw):
            task_id = s.get("task_id", f"step_{idx+1}")
            action = s.get("action", "status")
            params = s.get("params", {})
            retry_count = int(s.get("retry_count", 3))
            steps.append(TaskConfig(task_id=task_id, action=action, params=params, retry_count=retry_count))

        return PipelineConfig(name=name, on_failure=on_failure, steps=steps)
