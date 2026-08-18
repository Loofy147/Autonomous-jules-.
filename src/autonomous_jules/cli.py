"""Command Line Interface for Autonomous Jules."""

import argparse
import sys
import json
from autonomous_jules.pipeline import PipelineRunner

def main(args=None):
    parser = argparse.ArgumentParser(description="Autonomous Jules CLI Orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # status command
    subparsers.add_parser("status", help="Check system API connection status")

    # run command
    run_parser = subparsers.add_parser("run", help="Run a pipeline action")
    run_parser.add_argument("--action", required=True, help="Action name (e.g., run_agent, github_comment)")
    run_parser.add_argument("--param", action="append", help="Parameters in key=value format")

    parsed = parser.parse_args(args)

    runner = PipelineRunner()

    if parsed.command == "status":
        result = runner.run_step("status")
        print(json.dumps(result, indent=2))
        return 0

    elif parsed.command == "run":
        params = {}
        if parsed.param:
            for item in parsed.param:
                if "=" in item:
                    k, v = item.split("=", 1)
                    params[k] = v
        result = runner.run_step(parsed.action, params)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "SUCCESS" else 1

    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())
