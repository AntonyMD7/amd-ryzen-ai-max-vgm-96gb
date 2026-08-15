#!/usr/bin/env python3
"""Deterministic safety prefilters for issue triage, PR review, and docs repair.

Roadmap scope: P-042, P-043, P-061. The module is intentionally not an agent
runtime. It consumes sanitized explicit inputs or a bounded local docs tree and
emits review plans. Future GitHub Agentic Workflows integration can use these
contracts while retaining GitHub's read-only analysis and safe-output write gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
SECURITY_TERMS = re.compile(r"\b(vulnerab|exploit|credential|secret|token leak|rce|xss|sql injection|csrf|auth bypass)\w*", re.I)
BUG_TERMS = re.compile(r"\b(bug|crash|error|fails?|broken|regression|exception|traceback)\b", re.I)
DOC_TERMS = re.compile(r"\b(readme|docs?|documentation|typo|spelling|example)\b", re.I)
FEATURE_TERMS = re.compile(r"\b(feature|enhancement|support|request|proposal)\b", re.I)
HIGH_RISK_PATHS = (
    (re.compile(r"(^|/)(\.github/workflows|\.github/actions)(/|$)", re.I), "workflow_or_action"),
    (re.compile(r"(^|/)(auth|security|crypto|permissions?|access)(/|$)", re.I), "security_sensitive"),
    (re.compile(r"(^|/)(migrations?|schema)(/|$)", re.I), "data_migration_or_schema"),
    (re.compile(r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|Cargo\.lock|go\.sum|poetry\.lock|uv\.lock)$", re.I), "dependency_lockfile"),
    (re.compile(r"(^|/)(Dockerfile|compose\.ya?ml|terraform|infra)(/|$)?", re.I), "deployment_or_infrastructure"),
)
PUBLIC_DOCS = ("README.md", "START-HERE.md", "CONTRIBUTING.md", "SECURITY.md", "LICENSE")


class InputError(ValueError):
    pass


def text(value: Any, name: str, limit: int = 10000) -> str:
    result = str(value or "").strip()
    if not result:
        raise InputError(f"{name} is required")
    return result[:limit]


def issue_triage(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("issue must be an object")
    number = data.get("number")
    if isinstance(number, bool) or not isinstance(number, int):
        raise InputError("issue number must be integer")
    title = text(data.get("title"), "title", 500)
    body = str(data.get("body") or "")[:20000]
    combined = f"{title}\n{body}"

    if SECURITY_TERMS.search(combined):
        category = "POTENTIAL_SECURITY_REPORT"
        labels = ["security-review-needed"]
        write_allowed = False
        handling = "Do not post potentially sensitive details publicly. Route to the repository SECURITY.md/private reporting path and require maintainer review."
    elif DOC_TERMS.search(combined):
        category = "DOCUMENTATION"
        labels = ["documentation"]
        write_allowed = False
        handling = "Human or governed safe-output workflow may apply a documentation label after context review."
    elif BUG_TERMS.search(combined):
        category = "BUG_CANDIDATE"
        labels = ["bug"]
        write_allowed = False
        handling = "Verify reproduction/environment/version details before labeling or prioritizing."
    elif FEATURE_TERMS.search(combined):
        category = "FEATURE_CANDIDATE"
        labels = ["enhancement"]
        write_allowed = False
        handling = "Confirm scope and existing alternatives before labeling or planning implementation."
    else:
        category = "NEEDS_HUMAN_TRIAGE"
        labels = []
        write_allowed = False
        handling = "Insufficient deterministic signal; keep unclassified for maintainer review."

    return {
        "schema_version": "0.1",
        "mode": "ISSUE_TRIAGE_PLAN_ONLY",
        "issue": {"number": number, "title": title},
        "category": category,
        "suggested_labels": labels,
        "automatic_write_allowed": write_allowed,
        "handling": handling,
        "required_checks": [
            "Search for existing/duplicate issues before adding a new label/comment.",
            "Do not quote secrets, credentials, private logs, personal data, or unpublished security details into a public comment.",
            "Use a safe-output or explicit approval boundary for any GitHub write.",
        ],
        "execution": {"github_queried": False, "label_applied": False, "comment_posted": False, "issue_changed": False},
        "limitations": ["Keyword triage is a prefilter, not semantic understanding or severity assessment."],
    }


def pr_review(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("PR input must be an object")
    number = data.get("number")
    files = data.get("files")
    if isinstance(number, bool) or not isinstance(number, int):
        raise InputError("PR number must be integer")
    if not isinstance(files, list):
        raise InputError("files must be an array")
    findings = []
    total_changes = 0
    for item in files:
        if not isinstance(item, dict):
            continue
        path = text(item.get("path"), "file path", 500)
        additions = item.get("additions", 0)
        deletions = item.get("deletions", 0)
        if not isinstance(additions, int) or isinstance(additions, bool) or not isinstance(deletions, int) or isinstance(deletions, bool):
            raise InputError("additions/deletions must be integers")
        total_changes += max(0, additions) + max(0, deletions)
        for pattern, kind in HIGH_RISK_PATHS:
            if pattern.search(path):
                findings.append({"path": path, "kind": kind, "required_review": True})
    large = total_changes > 800 or len(files) > 40
    if large:
        findings.append({"path": None, "kind": "large_change_set", "required_review": True})

    ci = data.get("ci_status", "unknown")
    if ci not in {"success", "failure", "pending", "unknown"}:
        raise InputError("ci_status must be success, failure, pending, or unknown")
    decision = "HUMAN_REVIEW_REQUIRED"
    blockers = []
    if ci in {"failure", "pending", "unknown"}:
        blockers.append(f"CI status is {ci}")
    if findings:
        blockers.append("Risk-sensitive paths/change size require focused review")
    return {
        "schema_version": "0.1",
        "mode": "PR_REVIEW_PLAN_ONLY",
        "pr_number": number,
        "summary": {"file_count": len(files), "line_changes": total_changes, "ci_status": ci},
        "risk_findings": findings,
        "decision": decision,
        "blockers_or_review_focus": blockers,
        "review_checklist": [
            "Read the actual diff; metadata-only classification cannot find logic bugs.",
            "Verify tests cover changed behavior and inspect failing/pending CI before approval.",
            "Review workflows/actions for untrusted-input, permissions and action pinning risks.",
            "Review dependency changes with dependency-review/scanner evidence plus source diff.",
            "Review migrations/schema changes for backup/rollback and compatibility.",
            "Never auto-approve or auto-merge from this plan.",
        ],
        "execution": {"diff_content_read": False, "review_submitted": False, "approval_submitted": False, "merge_performed": False},
        "limitations": ["File metadata cannot establish correctness, security, test adequacy, or intent."],
    }


def docs_repair(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise InputError("root must be a directory")
    present = {name: (root / name).is_file() for name in PUBLIC_DOCS}
    repairs = []
    for name, exists in present.items():
        if not exists:
            repairs.append({"kind": "missing_public_doc", "path": name, "proposal": f"Create {name} through a reviewed documentation PR."})

    readme = root / "README.md"
    if readme.is_file():
        try:
            content = readme.read_text(encoding="utf-8", errors="replace")[:1_000_000]
        except OSError:
            content = ""
        checks = {
            "start_here_link": "START-HERE" in content,
            "contributing_link": "CONTRIBUTING" in content,
            "security_link": "SECURITY" in content,
            "license_mention": "LICENSE" in content or "license" in content.lower(),
        }
        for key, ok in checks.items():
            if not ok:
                repairs.append({"kind": "readme_navigation_gap", "path": "README.md", "proposal": f"Add/review {key.replace('_', ' ')} through a focused PR."})
    else:
        checks = {}

    return {
        "schema_version": "0.1",
        "mode": "DOCS_REPAIR_PLAN_ONLY",
        "observed": {"public_docs": present, "readme_navigation_checks": checks},
        "proposed_repairs": repairs,
        "decision": "PATCH_PR_RECOMMENDED" if repairs else "NO_DETERMINISTIC_REPAIR_NEEDED",
        "safe_automation_contract": [
            "Generate documentation changes on an isolated branch; never push directly to protected main.",
            "Open a reviewable PR rather than silently rewriting documentation.",
            "Run Markdown lint/link checks and project CI before merge.",
            "Do not invent commands, support claims, compatibility, versions or URLs not grounded in repository/upstream evidence.",
            "Do not auto-merge documentation repair PRs from untrusted issue/PR content.",
        ],
        "execution": {"file_written": False, "branch_created": False, "pull_request_created": False, "network_request_performed": False},
        "limitations": ["Presence/navigation checks do not establish documentation accuracy, completeness, accessibility, or link health."],
    }


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise InputError("input must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate GitHub triage/review/docs plans without GitHub writes")
    sub = parser.add_subparsers(dest="mode", required=True)
    for name in ("issue", "pr"):
        p = sub.add_parser(name)
        p.add_argument("input", type=Path)
    docs = sub.add_parser("docs")
    docs.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    try:
        if args.mode == "issue":
            result = issue_triage(load(args.input))
        elif args.mode == "pr":
            result = pr_review(load(args.input))
        else:
            result = docs_repair(args.root)
    except (OSError, json.JSONDecodeError, InputError) as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
