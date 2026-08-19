"""Tests for Pipeline runner and orchestration."""

import pytest
from autonomous_jules.pipeline import PipelineRunner, TaskConfig, PipelineResult

def test_task_config_and_pipeline_result_models():
    config = TaskConfig(task_id="t1", action="run_agent", params={"query": "hi"})
    assert config.task_id == "t1"
    assert config.retry_count == 3

    res = PipelineResult(status="SUCCESS", execution_time=0.5, details={"res": "ok"})
    res_dict = res.to_dict()
    assert res_dict["status"] == "SUCCESS"
    assert res_dict["execution_time"] == 0.5

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

def test_pipeline_github_review():
    runner = PipelineRunner()
    res = runner.run_step("github_review", {"owner": "o", "repo": "r", "pull_number": 5, "body": "lgtm", "event": "APPROVE"})
    assert res["status"] == "SUCCESS"
    assert "review" in res

def test_pipeline_trigger_workflow():
    runner = PipelineRunner()
    res = runner.run_step("trigger_workflow", {"owner": "o", "repo": "r", "workflow_id": "pipeline.yml"})
    assert res["status"] == "SUCCESS"
    assert "dispatch" in res

def test_pipeline_unknown_action():
    runner = PipelineRunner()
    res = runner.run_step("unknown_action")
    assert res["status"] == "FAILED"
    assert "Unknown action" in res["error"]
