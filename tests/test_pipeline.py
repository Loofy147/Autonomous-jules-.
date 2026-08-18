"""Tests for Pipeline runner and orchestration."""

import pytest
from autonomous_jules.pipeline import PipelineRunner

def test_pipeline_status():
    runner = PipelineRunner()
    res = runner.run_step("status")
    assert res["status"] == "SUCCESS"
    assert "jules" in res
    assert "github" in res

def test_pipeline_run_agent():
    runner = PipelineRunner()
    res = runner.run_step("run_agent", {"prompt": "test"})
    assert res["status"] == "SUCCESS"
    assert "task" in res

def test_pipeline_github_comment():
    runner = PipelineRunner()
    res = runner.run_step("github_comment", {"owner": "o", "repo": "r", "issue_number": 5, "body": "hi"})
    assert res["status"] == "SUCCESS"
    assert "comment" in res

def test_pipeline_unknown_action():
    runner = PipelineRunner()
    res = runner.run_step("unknown_action")
    assert res["status"] == "FAILED"
    assert "Unknown action" in res["error"]
