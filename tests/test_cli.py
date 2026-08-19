"""Tests for Command Line Interface."""

import pytest
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

def test_cli_github_review(capsys):
    ret = main(["run", "--action", "github_review", "--param", "owner=o", "--param", "repo=r", "--param", "pull_number=1", "--param", "body=lgtm"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "github_review" in captured.out

def test_cli_invalid_action(capsys):
    ret = main(["run", "--action", "invalid_action"])
    assert ret == 1
