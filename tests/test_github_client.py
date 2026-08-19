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

def test_github_client_create_issue_comment():
    client = GitHubClient()
    res = client.create_issue_comment("owner", "repo", 1, "test body")
    assert isinstance(res, dict)
    assert res.get("issue_number") == 1

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
