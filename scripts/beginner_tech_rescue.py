#!/usr/bin/env python3
"""Beginner Tech Rescue v0.1.

One safe entry point for three non-mutating tasks:
- basic system-health inspection;
- common error-message explanation;
- command explanation before execution.

The program intentionally has no repair/execution subcommand.
"""

from __future__ import annotations

import argparse
import json

from error_message_explainer import explain_error
from safe_command_explainer import explain as explain_command
from system_doctor import collect as collect_system, render as render_system


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Read-only beginner technology triage; explains before any change is considered"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    health = sub.add_parser("health", help="run shallow read-only system checks")
    health.add_argument("--audience", choices=["beginner", "intermediate", "engineer"], default="beginner")

    error = sub.add_parser("error", help="explain a common error pattern")
    error.add_argument("message")
    error.add_argument("--json", action="store_true")

    command = sub.add_parser("command", help="explain a command without running it")
    command.add_argument("text")
    command.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.mode == "health":
        report = collect_system()
        print(render_system(report, args.audience))
        return 0

    if args.mode == "error":
        report = explain_error(args.message)
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(report["plain_language"])
            print("Safe next checks:")
            for item in report["safe_next_checks"]:
                print(f"- {item}")
            print("No repair was attempted.")
        return 0

    report = explain_command(args.text)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["explanation"])
        print(f"Classification: {report['decision']}")
        for reason in report["risk_reasons"]:
            print(f"Review: {reason}")
        print(report["next_step"])
        print("The command was not executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
