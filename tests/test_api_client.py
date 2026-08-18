"""Tests for Jules API client."""

import pytest
from autonomous_jules.api_client import JulesClient

def test_jules_client_init():
    client = JulesClient(api_key="test_key")
    assert client.api_key == "test_key"
    assert "Authorization" in client.headers

def test_jules_client_get_status():
    client = JulesClient()
    status = client.get_status()
    assert isinstance(status, dict)
    assert "status" in status

def test_jules_client_submit_task():
    client = JulesClient()
    res = client.submit_task({"prompt": "hello"})
    assert isinstance(res, dict)
    assert "status" in res

def test_jules_client_fetch_result():
    client = JulesClient()
    res = client.fetch_result("task_123")
    assert isinstance(res, dict)
    assert res.get("task_id") == "task_123"
