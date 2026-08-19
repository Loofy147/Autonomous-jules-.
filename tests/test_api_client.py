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

def test_jules_client_retry():
    client = JulesClient(max_retries=2)
    assert client.max_retries == 2

def test_jules_client_poll_task_until_complete():
    client = JulesClient()
    res = client.poll_task_until_complete("task_123", timeout=1, interval=0.1)
    assert isinstance(res, dict)
    assert res.get("task_id") == "task_123"

def test_jules_client_cancel_task():
    client = JulesClient()
    res = client.cancel_task("task_123")
    assert isinstance(res, dict)
    assert res.get("status") == "cancelled"

def test_jules_client_list_tasks():
    client = JulesClient()
    res = client.list_tasks(limit=5)
    assert isinstance(res, dict)
    assert "tasks" in res
