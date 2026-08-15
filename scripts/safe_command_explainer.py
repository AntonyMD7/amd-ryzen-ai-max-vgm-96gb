#!/usr/bin/env python3
"""Safe Command Explainer v0.1.

Parses a command string for educational/risk-review purposes. It never executes the
command. The classifier is intentionally conservative: UNKNOWN is preferred to an
unsupported safety claim, and REVIEW/BLOCK-style guidance is not a malware verdict.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
from typing import Any

VERSION = "0.1.0"

COMMAND_KNOWLEDGE = {
    "pwd": ("Shows the current directory.", "READ_ONLY"),
    "ls": ("Lists directory entries.", "READ_ONLY"),
    "dir": ("Lists directory entries on Windows shells.", "READ_ONLY"),
    "whoami": ("Shows the current user identity.", "READ_ONLY"),
    "hostname": ("Shows the machine hostname.", "READ_ONLY_PRIVACY"),
    "git": ("Runs the Git version-control client; risk depends on the subcommand.", "CONTEXT_DEPENDENT"),
    "cat": ("Prints file content to standard output.", "READ_ONLY_PRIVACY"),
    "type": ("May display a file or identify a command, depending on the shell.", "CONTEXT_DEPENDENT"),
    "python": ("Runs Python code or a Python program.", "EXECUTES_CODE"),
    "python3": ("Runs Python code or a Python program.", "EXECUTES_CODE"),
    "powershell": ("Starts PowerShell and can execute arbitrary commands.", "EXECUTES_CODE"),
    "pwsh": ("Starts PowerShell and can execute arbitrary commands.", "EXECUTES_CODE"),
    "bash": ("Starts a shell and can execute arbitrary commands.", "EXECUTES_CODE"),
    "sh": ("Starts a shell and can execute arbitrary commands.", "EXECUTES_CODE"),
    "curl": ("Transfers data to or from a URL.", "NETWORK"),
    "wget": ("Downloads content from a URL.", "NETWORK"),
    "ssh": ("Opens a remote Secure Shell connection.", "REMOTE_ACCESS"),
    "sudo": ("Requests elevated privileges for another command.", "PRIVILEGED"),
    "rm": ("Removes filesystem entries.", "DESTRUCTIVE_POTENTIAL"),
    "del": ("Deletes files in Windows command shells.", "DESTRUCTIVE_POTENTIAL"),
    "rmdir": ("Removes directories.", "DESTRUCTIVE_POTENTIAL"),
    "shutdown": ("Requests system shutdown/restart.", "DISRUPTIVE"),
    "reboot": ("Requests a system restart.", "DISRUPTIVE"),
}

GIT_SUBCOMMANDS = {
    "status": "READ_ONLY",
    "diff": "READ_ONLY",
    "log": "READ_ONLY",
    "show": "READ_ONLY",
    "branch": "CONTEXT_DEPENDENT",
    "fetch": "NETWORK_METADATA",
    "add": "LOCAL_MUTATION",
    "commit": "LOCAL_MUTATION",
    "switch": "WORKTREE_MUTATION",
    "checkout": "CONTEXT_DEPENDENT",
    "merge": "HISTORY_WORKTREE_MUTATION",
    "pull": "NETWORK_AND_LOCAL_MUTATION",
    "push": "REMOTE_MUTATION",
    "reset": "DESTRUCTIVE_POTENTIAL",
    "clean": "DESTRUCTIVE_POTENTIAL",
}

HIGH_RISK_PATTERNS = [
    (re.compile(r"(^|\s)rm\s+-[^\n]*r[^\n]*f", re.I), "recursive forced deletion"),
    (re.compile(r"git\s+reset\s+--hard", re.I), "hard Git reset can discard worktree/index changes"),
    (re.compile(r"git\s+clean\s+-[^\n]*f", re.I), "Git clean can delete untracked files"),
    (re.compile(r"git\s+push\s+[^\n]*(--force|-f)(\s|$)", re.I), "force push can rewrite remote history"),
    (re.compile(r"(curl|wget)[^\n|;]*\|\s*(sh|bash|sudo|pwsh|powershell)", re.I), "downloads content and immediately executes it"),
    (re.compile(r"chmod\s+777", re.I), "world-writable permission change"),
    (re.compile(r"Set-ExecutionPolicy\s+Unrestricted", re.I), "weakens PowerShell execution-policy restrictions"),
]

SHELL_CONTROL = re.compile(r"(?:&&|\|\||[|;]|>|<|`|\$\()")
SECRET_HINT = re.compile(r"(?i)(token|password|passwd|secret|api[_-]?key|private[_-]?key)\s*=\s*\S+")


def tokenize(command: str) -> list[str]:
    try:
        return shlex.split(command, posix=True)
    except ValueError:
        return command.strip().split()


def explain(command: str) -> dict[str, Any]:
    raw = command.strip()
    tokens = tokenize(raw)
    base = tokens[0].lower() if tokens else ""
    meaning, baseline = COMMAND_KNOWLEDGE.get(base, ("Command is not in the local explanation catalog.", "UNKNOWN"))

    if base == "git" and len(tokens) > 1:
        sub = tokens[1].lower()
        baseline = GIT_SUBCOMMANDS.get(sub, "CONTEXT_DEPENDENT")
        meaning = f"Runs Git subcommand '{sub}'."

    risk_reasons = [description for pattern, description in HIGH_RISK_PATTERNS if pattern.search(raw)]
    has_shell_control = bool(SHELL_CONTROL.search(raw))
    secret_like = bool(SECRET_HINT.search(raw))

    if risk_reasons:
        decision = "HIGH_RISK_REVIEW"
    elif secret_like:
        decision = "SENSITIVE_INPUT_REVIEW"
    elif has_shell_control:
        decision = "COMPOUND_COMMAND_REVIEW"
    elif baseline in {"DESTRUCTIVE_POTENTIAL", "DISRUPTIVE", "PRIVILEGED", "REMOTE_MUTATION", "NETWORK_AND_LOCAL_MUTATION", "HISTORY_WORKTREE_MUTATION", "EXECUTES_CODE"}:
        decision = "REVIEW"
    elif baseline in {"READ_ONLY", "NETWORK_METADATA"}:
        decision = "LOWER_RISK_NOT_GUARANTEED_SAFE"
    else:
        decision = "CONTEXT_REQUIRED"

    return {
        "schema_version": "0.1",
        "tool": {"name": "safe_command_explainer.py", "version": VERSION, "mode": "NON_EXECUTING"},
        "input": {
            "command_echo": "[REDACTED]" if secret_like else raw,
            "token_count": len(tokens),
            "base_command": base or None,
        },
        "explanation": meaning,
        "baseline_class": baseline,
        "decision": decision,
        "risk_reasons": risk_reasons,
        "compound_shell_syntax_detected": has_shell_control,
        "sensitive_assignment_detected": secret_like,
        "next_step": (
            "Do not run this command until each risk reason and target is understood."
            if decision in {"HIGH_RISK_REVIEW", "SENSITIVE_INPUT_REVIEW", "COMPOUND_COMMAND_REVIEW", "REVIEW"}
            else "Verify the command against authoritative documentation and the intended target before running it."
        ),
        "limitations": [
            "Static text classification cannot prove a command is safe.",
            "Aliases, shell expansion, scripts, environment state, remote endpoints and permissions can change behavior.",
            "The explainer never executes the supplied command.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a command without executing it")
    parser.add_argument("command")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = explain(args.command)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["explanation"])
        print(f"Classification: {report['decision']}")
        if report["risk_reasons"]:
            print("Review: " + "; ".join(report["risk_reasons"]))
        print(report["next_step"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
