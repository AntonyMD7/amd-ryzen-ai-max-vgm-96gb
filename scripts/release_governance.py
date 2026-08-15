#!/usr/bin/env python3
"""Fail-closed release candidate governance planner.

This tool never creates tags/releases, uploads assets, or changes repository state.
It validates a caller-supplied release candidate record and emits the remaining
release gates plus a proposed least-privilege GitHub Actions permission set.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
SEMVER_TAG = re.compile(r"^v?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
REQUIRED_PROJECT_FILES = ("README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "START-HERE.md")


class CandidateError(ValueError):
    pass


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise CandidateError("release candidate must be an object")
    tag = str(candidate.get("tag", "")).strip()
    source_commit = str(candidate.get("source_commit", "")).strip()
    if not SEMVER_TAG.fullmatch(tag):
        raise CandidateError("tag must be a semantic-version release tag such as v1.2.3")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", source_commit):
        raise CandidateError("source_commit must be an exact 40-character commit SHA")

    files = candidate.get("project_files", {})
    if not isinstance(files, dict):
        raise CandidateError("project_files must be an object of boolean presence values")

    checks: list[dict[str, Any]] = []
    for name in REQUIRED_PROJECT_FILES:
        checks.append({"gate": f"project_file:{name}", "pass": files.get(name) is True})

    boolean_gates = {
        "ci_passed": "CI for exact source commit passed",
        "tests_passed": "test suite passed",
        "evidence_validated": "release evidence validated",
        "known_limitations_documented": "known limitations documented",
        "security_privacy_reviewed": "security/privacy review complete",
        "accessibility_reviewed": "accessibility review complete",
        "rollback_or_recovery_documented": "rollback/recovery documented where applicable",
        "release_notes_present": "release notes/changelog present",
    }
    for key, label in boolean_gates.items():
        checks.append({"gate": key, "label": label, "pass": candidate.get(key) is True})

    artifacts = candidate.get("artifacts", [])
    artifact_gate = isinstance(artifacts, list) and all(
        isinstance(a, dict)
        and bool(str(a.get("name", "")).strip())
        and bool(re.fullmatch(r"[0-9a-fA-F]{64}", str(a.get("sha256", ""))))
        for a in artifacts
    )
    checks.append({"gate": "artifact_digests_declared", "pass": artifact_gate})

    failures = [x for x in checks if not x["pass"]]
    attestation_requested = candidate.get("artifact_attestation_requested") is True
    permissions = {"contents": "write"}
    if attestation_requested:
        permissions["id-token"] = "write"
        permissions["attestations"] = "write"

    return {
        "schema_version": "0.1",
        "tool": {"name": "release_governance.py", "version": VERSION, "mode": "PLAN_ONLY"},
        "candidate": {"tag": tag, "source_commit": source_commit},
        "decision": "READY_FOR_GOVERNED_RELEASE_WORKFLOW" if not failures else "BLOCKED",
        "checks": checks,
        "failed_gates": [x["gate"] for x in failures],
        "proposed_workflow_permissions": permissions,
        "release_plan": [
            "Re-verify exact source commit and all required checks in the release workflow.",
            "Create the release as a draft first when using immutable-release workflows or when assets must be attached before publication.",
            "Build release assets from the exact source revision in CI; record SHA-256 and provenance.",
            "Generate artifact/release attestations when configured and verify them before publication.",
            "Publish the release only after all assets, notes and evidence are complete.",
            "Verify the published tag/commit/assets after release and retain the verification evidence.",
        ],
        "execution": {
            "tag_created": False,
            "release_created": False,
            "asset_uploaded": False,
            "repository_changed": False,
            "network_request_performed": False,
        },
        "limitations": [
            "Caller-supplied booleans are assertions; a real release workflow must independently verify them.",
            "This planner does not prove source reproducibility, artifact authenticity, or semantic-version correctness for a project's API.",
            "Repository release settings and GitHub features can change and must be checked at release time.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a release candidate without creating a release")
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.candidate.read_text(encoding="utf-8"))
        result = validate_candidate(data)
    except (OSError, json.JSONDecodeError, CandidateError) as exc:
        print(json.dumps({"decision": "BLOCKED", "input_error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["decision"] != "BLOCKED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
