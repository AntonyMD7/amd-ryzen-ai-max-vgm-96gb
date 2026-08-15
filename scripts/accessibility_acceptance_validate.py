#!/usr/bin/env python3
"""Validate Accessible AI supporting acceptance evidence.

This validator checks structure, privacy declarations, and evidence semantics.
It deliberately cannot certify WCAG conformance, accessibility completeness,
real-user acceptance, or production readiness.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import jsonschema

SCHEMA = Path(__file__).resolve().parents[1] / "schemas" / "accessible-ai-acceptance-v0.1.schema.json"

SENSITIVE_PATTERNS = (
    re.compile(r"\b(?:password|passwd|secret|api[_ -]?key|bearer)\s*[:=]\s*\S+", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\b[A-Z]:\\+Users\\+[^\\\s]+", re.I),
    re.compile(r"/home/[^/\s]+", re.I),
)

PEOPLE_EVIDENCE = {"MANUAL_ASSISTIVE_TECH", "AGGREGATED_REAL_USER_USABILITY"}


class AcceptanceEvidenceError(ValueError):
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


def validate_semantics(record: dict[str, Any]) -> dict[str, Any]:
    for text in _walk_strings(record):
        for pattern in SENSITIVE_PATTERNS:
            if pattern.search(text):
                raise AcceptanceEvidenceError("public acceptance evidence contains a sensitive-value/path pattern")

    evidence_class = record["evidence_class"]
    privacy = record["privacy"]
    checks = record["checks"]

    if evidence_class in PEOPLE_EVIDENCE and not privacy["consent_recorded_when_people_involved"]:
        raise AcceptanceEvidenceError("people-involved evidence requires recorded consent")
    if evidence_class not in PEOPLE_EVIDENCE and privacy["consent_recorded_when_people_involved"]:
        raise AcceptanceEvidenceError("consent flag must be false when no people are involved")

    passed = sorted(name for name, check in checks.items() if check["status"] == "PASS")
    failed = sorted(name for name, check in checks.items() if check["status"] == "FAIL")
    not_run = sorted(name for name, check in checks.items() if check["status"] == "NOT_RUN")

    if evidence_class == "SYNTHETIC_CONFORMANCE":
        status = "SYNTHETIC_ONLY_NOT_ACCEPTANCE"
    elif failed:
        status = "SUPPORTING_EVIDENCE_HAS_FAILURES"
    elif evidence_class == "AUTOMATED_TOOL":
        status = "AUTOMATED_SUPPORTING_EVIDENCE_NOT_CONFORMANCE"
    elif not_run:
        status = "SUPPORTING_EVIDENCE_INCOMPLETE"
    else:
        status = "SUPPORTING_ACCEPTANCE_EVIDENCE_NOT_CONFORMANCE"

    return {
        "status": status,
        "evidence_class": evidence_class,
        "passed_checks": passed,
        "failed_checks": failed,
        "not_run_checks": not_run,
        "schema_validation": "PASS",
        "privacy_prefilter": "PASS",
        "wcag_conformance_certified_by_validator": False,
        "accessibility_completeness_certified_by_validator": False,
        "real_user_acceptance_certified_by_validator": False,
        "production_ready_certified_by_validator": False,
    }


def validate_record(record: dict[str, Any]) -> dict[str, Any]:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(record)
    return validate_semantics(record)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Accessible AI supporting evidence")
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    result = validate_record(record)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
