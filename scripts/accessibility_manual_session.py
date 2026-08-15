#!/usr/bin/env python3
"""Validate privacy-minimized manual assistive-technology session evidence.

This module records a reproducible manual accessibility session and maps it into
DAIS' existing Accessible AI supporting-evidence contract. It deliberately does
not drive a browser, screen reader, microphone, operating system, or production
surface and cannot certify WCAG conformance or roadmap completion.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import jsonschema

from accessibility_acceptance_validate import validate_record as validate_supporting_record

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "accessible-ai-manual-session-v0.1.schema.json"

CANONICAL_TASK_IDS = (
    "skip_navigation",
    "landmark_and_heading_navigation",
    "interactive_control_operation",
    "status_and_safety_announcement",
    "logical_reading_order",
    "focus_visibility_and_location",
    "zoom_reflow_400",
    "reduced_motion",
    "language_semantics",
    "error_and_issue_discoverability",
)

SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:password|passwd|secret|api[_ -]?key|bearer)\s*[:=]\s*\S+", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b[A-Z]:\\+Users\\+[^\\\s]+", re.I),
    re.compile(r"/home/[^/\s]+", re.I),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
)

NON_REPRODUCIBLE_VERSION_VALUES = {"", "unknown", "not-run", "not run", "n/a", "na", "unspecified"}


class ManualSessionError(ValueError):
    pass


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_strings(child)


def _canonical_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def session_sha256(record: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(record)).hexdigest()


def _task_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks = record["tasks"]
    ids = [task["task_id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ManualSessionError("manual session contains duplicate task IDs")
    expected = set(CANONICAL_TASK_IDS)
    observed = set(ids)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ManualSessionError(f"manual session task set mismatch: missing={missing} extra={extra}")
    return {task["task_id"]: task for task in tasks}


def _ensure_public_evidence_privacy(record: dict[str, Any]) -> None:
    for text in _walk_strings(record):
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                raise ManualSessionError("public manual-session evidence contains a sensitive/contact/path pattern")


def validate_semantics(record: dict[str, Any]) -> dict[str, Any]:
    _ensure_public_evidence_privacy(record)
    tasks = _task_map(record)
    privacy = record["privacy"]
    mode = record["session_mode"]

    if mode == "MANUAL_ASSISTIVE_TECH":
        if not privacy["people_involved"]:
            raise ManualSessionError("manual assistive-technology evidence requires people_involved=true")
        if not privacy["consent_prerequisite_satisfied"]:
            raise ManualSessionError("manual assistive-technology evidence requires an external consent prerequisite")

        env = record["environment"]
        for field in (
            "os_version",
            "browser_version",
            "assistive_technology_version",
        ):
            value = env[field].strip().lower()
            if value in NON_REPRODUCIBLE_VERSION_VALUES:
                raise ManualSessionError(f"manual session requires reproducible {field}")

        subject = record["subject"]
        if subject["sha256"] == "0" * 64 or subject["artifact_ref"].lower().startswith("synthetic"):
            raise ManualSessionError("manual assistive-technology evidence requires a non-synthetic exact subject identity")
    else:
        if privacy["people_involved"] or privacy["consent_prerequisite_satisfied"]:
            raise ManualSessionError("synthetic protocol checks must not claim people or consent")

    failed = sorted(task_id for task_id, task in tasks.items() if task["status"] == "FAIL")
    blocked = sorted(task_id for task_id, task in tasks.items() if task["status"] == "BLOCKED")
    not_run = sorted(task_id for task_id, task in tasks.items() if task["status"] == "NOT_RUN")
    passed = sorted(task_id for task_id, task in tasks.items() if task["status"] == "PASS")

    if mode == "SYNTHETIC_PROTOCOL_CHECK":
        status = "SYNTHETIC_ONLY_NOT_ACCEPTANCE"
    elif failed:
        status = "MANUAL_SESSION_HAS_FAILURES"
    elif blocked or not_run:
        status = "MANUAL_SESSION_INCOMPLETE"
    else:
        status = "MANUAL_SUPPORTING_ACCEPTANCE_NOT_CONFORMANCE"

    return {
        "status": status,
        "session_mode": mode,
        "session_sha256": session_sha256(record),
        "passed_tasks": passed,
        "failed_tasks": failed,
        "blocked_tasks": blocked,
        "not_run_tasks": not_run,
        "schema_validation": "PASS",
        "privacy_prefilter": "PASS",
        "wcag_conformance_certified_by_validator": False,
        "cross_at_compatibility_certified_by_validator": False,
        "production_ready_certified_by_validator": False,
        "roadmap_completion_certified_by_validator": False,
    }


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(record)
    return validate_semantics(record)


def _aggregate_status(tasks: dict[str, dict[str, Any]], task_ids: tuple[str, ...]) -> str:
    statuses = {tasks[task_id]["status"] for task_id in task_ids}
    if "FAIL" in statuses:
        return "FAIL"
    if "BLOCKED" in statuses or "NOT_RUN" in statuses:
        return "NOT_RUN"
    applicable = statuses - {"NOT_APPLICABLE"}
    if not applicable:
        return "NOT_APPLICABLE"
    return "PASS" if applicable == {"PASS"} else "NOT_RUN"


def _notes_for(tasks: dict[str, dict[str, Any]], task_ids: tuple[str, ...]) -> str:
    pieces = []
    for task_id in task_ids:
        task = tasks[task_id]
        note = task.get("notes", "").strip()
        pieces.append(f"{task_id}={task['status']}" + (f" ({note})" if note else ""))
    return "; ".join(pieces)[:600]


def to_supporting_record(record: dict[str, Any]) -> dict[str, Any]:
    """Map the detailed session into the existing F-06 supporting-evidence schema."""
    result = validate_record(record)
    tasks = _task_map(record)
    digest_ref = f"manual-session-sha256:{result['session_sha256']}"

    groups: dict[str, tuple[str, ...]] = {
        "keyboard_only": (
            "skip_navigation",
            "interactive_control_operation",
            "focus_visibility_and_location",
        ),
        "screen_reader": (
            "landmark_and_heading_navigation",
            "status_and_safety_announcement",
            "logical_reading_order",
            "error_and_issue_discoverability",
        ),
        "zoom_reflow_400": ("zoom_reflow_400",),
        "reduced_motion": ("reduced_motion",),
        "language_semantics": ("language_semantics",),
    }

    checks: dict[str, dict[str, str]] = {}
    for name, task_ids in groups.items():
        checks[name] = {
            "status": _aggregate_status(tasks, task_ids),
            "evidence_ref": digest_ref,
            "notes": _notes_for(tasks, task_ids),
        }

    checks["automated_rules"] = {
        "status": "NOT_RUN",
        "evidence_ref": "",
        "notes": "Manual session evidence does not imply an automated accessibility-engine run.",
    }

    env = record["environment"]
    supporting = {
        "schema_version": "0.1",
        "evidence_type": "accessible-ai-supporting-acceptance",
        "evidence_class": (
            "MANUAL_ASSISTIVE_TECH"
            if record["session_mode"] == "MANUAL_ASSISTIVE_TECH"
            else "SYNTHETIC_CONFORMANCE"
        ),
        "subject": copy.deepcopy(record["subject"]),
        "standard_target": "WCAG_2_2_AA",
        "environment": {
            "os_family": f"{env['os_family']} {env['os_version']}",
            "browser_family": f"{env['browser_family']} {env['browser_version']}",
            "assistive_technology": f"{env['assistive_technology_name']} {env['assistive_technology_version']}",
        },
        "checks": checks,
        "privacy": {
            "participant_identity_stored": False,
            "participant_contact_stored": False,
            "credential_values_stored": False,
            "private_content_stored": False,
            "consent_recorded_when_people_involved": record["privacy"]["consent_prerequisite_satisfied"],
        },
        "claims": {
            "wcag_conformance": False,
            "all_accessibility_issues_found": False,
            "real_user_acceptance": False,
            "production_ready": False,
        },
    }
    validate_supporting_record(supporting)
    return supporting


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a DAIS manual assistive-technology session")
    parser.add_argument("record", type=Path)
    parser.add_argument("--supporting-record-out", type=Path)
    args = parser.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = validate_record(record)
    supporting = to_supporting_record(record)
    result["supporting_record_status"] = validate_supporting_record(supporting)["status"]

    if args.supporting_record_out:
        args.supporting_record_out.write_text(json.dumps(supporting, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
