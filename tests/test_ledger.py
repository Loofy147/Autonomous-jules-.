"""Tests for ledger core module and PipelineRunner ledger integration."""

import os
import tempfile
from pathlib import Path
import pytest

import ledger as L
from autonomous_jules.pipeline import PipelineRunner


def test_ledger_core_basic_and_contradiction():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"

        # Init
        L.save(ledger_path, {
            "project": "test-project",
            "created": L.datetime.now(L.timezone.utc).isoformat(),
            "next_id": 1,
            "entries": [],
            "comparators": {}
        })

        data = L.load(ledger_path)
        assert data["project"] == "test-project"

        # Log entry 1
        entry1 = L.build_entry(data, category="constant", key="LIMIT", value="10", session="s1")
        assert entry1["id"] == 1

        # Log entry 2 (contradicting)
        entry2 = L.build_entry(data, category="constant", key="LIMIT", value="20", session="s2")
        assert entry2["id"] == 2

        L.save(ledger_path, data)

        # Check contradictions
        contradictions, warnings = L._find_contradictions(data["entries"], data.get("comparators", {}))
        assert len(contradictions) == 1
        assert contradictions[0][0]["value"] == "10"
        assert contradictions[0][1]["value"] == "20"

        # Supersede
        entry3 = L.build_entry(data, category="constant", key="LIMIT", value="20", supersedes=2, session="s3")
        assert entry3["id"] == 3

        contradictions2, _ = L._find_contradictions(data["entries"], data.get("comparators", {}))
        assert len(contradictions2) == 0


def test_ledger_numeric_range_comparator():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = Path(tmpdir) / "ledger.json"
        L.save(ledger_path, {
            "project": "range-test",
            "created": L.datetime.now(L.timezone.utc).isoformat(),
            "next_id": 1,
            "entries": [],
            "comparators": {}
        })

        data = L.load(ledger_path)
        L.build_entry(data, category="constraint", key="LATENCY_MS", value="10-50", comparator="numeric_range")
        L.build_entry(data, category="constraint", key="LATENCY_MS", value="40-100", comparator="numeric_range")

        # Overlapping ranges -> compatible
        contradictions, _ = L._find_contradictions(data["entries"], data.get("comparators", {}))
        assert len(contradictions) == 0

        # Non-overlapping range -> contradiction
        L.build_entry(data, category="constraint", key="LATENCY_MS", value="200-300", comparator="numeric_range")
        contradictions2, _ = L._find_contradictions(data["entries"], data.get("comparators", {}))
        assert len(contradictions2) == 1


def test_pipeline_ledger_actions():
    runner = PipelineRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "ledger.json")

        # 1. ledger_init
        res_init = runner.run_step("ledger_init", {"ledger_path": ledger_path, "project": "pipeline-ledger"})
        assert res_init["status"] == "SUCCESS"
        assert res_init["ledger"]["ok"] is True

        # Re-init without force
        res_reinit = runner.run_step("ledger_init", {"ledger_path": ledger_path, "project": "pipeline-ledger"})
        assert res_reinit["status"] == "SUCCESS"
        assert "already exists" in res_reinit["ledger"]["message"]

        # 2. ledger_log
        res_log1 = runner.run_step("ledger_log", {
            "ledger_path": ledger_path,
            "category": "decision",
            "key": "DATABASE",
            "value": "PostgreSQL",
            "rationale": "ACID compliance required",
            "session": "s1"
        })
        assert res_log1["status"] == "SUCCESS"
        assert res_log1["ledger"]["id"] == 1

        # 3. ledger_log contradiction
        res_log2 = runner.run_step("ledger_log", {
            "ledger_path": ledger_path,
            "category": "decision",
            "key": "DATABASE",
            "value": "SQLite",
            "session": "s2"
        })
        assert res_log2["status"] == "SUCCESS"
        assert res_log2["ledger"]["id"] == 2

        # 4. ledger_check (expect FAILED due to contradiction)
        res_check = runner.run_step("ledger_check", {"ledger_path": ledger_path})
        assert res_check["status"] == "FAILED"
        assert len(res_check["ledger"]["contradictions"]) == 1

        # ledger_check with fail_on_contradiction=False
        res_check_nofail = runner.run_step("ledger_check", {
            "ledger_path": ledger_path,
            "fail_on_contradiction": False
        })
        assert res_check_nofail["status"] == "SUCCESS"
        assert res_check_nofail["ledger"]["ok"] is False

        # 5. Resolve contradiction via supersedes
        res_log3 = runner.run_step("ledger_log", {
            "ledger_path": ledger_path,
            "category": "decision",
            "key": "DATABASE",
            "value": "SQLite",
            "supersedes": 2,
            "rationale": "Embedded simplifies deployment",
            "session": "s3"
        })
        assert res_log3["status"] == "SUCCESS"

        # Check resolved
        res_check_resolved = runner.run_step("ledger_check", {"ledger_path": ledger_path})
        assert res_check_resolved["status"] == "SUCCESS"
        assert res_check_resolved["ledger"]["ok"] is True

        # 6. ledger_show
        res_show = runner.run_step("ledger_show", {"ledger_path": ledger_path, "key": "DATABASE"})
        assert res_show["status"] == "SUCCESS"
        assert len(res_show["ledger"]["entries"]) == 3

        # ledger_show unknown key
        res_show_unk = runner.run_step("ledger_show", {"ledger_path": ledger_path, "key": "NON_EXISTENT"})
        assert res_show_unk["status"] == "FAILED"

        # 7. Reports: ledger_digest, ledger_health, ledger_keys, ledger_stale
        res_digest = runner.run_step("ledger_digest", {"ledger_path": ledger_path})
        assert res_digest["status"] == "SUCCESS"
        assert "Context primer" in res_digest["ledger"]["output"]

        res_health = runner.run_step("ledger_health", {"ledger_path": ledger_path})
        assert res_health["status"] == "SUCCESS"

        res_keys = runner.run_step("ledger_keys", {"ledger_path": ledger_path})
        assert res_keys["status"] == "SUCCESS"

        # Testing stale keys check with days=30 (fresh entries -> no stale keys -> ok=True)
        res_stale = runner.run_step("ledger_stale", {"ledger_path": ledger_path, "days": 30})
        assert res_stale["status"] == "SUCCESS"
        assert "no stale keys" in res_stale["ledger"]["output"]


def test_pipeline_dry_run_ledger():
    runner = PipelineRunner()
    res = runner.run_step("ledger_log", {"category": "goal", "key": "PERF", "value": "fast"}, dry_run=True)
    assert res["status"] == "SUCCESS"
    assert res["dry_run"] is True


def test_multi_step_pipeline_with_ledger():
    runner = PipelineRunner()
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger_path = os.path.join(tmpdir, "pipeline_ledger.json")
        pipeline_cfg = {
            "name": "Ledger Multi-step Pipeline",
            "on_failure": "stop_on_failure",
            "steps": [
                {
                    "task_id": "init_ledger",
                    "action": "ledger_init",
                    "params": {"ledger_path": ledger_path, "project": "multi-step"}
                },
                {
                    "task_id": "log_goal",
                    "action": "ledger_log",
                    "params": {"ledger_path": ledger_path, "category": "goal", "key": "Uptime", "value": "99.9%"}
                },
                {
                    "task_id": "verify_ledger",
                    "action": "ledger_check",
                    "params": {"ledger_path": ledger_path}
                }
            ]
        }
        res = runner.run_pipeline(pipeline_cfg)
        assert res.status == "SUCCESS"
        assert len(res.details["steps"]) == 3
