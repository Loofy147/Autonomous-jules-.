"""Tests for showcase examples and demonstration script."""

import os
import sys
import json
import pytest

# Ensure repository root is in sys.path when running in isolated test runners
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from examples.showcase_demo import showcase_jules_client, showcase_github_client, showcase_pipeline_runner, showcase_cli, main as showcase_main
from autonomous_jules.pipeline import PipelineRunner

def test_showcase_pipeline_json_validity():
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
    pipeline_file = os.path.join(examples_dir, "showcase_pipeline.json")
    assert os.path.exists(pipeline_file)

    with open(pipeline_file, "r") as f:
        data = json.load(f)
    assert "name" in data
    assert "steps" in data
    assert len(data["steps"]) >= 5

def test_showcase_pipeline_execution():
    examples_dir = os.path.join(os.path.dirname(__file__), "..", "examples")
    pipeline_file = os.path.join(examples_dir, "showcase_pipeline.json")

    runner = PipelineRunner()
    res = runner.run_pipeline(pipeline_file, dry_run=True)
    assert res.status == "SUCCESS"
    assert len(res.details["steps"]) == 6

def test_showcase_demo_functions(capsys):
    showcase_jules_client()
    captured = capsys.readouterr()
    assert "Showcase Jules API Client" in captured.out

    showcase_github_client()
    captured = capsys.readouterr()
    assert "Showcase GitHub REST Client" in captured.out

    showcase_pipeline_runner()
    captured = capsys.readouterr()
    assert "Showcase Pipeline Runner" in captured.out

    showcase_cli()
    captured = capsys.readouterr()
    assert "Showcase CLI Command Invocation" in captured.out

def test_showcase_demo_main(capsys):
    showcase_main()
    captured = capsys.readouterr()
    assert "SHOWCASE DEMO COMPLETED SUCCESSFULLY" in captured.out
