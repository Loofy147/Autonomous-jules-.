#!/usr/bin/env python3
"""
Autonomous Jules Showcase Demonstration Script.

This script demonstrates how to programmatically use:
1. JulesClient: Submit tasks, check status, poll, and cancel tasks.
2. GitHubClient: Comment on issues, submit PR reviews, and set commit status checks.
3. PipelineRunner: Run multi-step declarative workflows programmatically.
4. CLI Integration: Execute pipeline commands via command line interface.
"""

import os
import json
import sys
from autonomous_jules.api_client import JulesClient
from autonomous_jules.github_client import GitHubClient
from autonomous_jules.pipeline import PipelineRunner, PipelineConfig
from autonomous_jules.cli import main as cli_main


def showcase_jules_client():
    print("\n--- 1. Showcase Jules API Client ---")
    client = JulesClient(api_key="showcase_demo_key")
    print(f"Authenticated: {client.is_authenticated()}")

    status = client.get_status()
    print(f"Status check result: {status.get('status')}")

    task_res = client.submit_task({"prompt": "Showcase automated refactoring"})
    print(f"Task submitted: ID={task_res.get('task_id')}, Status={task_res.get('status')}")

    poll_res = client.poll_task_until_complete(task_res.get("task_id", "task_simulated_123"), timeout=2)
    print(f"Task polling completed: ID={poll_res.get('task_id')}")


def showcase_github_client():
    print("\n--- 2. Showcase GitHub REST Client ---")
    client = GitHubClient(token="showcase_github_token")
    print(f"Authenticated: {client.is_authenticated()}")

    comment = client.create_issue_comment("my-org", "my-repo", 101, "Autonomous Jules Showcase Comment")
    print(f"Created issue comment: Issue #{comment.get('issue_number')}")

    review = client.create_pull_request_review("my-org", "my-repo", 12, "Approved by Autonomous Jules Agent", event="APPROVE")
    print(f"Submitted PR review: PR #{review.get('pull_number')}, Event={review.get('event')}")

    status_check = client.create_commit_status("my-org", "my-repo", "abc1234", "success", context="autonomous-jules/showcase")
    print(f"Created commit status check: SHA={status_check.get('sha')}, State={status_check.get('state')}")


def showcase_pipeline_runner():
    print("\n--- 3. Showcase Pipeline Runner (Dry-Run Mode) ---")
    runner = PipelineRunner()

    config_file = os.path.join(os.path.dirname(__file__), "showcase_pipeline.json")
    print(f"Loading declarative pipeline configuration from: {config_file}")

    pipeline_result = runner.run_pipeline(config_file, dry_run=True)
    print(f"Pipeline Execution Status: [{pipeline_result.status}]")
    print(f"Total Duration: {pipeline_result.execution_time}s")
    print(f"Executed Steps Count: {len(pipeline_result.details.get('steps', []))}")
    for idx, step in enumerate(pipeline_result.details.get("steps", []), 1):
        print(f"  Step {idx} [{step.get('task_id')}]: Action='{step.get('action')}' -> {step.get('result', {}).get('status')}")


def showcase_cli():
    print("\n--- 4. Showcase CLI Command Invocation ---")
    print("Executing CLI 'status' command:")
    cli_main(["status", "--output-format", "text"])

    print("\nExecuting CLI 'run' command with declarative pipeline config:")
    config_file = os.path.join(os.path.dirname(__file__), "showcase_pipeline.json")
    cli_main(["--dry-run", "run", "--config-file", config_file, "--output-format", "text"])


def main():
    print("==================================================")
    print("       AUTONOMOUS JULES SHOWCASE DEMO            ")
    print("==================================================")
    showcase_jules_client()
    showcase_github_client()
    showcase_pipeline_runner()
    showcase_cli()
    print("\n==================================================")
    print("       SHOWCASE DEMO COMPLETED SUCCESSFULLY       ")
    print("==================================================")


if __name__ == "__main__":
    main()
