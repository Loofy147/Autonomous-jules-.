"""Pipeline Orchestration and Runner module."""

import contextlib
import io
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, Any, Optional, List, Union
from autonomous_jules.api_client import JulesClient
from autonomous_jules.github_client import GitHubClient

try:
    import ledger as L
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    import ledger as L


@dataclass
class TaskConfig:
    """Task Execution Configuration data model."""
    task_id: str
    action: str
    params: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 3

    def to_dict(self) -> Dict[str, Any]:
        """Convert TaskConfig to dictionary."""
        return {
            "task_id": self.task_id,
            "action": self.action,
            "params": self.params,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskConfig":
        """Construct TaskConfig from dictionary."""
        return cls(
            task_id=data.get("task_id", "step_1"),
            action=data.get("action", "status"),
            params=data.get("params", {}),
            retry_count=int(data.get("retry_count", 3)),
        )


@dataclass
class PipelineConfig:
    """Pipeline Configuration data model."""
    name: str = "Autonomous Jules Pipeline"
    on_failure: str = "stop_on_failure"  # "stop_on_failure" or "continue_on_failure"
    steps: List[TaskConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert PipelineConfig to dictionary."""
        return {
            "name": self.name,
            "on_failure": self.on_failure,
            "steps": [s.to_dict() for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Construct PipelineConfig from dictionary."""
        name = data.get("name", "Autonomous Jules Pipeline")
        on_failure = data.get("on_failure", "stop_on_failure")
        steps_raw = data.get("steps", [])
        steps = [TaskConfig.from_dict(s) for s in steps_raw]
        return cls(name=name, on_failure=on_failure, steps=steps)


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


def _run_ledger_cli_report(fn, ledger_path: Union[str, Path], **kwargs) -> Dict[str, Any]:
    """Capture stdout and execute a ledger CLI report command."""
    args = SimpleNamespace(path=str(ledger_path), **kwargs)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            rc = fn(args)
        return {"ok": (rc if isinstance(rc, int) else 0) == 0, "output": buf.getvalue()}
    except SystemExit as e:
        return {"ok": False, "output": buf.getvalue(), "error": str(e.code)}


def resolve_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """Substitute environment variables ($VAR or ${VAR}) in parameter values."""
    resolved = {}
    for k, v in params.items():
        if isinstance(v, str) and v.startswith("$"):
            var_name = v[1:].strip("{}")
            resolved[k] = os.getenv(var_name, v)
        else:
            resolved[k] = v
    return resolved


class PipelineRunner:
    """Orchestrates single-step and multi-step workflow actions."""

    def __init__(self, jules_client: Optional[JulesClient] = None, github_client: Optional[GitHubClient] = None):
        self.jules_client = jules_client or JulesClient()
        self.github_client = github_client or GitHubClient()

    def run_step(self, action: str, params: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Execute a single workflow step."""
        params = resolve_params(params or {})
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

        elif action == "get_issue":
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            issue_number = int(params.get("issue_number", 1))
            issue_res = self.github_client.get_issue(owner, repo, issue_number)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "issue": issue_res
            }

        elif action in ("create_pr", "create_pull_request"):
            owner = params.get("owner", "owner")
            repo = params.get("repo", "repo")
            title = params.get("title", "Autonomous Agent Pull Request")
            head = params.get("head", "feature-branch")
            base = params.get("base", "main")
            body = params.get("body", "Automated PR created by Autonomous Jules.")
            pr_res = self.github_client.create_pull_request(owner, repo, title, head, base, body)
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "pull_request": pr_res
            }

        elif action == "ledger_init":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            project = params.get("project", "autonomous-jules")
            force = params.get("force", False)
            if ledger_path.exists() and not force:
                return {
                    "action": action,
                    "status": "SUCCESS",
                    "duration": round(time.time() - start_time, 4),
                    "ledger": {"ok": True, "project": project, "message": f"{ledger_path} already exists."}
                }
            L.save(ledger_path, {
                "project": project,
                "created": L.datetime.now(L.timezone.utc).isoformat(),
                "next_id": 1,
                "entries": [],
                "comparators": {}
            })
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "ledger": {"ok": True, "project": project}
            }

        elif action == "ledger_log":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                L.save(ledger_path, {
                    "project": params.get("project", "autonomous-jules"),
                    "created": L.datetime.now(L.timezone.utc).isoformat(),
                    "next_id": 1,
                    "entries": [],
                    "comparators": {}
                })
            data = L.load(ledger_path)
            warnings: List[str] = []
            try:
                entry = L.build_entry(
                    data,
                    category=params.get("category", "decision"),
                    key=params.get("key", ""),
                    value=str(params.get("value", "")),
                    rationale=params.get("rationale", ""),
                    session=params.get("session", ""),
                    supersedes=params.get("supersedes"),
                    comparator=params.get("comparator"),
                    warn=warnings.append,
                )
                L.save(ledger_path, data)
                return {
                    "action": action,
                    "status": "SUCCESS",
                    "duration": round(time.time() - start_time, 4),
                    "ledger": {"ok": True, "id": entry["id"], "entry": entry, "warnings": warnings}
                }
            except Exception as e:
                return {
                    "action": action,
                    "status": "FAILED",
                    "error": str(e),
                    "duration": round(time.time() - start_time, 4)
                }

        elif action == "ledger_check":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                data = {"entries": [], "comparators": {}}
            else:
                data = L.load(ledger_path)
            contradictions, warnings = L._find_contradictions(
                data.get("entries", []), data.get("comparators", {})
            )
            ok = len(contradictions) == 0
            fail_on_contradiction = params.get("fail_on_contradiction", True)
            formatted_contradictions = [
                {
                    "key": cur["key"],
                    "origin_id": prev["id"],
                    "origin_value": prev["value"],
                    "latest_id": cur["id"],
                    "latest_value": cur["value"],
                }
                for prev, cur in contradictions
            ]
            res_data = {
                "action": action,
                "status": "SUCCESS" if (ok or not fail_on_contradiction) else "FAILED",
                "duration": round(time.time() - start_time, 4),
                "ledger": {
                    "ok": ok,
                    "contradictions": formatted_contradictions,
                    "warnings": warnings,
                }
            }
            if not ok and fail_on_contradiction:
                res_data["error"] = f"Found {len(contradictions)} unresolved contradiction(s)"
            return res_data

        elif action == "ledger_digest":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                L.save(ledger_path, {
                    "project": params.get("project", "autonomous-jules"),
                    "created": L.datetime.now(L.timezone.utc).isoformat(),
                    "next_id": 1,
                    "entries": [],
                    "comparators": {}
                })
            report_res = _run_ledger_cli_report(L.cmd_digest, ledger_path)
            return {
                "action": action,
                "status": "SUCCESS" if report_res["ok"] else "FAILED",
                "duration": round(time.time() - start_time, 4),
                "ledger": report_res
            }

        elif action == "ledger_health":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                L.save(ledger_path, {
                    "project": params.get("project", "autonomous-jules"),
                    "created": L.datetime.now(L.timezone.utc).isoformat(),
                    "next_id": 1,
                    "entries": [],
                    "comparators": {}
                })
            report_res = _run_ledger_cli_report(L.cmd_health, ledger_path)
            return {
                "action": action,
                "status": "SUCCESS" if report_res["ok"] else "FAILED",
                "duration": round(time.time() - start_time, 4),
                "ledger": report_res
            }

        elif action == "ledger_show":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            key = params.get("key")
            if not key:
                return {
                    "action": action,
                    "status": "FAILED",
                    "error": "Parameter 'key' is required for ledger_show",
                    "duration": round(time.time() - start_time, 4)
                }
            if not ledger_path.exists():
                return {
                    "action": action,
                    "status": "FAILED",
                    "error": f"Ledger file '{ledger_path}' does not exist",
                    "duration": round(time.time() - start_time, 4)
                }
            data = L.load(ledger_path)
            entries = sorted((e for e in data.get("entries", []) if e["key"] == key), key=lambda x: x["id"])
            if not entries:
                return {
                    "action": action,
                    "status": "FAILED",
                    "error": f"no entries for key '{key}'",
                    "duration": round(time.time() - start_time, 4)
                }
            return {
                "action": action,
                "status": "SUCCESS",
                "duration": round(time.time() - start_time, 4),
                "ledger": {"ok": True, "key": key, "entries": entries}
            }

        elif action == "ledger_keys":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                L.save(ledger_path, {
                    "project": params.get("project", "autonomous-jules"),
                    "created": L.datetime.now(L.timezone.utc).isoformat(),
                    "next_id": 1,
                    "entries": [],
                    "comparators": {}
                })
            threshold = float(params.get("threshold", 0.80))
            report_res = _run_ledger_cli_report(L.cmd_keys, ledger_path, threshold=threshold)
            return {
                "action": action,
                "status": "SUCCESS" if report_res["ok"] else "FAILED",
                "duration": round(time.time() - start_time, 4),
                "ledger": report_res
            }

        elif action == "ledger_stale":
            ledger_path = Path(params.get("ledger_path", "ledger.json"))
            if not ledger_path.exists():
                L.save(ledger_path, {
                    "project": params.get("project", "autonomous-jules"),
                    "created": L.datetime.now(L.timezone.utc).isoformat(),
                    "next_id": 1,
                    "entries": [],
                    "comparators": {}
                })
            days = int(params.get("days", 30))
            category = params.get("category")
            report_res = _run_ledger_cli_report(L.cmd_stale, ledger_path, days=days, category=category)
            return {
                "action": action,
                "status": "SUCCESS" if report_res["ok"] else "FAILED",
                "duration": round(time.time() - start_time, 4),
                "ledger": report_res
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
            config = PipelineConfig.from_dict(data)
        elif isinstance(pipeline_config, dict):
            config = PipelineConfig.from_dict(pipeline_config)
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
