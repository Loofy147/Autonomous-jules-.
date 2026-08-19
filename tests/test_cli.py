"""Tests for Command Line Interface."""

import pytest
import tempfile
import json
from autonomous_jules.cli import main

def test_cli_status(capsys):
    ret = main(["status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "status" in captured.out

def test_cli_run_agent(capsys):
    ret = main(["run", "--action", "run_agent", "--param", "query=test"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "run_agent" in captured.out

def test_cli_run_dry_run(capsys):
    ret = main(["--dry-run", "run", "--action", "run_agent", "--param", "query=test"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "dry_run" in captured.out

def test_cli_github_review(capsys):
    ret = main(["run", "--action", "github_review", "--param", "owner=o", "--param", "repo=r", "--param", "pull_number=1", "--param", "body=lgtm"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "github_review" in captured.out

def test_cli_invalid_action(capsys):
    ret = main(["run", "--action", "invalid_action"])
    assert ret == 1

def test_cli_poll_command(capsys):
    ret = main(["poll", "--task-id", "task_123", "--timeout", "2"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "poll" in captured.out

def test_cli_cancel_command(capsys):
    ret = main(["cancel", "--task-id", "task_123"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "cancel" in captured.out

def test_cli_commit_status_command(capsys):
    ret = main(["commit-status", "--owner", "o", "--repo", "r", "--sha", "abc1234", "--state", "success"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "commit_status" in captured.out

def test_cli_create_pr_command(capsys):
    ret = main(["create-pr", "--owner", "o", "--repo", "r", "--title", "PR Title", "--head", "feat-1"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "create_pr" in captured.out

def test_cli_create_issue_command(capsys):
    ret = main(["create-issue", "--owner", "o", "--repo", "r", "--title", "Issue Title", "--body", "Body"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "create_issue" in captured.out

def test_cli_get_file_command(capsys):
    ret = main(["get-file", "--owner", "o", "--repo", "r", "--path", "README.md"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "get_file" in captured.out

def test_cli_run_config_file(capsys):
    cfg_dict = {
        "name": "CLI File Pipeline",
        "steps": [
            {"task_id": "step1", "action": "status"}
        ]
    }
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
        json.dump(cfg_dict, f)
        f_path = f.name

    ret = main(["run", "--config-file", f_path, "--output-format", "json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "CLI File Pipeline" in captured.out

def test_cli_text_output_format(capsys):
    ret = main(["--output-format", "text", "status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Summary: [SUCCESS]" in captured.out
