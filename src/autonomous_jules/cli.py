"""Command Line Interface for Autonomous Jules."""

import argparse
import sys
import json
from typing import Dict, Any, Optional
from autonomous_jules.pipeline import PipelineRunner

def format_output(data: Dict[str, Any], output_format: str = "json") -> str:
    """Format dictionary result for stdout."""
    if output_format == "json":
        return json.dumps(data, indent=2)
    elif output_format == "text":
        status = data.get("status", "UNKNOWN")
        action = data.get("action", data.get("details", {}).get("pipeline_name", "pipeline"))
        duration = data.get("duration", data.get("execution_time", 0))
        lines = [f"Summary: [{status}] {action} (Duration: {duration}s)"]
        if "errors" in data and data["errors"]:
            lines.append("Errors:")
            for err in data["errors"]:
                lines.append(f"  - {err}")
        return "\n".join(lines)
    return json.dumps(data, indent=2)

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Autonomous Jules CLI Orchestrator")
    parser.add_argument("--output-format", choices=["json", "text"], default="json", help="Output format (json or text)")
    parser.add_argument("--dry-run", action="store_true", default=False, help="Execute in dry-run mode without network API calls")
    parser.add_argument("--verbose", action="store_true", default=False, help="Enable verbose log output")

    # Common options for subparsers with default=argparse.SUPPRESS so top-level values aren't overridden
    common_sub = argparse.ArgumentParser(add_help=False)
    common_sub.add_argument("--output-format", choices=["json", "text"], default=argparse.SUPPRESS)
    common_sub.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS)
    common_sub.add_argument("--verbose", action="store_true", default=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(dest="command")

    # status command
    subparsers.add_parser("status", parents=[common_sub], help="Check system API connection status")

    # run command
    run_parser = subparsers.add_parser("run", parents=[common_sub], help="Run a pipeline action or multi-step pipeline config file")
    run_parser.add_argument("--action", help="Action name (e.g., run_agent, github_comment, github_review, trigger_workflow, commit_status, create_pr)")
    run_parser.add_argument("--config-file", help="Path to pipeline JSON configuration file")
    run_parser.add_argument("--param", action="append", help="Parameters in key=value format")

    # poll command
    poll_parser = subparsers.add_parser("poll", parents=[common_sub], help="Poll task completion status")
    poll_parser.add_argument("--task-id", required=True, help="Task ID to poll")
    poll_parser.add_argument("--timeout", type=int, default=60, help="Polling timeout in seconds")

    # cancel command
    cancel_parser = subparsers.add_parser("cancel", parents=[common_sub], help="Cancel a running task")
    cancel_parser.add_argument("--task-id", required=True, help="Task ID to cancel")

    # commit-status command
    cs_parser = subparsers.add_parser("commit-status", parents=[common_sub], help="Set a GitHub commit status check")
    cs_parser.add_argument("--owner", required=True, help="Repository owner")
    cs_parser.add_argument("--repo", required=True, help="Repository name")
    cs_parser.add_argument("--sha", default="HEAD", help="Commit SHA")
    cs_parser.add_argument("--state", choices=["success", "failure", "pending", "error"], default="success", help="Commit status state")
    cs_parser.add_argument("--context", default="autonomous-jules/pipeline", help="Status check context label")
    cs_parser.add_argument("--description", default="", help="Status description")

    # create-pr command
    pr_parser = subparsers.add_parser("create-pr", parents=[common_sub], help="Create a pull request")
    pr_parser.add_argument("--owner", required=True, help="Repository owner")
    pr_parser.add_argument("--repo", required=True, help="Repository name")
    pr_parser.add_argument("--title", required=True, help="Pull request title")
    pr_parser.add_argument("--head", required=True, help="Branch containing changes")
    pr_parser.add_argument("--base", default="main", help="Target branch")
    pr_parser.add_argument("--body", default="", help="Pull request description body")

    # create-issue command
    issue_parser = subparsers.add_parser("create-issue", parents=[common_sub], help="Create a repository issue")
    issue_parser.add_argument("--owner", required=True, help="Repository owner")
    issue_parser.add_argument("--repo", required=True, help="Repository name")
    issue_parser.add_argument("--title", required=True, help="Issue title")
    issue_parser.add_argument("--body", default="", help="Issue description body")

    # get-file command
    file_parser = subparsers.add_parser("get-file", parents=[common_sub], help="Get content of a file")
    file_parser.add_argument("--owner", required=True, help="Repository owner")
    file_parser.add_argument("--repo", required=True, help="Repository name")
    file_parser.add_argument("--path", required=True, help="File path in repository")
    file_parser.add_argument("--ref", default="main", help="Git reference (branch/tag/sha)")

    parsed = parser.parse_args(args)

    runner = PipelineRunner()
    output_format = parsed.output_format
    dry_run = parsed.dry_run

    if parsed.command == "status":
        result = runner.run_step("status", dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "run":
        if parsed.config_file:
            res_obj = runner.run_pipeline(parsed.config_file, dry_run=dry_run)
            result = res_obj.to_dict()
            print(format_output(result, output_format))
            return 0 if result.get("status") == "SUCCESS" else 1

        if not parsed.action:
            parser.error("The --action parameter or --config-file parameter is required for 'run'.")

        params = {}
        if parsed.param:
            for item in parsed.param:
                if "=" in item:
                    k, v = item.split("=", 1)
                    params[k] = v

        result = runner.run_step(parsed.action, params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "poll":
        params = {"task_id": parsed.task_id, "timeout": parsed.timeout}
        result = runner.run_step("poll", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "cancel":
        params = {"task_id": parsed.task_id}
        result = runner.run_step("cancel", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "commit-status":
        params = {
            "owner": parsed.owner,
            "repo": parsed.repo,
            "sha": parsed.sha,
            "state": parsed.state,
            "context": parsed.context,
            "description": parsed.description
        }
        result = runner.run_step("commit_status", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "create-pr":
        params = {
            "owner": parsed.owner,
            "repo": parsed.repo,
            "title": parsed.title,
            "head": parsed.head,
            "base": parsed.base,
            "body": parsed.body
        }
        result = runner.run_step("create_pr", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "create-issue":
        params = {
            "owner": parsed.owner,
            "repo": parsed.repo,
            "title": parsed.title,
            "body": parsed.body
        }
        result = runner.run_step("create_issue", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    elif parsed.command == "get-file":
        params = {
            "owner": parsed.owner,
            "repo": parsed.repo,
            "path": parsed.path,
            "ref": parsed.ref
        }
        result = runner.run_step("get_file", params, dry_run=dry_run)
        print(format_output(result, output_format))
        return 0 if result.get("status") == "SUCCESS" else 1

    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
