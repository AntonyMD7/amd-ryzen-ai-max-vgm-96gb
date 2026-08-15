#!/usr/bin/env python3
"""Verify a public-build release candidate without creating a release.

This verifier is deliberately one step *before* release publication. It binds an
exact checked-out commit, a semantic-version candidate tag, the canonical
19-gate completion record, and required public repository files into a
machine-readable readiness decision.

It never creates or moves a tag, creates/edits a GitHub release, uploads a
release asset, changes repository settings, or contacts a network service.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from public_build_completion_contract import GATES, audit_record, load_record

VERSION = "0.2.0"
SEMVER_TAG = re.compile(
    r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$"
)
EXACT_COMMIT = re.compile(r"^[0-9a-f]{40}$")
PRE_RELEASE_BLOCKERS = {
    "version_tag_or_release_published",
    "canonical_handover_or_build_record_updated",
}
REQUIRED_PUBLIC_FILES = (
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "START-HERE.md",
)


class ReleaseReadinessError(ValueError):
    pass


def _git_head(repo_root: Path) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    value = proc.stdout.strip().lower()
    if proc.returncode != 0 or not EXACT_COMMIT.fullmatch(value):
        raise ReleaseReadinessError("unable to resolve exact checked-out git HEAD")
    return value


def evaluate_release_readiness(
    record: dict[str, Any],
    *,
    tag: str,
    source_commit: str,
    observed_commit: str,
    repo_root: Path,
) -> dict[str, Any]:
    tag = tag.strip()
    source_commit = source_commit.strip().lower()
    observed_commit = observed_commit.strip().lower()

    if not SEMVER_TAG.fullmatch(tag):
        raise ReleaseReadinessError("candidate tag must be semantic versioning, for example v1.2.3 or v1.2.3-rc.1")
    if not EXACT_COMMIT.fullmatch(source_commit):
        raise ReleaseReadinessError("source_commit must be an exact lowercase 40-character SHA-1 commit id")
    if not EXACT_COMMIT.fullmatch(observed_commit):
        raise ReleaseReadinessError("observed_commit must be an exact lowercase 40-character SHA-1 commit id")

    audit = audit_record(record)
    checks: list[dict[str, Any]] = []

    checks.append({
        "gate": "completion_record_structurally_valid",
        "pass": not audit["errors"],
        "detail": audit["errors"],
    })
    checks.append({
        "gate": "exact_source_commit_checked_out",
        "pass": source_commit == observed_commit,
        "expected": source_commit,
        "observed": observed_commit,
    })

    status = record.get("status")
    checks.append({
        "gate": "subject_remains_in_progress_before_release",
        "pass": status == "IN_PROGRESS",
        "observed": status,
    })

    gates = record.get("gates", {}) if isinstance(record.get("gates"), dict) else {}
    blocking = set(audit.get("blocking_gates", []))
    checks.append({
        "gate": "only_release_and_final_handover_remain_blocking",
        "pass": blocking == PRE_RELEASE_BLOCKERS,
        "observed_blocking_gates": sorted(blocking),
        "allowed_pre_release_blockers": sorted(PRE_RELEASE_BLOCKERS),
    })

    non_release_gate_failures: list[str] = []
    for gate_name in GATES:
        if gate_name in PRE_RELEASE_BLOCKERS:
            continue
        gate = gates.get(gate_name, {})
        if not isinstance(gate, dict) or gate.get("state") not in {"PASS", "NOT_APPLICABLE"}:
            non_release_gate_failures.append(gate_name)
    checks.append({
        "gate": "all_non_release_completion_gates_satisfied",
        "pass": not non_release_gate_failures,
        "failures": sorted(non_release_gate_failures),
    })

    completion = record.get("completion_record", {}) if isinstance(record.get("completion_record"), dict) else {}
    checks.append({
        "gate": "completion_record_subject_matches",
        "pass": completion.get("roadmap_id") == record.get("subject_id"),
        "subject_id": record.get("subject_id"),
    })

    file_checks = []
    for rel in REQUIRED_PUBLIC_FILES:
        present = (repo_root / rel).is_file()
        file_checks.append({"path": rel, "present": present})
    checks.append({
        "gate": "required_public_files_present",
        "pass": all(item["present"] for item in file_checks),
        "files": file_checks,
    })

    failures = [item["gate"] for item in checks if not item["pass"]]
    decision = "READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW" if not failures else "BLOCKED"

    return {
        "schema_version": "0.2",
        "evidence_type": "dais-public-build-release-readiness",
        "tool": {"name": "release_readiness_verify.py", "version": VERSION, "mode": "READ_ONLY"},
        "subject_id": record.get("subject_id"),
        "candidate": {"tag": tag, "source_commit": source_commit},
        "observed_commit": observed_commit,
        "decision": decision,
        "checks": checks,
        "failed_checks": failures,
        "completion_contract": {
            "declared_status": audit.get("declared_status"),
            "blocking_gates": audit.get("blocking_gates", []),
            "completion_contract_satisfied": audit.get("completion_contract_satisfied", False),
            "ready_for_canonical_completion_review": audit.get("ready_for_canonical_completion_review", False),
        },
        "execution": {
            "network_request_performed": False,
            "tag_created": False,
            "release_created": False,
            "release_asset_uploaded": False,
            "repository_file_modified": False,
            "repository_setting_modified": False,
            "roadmap_completion_promoted": False,
        },
        "truth_boundary": {
            "readiness_is_release_publication": False,
            "readiness_is_completion": False,
            "source_coverage_is_completion": False,
            "ci_is_completion": False,
        },
        "next_gate": (
            "Independent governed release creation/publishing and post-publication verification are required before the version/release gate can PASS. "
            "The final canonical handover must then bind that published identity before COMPLETE can be reviewed."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="canonical public-build completion record JSON")
    parser.add_argument("--tag", required=True, help="semantic-version candidate tag")
    parser.add_argument("--source-commit", required=True, help="exact commit expected to be checked out")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    try:
        repo_root = args.repo_root.resolve()
        record = load_record(args.record)
        observed = _git_head(repo_root)
        result = evaluate_release_readiness(
            record,
            tag=args.tag,
            source_commit=args.source_commit,
            observed_commit=observed,
            repo_root=repo_root,
        )
    except (OSError, json.JSONDecodeError, ReleaseReadinessError, ValueError) as exc:
        result = {
            "schema_version": "0.2",
            "evidence_type": "dais-public-build-release-readiness",
            "decision": "BLOCKED",
            "input_error": str(exc),
            "execution": {
                "network_request_performed": False,
                "tag_created": False,
                "release_created": False,
                "release_asset_uploaded": False,
                "repository_file_modified": False,
                "repository_setting_modified": False,
                "roadmap_completion_promoted": False,
            },
        }

    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("decision") == "READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW" else 2


if __name__ == "__main__":
    raise SystemExit(main())
