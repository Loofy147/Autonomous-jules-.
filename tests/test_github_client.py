"""Tests for GitHub REST API client."""

import pytest
from autonomous_jules.github_client import GitHubClient

def test_github_client_init():
    client = GitHubClient(token="test_token")
    assert client.token == "test_token"
    assert "Authorization" in client.headers

def test_github_client_get_user():
    client = GitHubClient()
    user = client.get_user()
    assert isinstance(user, dict)

def test_github_client_get_repo():
    client = GitHubClient()
    repo = client.get_repo("test_owner", "test_repo")
    assert isinstance(repo, dict)

def test_github_client_get_file_content():
    client = GitHubClient()
    content = client.get_file_content("owner", "repo", "README.md")
    assert isinstance(content, dict)

def test_github_client_create_issue():
    client = GitHubClient()
    res = client.create_issue("owner", "repo", "Test Title", "Test Body")
    assert isinstance(res, dict)
    assert res.get("title") == "Test Title"

def test_github_client_create_issue_comment():
    client = GitHubClient()
    res = client.create_issue_comment("owner", "repo", 1, "test body")
    assert isinstance(res, dict)
    assert res.get("issue_number") == 1

def test_github_client_get_pull_request():
    client = GitHubClient()
    res = client.get_pull_request("owner", "repo", 10)
    assert isinstance(res, dict)
    assert res.get("pull_number") == 10

def test_github_client_create_pull_request_review():
    client = GitHubClient()
    res = client.create_pull_request_review("owner", "repo", 1, "review body", "APPROVE")
    assert isinstance(res, dict)
    assert res.get("pull_number") == 1
    assert res.get("event") == "APPROVE"

def test_github_client_trigger_workflow_dispatch():
    client = GitHubClient()
    res = client.trigger_workflow_dispatch("owner", "repo", "pipeline.yml", "main")
    assert isinstance(res, dict)
    assert res.get("workflow_id") == "pipeline.yml"
    assert res.get("status") == "triggered"

def test_github_client_get_workflow_run():
    client = GitHubClient()
    res = client.get_workflow_run("owner", "repo", 12345)
    assert isinstance(res, dict)
    assert res.get("run_id") == 12345

def test_github_client_create_commit_status():
    client = GitHubClient()
    res = client.create_commit_status("owner", "repo", "abc1234", "success", description="all good")
    assert isinstance(res, dict)
    assert res.get("sha") == "abc1234"
    assert res.get("state") == "success"
