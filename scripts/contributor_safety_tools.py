#!/usr/bin/env python3
"""Plan-only contributor safety utilities for public repositories.

Roadmap scope: P-052, P-054, P-055. The module produces reviewable pull-request
payloads, onboarding checklists, and CODEOWNERS proposals from explicit inputs.
It never opens a PR, adds a collaborator, requests a review, or writes CODEOWNERS.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
OWNER = re.compile(r"^@[A-Za-z0-9](?:[A-Za-z0-9-]{0,37})(?:/[A-Za-z0-9_.-]+)?$")


class InputError(ValueError):
    pass


def clean_text(value: Any, name: str, *, max_len: int) -> str:
    text = str(value or "").strip()
    if not text:
        raise InputError(f"{name} is required")
    if len(text) > max_len:
        raise InputError(f"{name} exceeds {max_len} characters")
    return text


def pr_plan(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("PR input must be an object")
    title = clean_text(data.get("title"), "title", max_len=180)
    summary = clean_text(data.get("summary"), "summary", max_len=4000)
    base = clean_text(data.get("base"), "base", max_len=120)
    head = clean_text(data.get("head"), "head", max_len=120)
    if base == head:
        raise InputError("head must differ from base")

    checks = data.get("checks", {})
    if not isinstance(checks, dict):
        raise InputError("checks must be an object")
    required = (
        "tests_run",
        "ci_expected",
        "secrets_reviewed",
        "scope_reviewed",
        "rollback_considered",
    )
    failed = [key for key in required if checks.get(key) is not True]
    body = (
        "## Summary\n" + summary + "\n\n"
        "## Safety / verification\n"
        + "\n".join(f"- [x] {key.replace('_', ' ')}" for key in required if checks.get(key) is True)
        + ("\n" + "\n".join(f"- [ ] {key.replace('_', ' ')}" for key in failed) if failed else "")
        + "\n"
    )
    return {
        "schema_version": "0.1",
        "tool": {"name": "contributor_safety_tools.py", "version": VERSION, "mode": "PR_PLAN_ONLY"},
        "payload": {"title": title, "body": body, "base": base, "head": head, "draft_recommended": bool(failed)},
        "decision": "READY_FOR_HUMAN_OR_GOVERNED_PR_CREATE" if not failed else "DRAFT_OR_BLOCKED_UNTIL_CHECKS_COMPLETE",
        "failed_checks": failed,
        "execution": {"pull_request_created": False, "branch_changed": False, "network_request_performed": False},
    }


def onboarding_plan(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("onboarding input must be an object")
    project = clean_text(data.get("project"), "project", max_len=180)
    files = data.get("files", {})
    if not isinstance(files, dict):
        raise InputError("files must be an object")
    steps = [
        {"step": "Read README", "ready": files.get("README.md") is True},
        {"step": "Read START-HERE", "ready": files.get("START-HERE.md") is True},
        {"step": "Read CONTRIBUTING", "ready": files.get("CONTRIBUTING.md") is True},
        {"step": "Review CODE_OF_CONDUCT if present", "ready": True},
        {"step": "Review SECURITY before reporting a vulnerability", "ready": files.get("SECURITY.md") is True},
        {"step": "Confirm license before contributing/reusing code", "ready": files.get("LICENSE") is True},
        {"step": "Use an issue/discussion to confirm scope for non-trivial work", "ready": True},
        {"step": "Create a focused branch and run documented tests before PR", "ready": files.get("CONTRIBUTING.md") is True},
    ]
    missing = [x["step"] for x in steps if not x["ready"]]
    return {
        "schema_version": "0.1",
        "tool": {"name": "contributor_safety_tools.py", "version": VERSION, "mode": "ONBOARDING_PLAN_ONLY"},
        "project": project,
        "steps": steps,
        "maintainer_gaps": missing,
        "status": "ONBOARDING_PATH_COMPLETE" if not missing else "ONBOARDING_PATH_HAS_GAPS",
        "execution": {"issue_created": False, "comment_created": False, "collaborator_changed": False},
    }


def codeowners_proposal(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("CODEOWNERS input must be an object")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise InputError("rules must be a non-empty array")

    lines = ["# Proposed CODEOWNERS — review before writing to .github/CODEOWNERS"]
    normalized = []
    for index, item in enumerate(rules):
        if not isinstance(item, dict):
            raise InputError(f"rule {index} must be an object")
        pattern = clean_text(item.get("pattern"), f"rules[{index}].pattern", max_len=500)
        if "\n" in pattern or pattern.startswith("#"):
            raise InputError("CODEOWNERS patterns cannot contain newline or begin with # in this planner")
        owners = item.get("owners")
        if not isinstance(owners, list) or not owners:
            raise InputError(f"rules[{index}].owners must be a non-empty array")
        normalized_owners = []
        for owner in owners:
            owner = str(owner).strip()
            if not OWNER.fullmatch(owner):
                raise InputError(f"invalid owner token: {owner!r}")
            normalized_owners.append(owner)
        lines.append(pattern + " " + " ".join(normalized_owners))
        normalized.append({"pattern": pattern, "owners": normalized_owners})

    protects_file = any(rule["pattern"] in {"/.github/CODEOWNERS", ".github/CODEOWNERS", "/.github/", ".github/"} for rule in normalized)
    return {
        "schema_version": "0.1",
        "tool": {"name": "contributor_safety_tools.py", "version": VERSION, "mode": "CODEOWNERS_PROPOSAL_ONLY"},
        "proposed_content": "\n".join(lines) + "\n",
        "rules": normalized,
        "security_note": (
            "Proposal includes ownership for CODEOWNERS/.github."
            if protects_file
            else "Consider assigning an owner to .github/CODEOWNERS or the .github directory so ownership rules are themselves protected."
        ),
        "required_verification": [
            "Verify every referenced user/team exists and has appropriate repository access.",
            "Use GitHub's CODEOWNERS errors endpoint or repository UI to detect invalid syntax after a proposed change.",
            "Review rule order because later matching rules can override earlier ownership.",
            "Review case-sensitive paths against the repository tree.",
        ],
        "execution": {"codeowners_written": False, "review_requested": False, "repository_changed": False},
    }


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InputError("input must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate contributor/PR/CODEOWNERS plans without GitHub mutation")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("pr", "onboarding", "codeowners"):
        p = sub.add_parser(name)
        p.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.input)
        result = {"pr": pr_plan, "onboarding": onboarding_plan, "codeowners": codeowners_proposal}[args.mode](data)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
