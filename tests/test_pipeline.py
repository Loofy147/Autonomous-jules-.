"""Tests for Pipeline runner and orchestration."""

import os
import pytest
import tempfile
import json
from autonomous_jules.pipeline import PipelineRunner, TaskConfig, PipelineConfig, PipelineResult, resolve_params

def test_task_config_and_pipeline_result_models():
    config = TaskConfig(task_id="t1", action="run_agent", params={"query": "hi"})
    assert config.task_id == "t1"
    assert config.retry_count == 3

    p_config = PipelineConfig(name="P1", steps=[config])
    p_dict = p_config.to_dict()
    assert p_dict["name"] == "P1"
    assert len(p_dict["steps"]) == 1

    p_deserialized = PipelineConfig.from_dict(p_dict)
    assert p_deserialized.name == "P1"

    res = PipelineResult(status="SUCCESS", execution_time=0.5, details={"res": "ok"})
    res_dict = res.to_dict()
    assert res_dict["status"] == "SUCCESS"
    assert res_dict["execution_time"] == 0.5

def test_resolve_params():
    os.environ["TEST_ENV_VAR"] = "my_env_val"
    params = {"key1": "$TEST_ENV_VAR", "key2": "${TEST_ENV_VAR}", "key3": "literal"}
    resolved = resolve_params(params)
    assert resolved["key1"] == "my_env_val"
    assert resolved["key2"] == "my_env_val"
    assert resolved["key3"] == "literal"

def test_pipeline_status():
    runner = PipelineRunner()
    res = runner.run_step("status")
    assert res["status"] == "SUCCESS"
    assert "jules" in res
    assert "github" in res

def test_pipeline_dry_run():
    runner = PipelineRunner()
    res = runner.run_step("run_agent", {"prompt": "test"}, dry_run=True)
    assert res["status"] == "SUCCESS"
    assert res["dry_run"] is True

def test_pipeline_run_agent():
    runner = PipelineRunner()
    res = runner.run_step("run_agent", {"prompt": "test"})
    assert res["status"] == "SUCCESS"
    assert "task" in res

def test_pipeline_poll_and_cancel():
    runner = PipelineRunner()
    poll_res = runner.run_step("poll", {"task_id": "t1", "timeout": 1})
    assert poll_res["status"] == "SUCCESS"

    cancel_res = runner.run_step("cancel", {"task_id": "t1"})
    assert cancel_res["status"] == "SUCCESS"

def test_pipeline_list_tasks():
    runner = PipelineRunner()
    res = runner.run_step("list_tasks", {"limit": 5})
    assert res["status"] == "SUCCESS"

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

def test_pipeline_commit_status():
    runner = PipelineRunner()
    res = runner.run_step("commit_status", {"owner": "o", "repo": "r", "sha": "abc", "state": "success"})
    assert res["status"] == "SUCCESS"
    assert "commit_status" in res

def test_pipeline_get_file_and_create_issue():
    runner = PipelineRunner()
    file_res = runner.run_step("get_file", {"owner": "o", "repo": "r", "path": "README.md"})
    assert file_res["status"] == "SUCCESS"

    issue_res = runner.run_step("create_issue", {"owner": "o", "repo": "r", "title": "t", "body": "b"})
    assert issue_res["status"] == "SUCCESS"

    get_issue_res = runner.run_step("get_issue", {"owner": "o", "repo": "r", "issue_number": 1})
    assert get_issue_res["status"] == "SUCCESS"

def test_pipeline_create_pr():
    runner = PipelineRunner()
    pr_res = runner.run_step("create_pr", {"owner": "o", "repo": "r", "title": "t", "head": "h", "base": "main"})
    assert pr_res["status"] == "SUCCESS"
    assert "pull_request" in pr_res

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

def test_multi_step_pipeline_run():
    runner = PipelineRunner()
    cfg_dict = {
        "name": "Test Pipeline",
        "on_failure": "stop_on_failure",
        "steps": [
            {"task_id": "step1", "action": "status"},
            {"task_id": "step2", "action": "run_agent", "params": {"query": "check"}}
        ]
    }
    res = runner.run_pipeline(cfg_dict)
    assert res.status == "SUCCESS"
    assert len(res.details["steps"]) == 2

def test_pipeline_run_from_file():
    runner = PipelineRunner()
    cfg_dict = {
        "name": "File Pipeline",
        "steps": [
            {"task_id": "step1", "action": "status"}
        ]
    }
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f:
        json.dump(cfg_dict, f)
        f_path = f.name

    res = runner.run_pipeline(f_path)
    assert res.status == "SUCCESS"
    assert len(res.details["steps"]) == 1
