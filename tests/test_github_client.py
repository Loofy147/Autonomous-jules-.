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
