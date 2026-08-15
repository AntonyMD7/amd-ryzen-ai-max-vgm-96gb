#!/usr/bin/env python3
"""Fail-closed completion-contract auditor for the DAIS public-build portfolio.

This module turns the canonical roadmap's completion contract into a reusable,
machine-checkable record. It deliberately does not infer completion from source
coverage, CI, repository popularity, or a single tool result.

A subject may be marked COMPLETE only when every applicable completion gate is
explicitly PASS with evidence, every non-applicable gate has a reviewed
rationale, and the canonical Project Completion Record fields are populated.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1"
ALLOWED_SUBJECT_RE = re.compile(r"^(?:P-(?:00[1-9]|0[1-9][0-9]|1[0-9]{2}|2[0-1][0-9]|22[0-7])|F-0[1-6])$")
ALLOWED_STATUS = {"IN_PROGRESS", "BLOCKED", "DEFERRED", "COMPLETE"}
ALLOWED_GATE_STATES = {"PASS", "FAIL", "UNKNOWN", "NOT_APPLICABLE"}

# Exact semantic coverage of the roadmap's 19 completion-contract checks.
GATES = (
    "problem_and_intended_users_defined",
    "public_repository_or_distribution_surface_exists",
    "explicit_open_source_license",
    "complete_readme",
    "beginner_start_here_path",
    "engineering_or_architecture_documentation",
    "reproducible_installation_or_use_instructions",
    "safety_scope_and_limitations",
    "recovery_or_rollback_guidance_for_mutating_tools",
    "tests_and_ci",
    "security_and_privacy_review",
    "accessibility_review",
    "multilingual_path_considered",
    "real_world_acceptance_test",
    "evidence_retained",
    "version_tag_or_release_published",
    "known_limitations_documented",
    "contribution_and_issue_paths",
    "canonical_handover_or_build_record_updated",
)

# Exact semantic coverage of the roadmap's Project Completion Record template.
COMPLETION_RECORD_FIELDS = (
    "project",
    "roadmap_id",
    "repository",
    "public_url",
    "version",
    "release_or_tag",
    "completion_date",
    "license",
    "ci_status",
    "security_review",
    "accessibility_review",
    "beginner_path_verified",
    "engineer_path_verified",
    "multilingual_status",
    "real_world_test",
    "evidence_location",
    "known_limitations",
    "handover",
    "final_status",
)

SENSITIVE_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s]{8,}"),
)


class CompletionContractError(ValueError):
    """Raised when a completion record violates the canonical contract."""


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _contains_sensitive_text(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_sensitive_text(v) for v in value.values())
    if isinstance(value, list):
        return any(_contains_sensitive_text(v) for v in value)
    if not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in SENSITIVE_PATTERNS)


def _validate_gate(name: str, gate: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(gate, dict):
        return [f"gate {name} must be an object"]

    unknown_fields = sorted(set(gate) - {"state", "evidence", "rationale", "applicability_reviewed"})
    if unknown_fields:
        errors.append(f"gate {name} contains unsupported fields: {unknown_fields}")

    state = gate.get("state")
    if state not in ALLOWED_GATE_STATES:
        errors.append(f"gate {name} has invalid state: {state!r}")
        return errors

    evidence = gate.get("evidence", [])
    if not isinstance(evidence, list) or any(not _nonempty_string(item) for item in evidence):
        errors.append(f"gate {name} evidence must be a list of non-empty strings")
        evidence = []

    rationale = gate.get("rationale", "")
    if rationale is not None and not isinstance(rationale, str):
        errors.append(f"gate {name} rationale must be a string")

    reviewed = gate.get("applicability_reviewed", False)
    if not isinstance(reviewed, bool):
        errors.append(f"gate {name} applicability_reviewed must be boolean")

    if state == "PASS" and not evidence:
        errors.append(f"gate {name} cannot PASS without evidence")
    if state == "NOT_APPLICABLE":
        if not reviewed:
            errors.append(f"gate {name} NOT_APPLICABLE requires applicability_reviewed=true")
        if not _nonempty_string(rationale):
            errors.append(f"gate {name} NOT_APPLICABLE requires a rationale")

    return errors


def audit_record(record: dict[str, Any]) -> dict[str, Any]:
    """Audit one completion record without mutating it.

    Returns a deterministic report. Structural/semantic errors are included in
    ``errors``. The caller decides whether to fail the process.
    """
    errors: list[str] = []

    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    subject_id = record.get("subject_id")
    if not isinstance(subject_id, str) or not ALLOWED_SUBJECT_RE.fullmatch(subject_id):
        errors.append("subject_id must be canonical P-001..P-227 or F-01..F-06")

    status = record.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"status must be one of {sorted(ALLOWED_STATUS)}")

    gates = record.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}

    missing_gates = sorted(set(GATES) - set(gates))
    extra_gates = sorted(set(gates) - set(GATES))
    if missing_gates:
        errors.append(f"missing completion gates: {missing_gates}")
    if extra_gates:
        errors.append(f"unknown completion gates: {extra_gates}")

    for gate_name in GATES:
        if gate_name in gates:
            errors.extend(_validate_gate(gate_name, gates[gate_name]))

    completion_record = record.get("completion_record")
    if not isinstance(completion_record, dict):
        errors.append("completion_record must be an object")
        completion_record = {}

    missing_fields = sorted(set(COMPLETION_RECORD_FIELDS) - set(completion_record))
    extra_fields = sorted(set(completion_record) - set(COMPLETION_RECORD_FIELDS))
    if missing_fields:
        errors.append(f"missing Project Completion Record fields: {missing_fields}")
    if extra_fields:
        errors.append(f"unknown Project Completion Record fields: {extra_fields}")

    if completion_record.get("roadmap_id") not in (None, "", subject_id):
        errors.append("completion_record.roadmap_id must match subject_id")

    if completion_record.get("final_status") not in (None, "", status):
        errors.append("completion_record.final_status must match top-level status when populated")

    if _contains_sensitive_text(record):
        errors.append("record contains a token/secret/private-key pattern and is not safe for public evidence")

    gate_states = Counter(
        gates[name].get("state")
        for name in GATES
        if isinstance(gates.get(name), dict) and gates[name].get("state") in ALLOWED_GATE_STATES
    )
    blocking_gates = [
        name
        for name in GATES
        if not isinstance(gates.get(name), dict)
        or gates[name].get("state") not in {"PASS", "NOT_APPLICABLE"}
    ]
    applicable_gate_failure = bool(blocking_gates)

    completion_fields_populated = all(
        _nonempty_string(completion_record.get(field)) for field in COMPLETION_RECORD_FIELDS
    )
    record_semantically_complete = not applicable_gate_failure and completion_fields_populated

    if status == "COMPLETE" and not record_semantically_complete:
        errors.append("status COMPLETE is forbidden until every applicable gate passes and the Project Completion Record is fully populated")
    if status == "COMPLETE" and completion_record.get("final_status") != "COMPLETE":
        errors.append("a COMPLETE subject requires completion_record.final_status=COMPLETE")

    if status != "COMPLETE" and record_semantically_complete:
        readiness = "READY_FOR_CANONICAL_COMPLETION_REVIEW"
    elif status == "COMPLETE" and not errors:
        readiness = "COMPLETE_CONTRACT_SATISFIED"
    else:
        readiness = "INCOMPLETE"

    return {
        "schema_version": SCHEMA_VERSION,
        "claim": "COMPLETION_CONTRACT_AUDIT_ONLY",
        "subject_id": subject_id,
        "declared_status": status,
        "gate_counts": {state: gate_states.get(state, 0) for state in sorted(ALLOWED_GATE_STATES)},
        "blocking_gates": blocking_gates,
        "project_completion_record_populated": completion_fields_populated,
        "ready_for_canonical_completion_review": readiness == "READY_FOR_CANONICAL_COMPLETION_REVIEW",
        "completion_contract_satisfied": readiness == "COMPLETE_CONTRACT_SATISFIED",
        "readiness": readiness,
        "errors": sorted(errors),
        "safe_public_evidence_prefilter": not _contains_sensitive_text(record),
        "source_coverage_alone_is_completion": False,
        "ci_alone_is_completion": False,
        "automated_accessibility_check_alone_is_conformance": False,
    }


def load_record(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise CompletionContractError("completion record must be a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="JSON completion-contract record")
    args = parser.parse_args(argv)

    report = audit_record(load_record(args.record))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not report["errors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
