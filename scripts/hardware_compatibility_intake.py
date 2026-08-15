#!/usr/bin/env python3
"""Hardware Compatibility Commons v0.2 public intake validator.

The intake layer validates a deliberately narrow report schema and refuses likely
secrets, personal identifiers, private network identifiers, user home paths, and
unique-device fields before a report is eligible for public review.

It does not probe hardware, upload anything, redact in-place, update firmware,
change drivers, or convert a community report into a verified compatibility
claim. Refusal is preferred to lossy automatic redaction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

import jsonschema

VERSION = "0.2.0"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "hardware-compatibility-report-v0.2.schema.json"


class IntakeError(ValueError):
    """Raised when a report is unsafe or semantically invalid for public review."""


SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key-material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", re.I)),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("api-key-like", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer-token", re.compile(r"\bbearer\s+[A-Za-z0-9._~-]{16,}\b", re.I)),
    ("email-address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("mac-address", re.compile(r"\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b", re.I)),
    ("private-ipv4-10", re.compile(r"\b10(?:\.\d{1,3}){3}\b")),
    ("private-ipv4-192", re.compile(r"\b192\.168(?:\.\d{1,3}){2}\b")),
    ("private-ipv4-172", re.compile(r"\b172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}\b")),
    ("cgnat-ipv4", re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2}\b")),
    ("linux-user-path", re.compile(r"/home/[^/\s]+/", re.I)),
    ("macos-user-path", re.compile(r"/Users/[^/\s]+/", re.I)),
    ("windows-user-path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.I)),
)

FORBIDDEN_CONFIGURATION_KEY = re.compile(
    r"(?:^|[_.:/-])(?:serial|serialnumber|serial_number|uuid|machineid|machine_id|deviceid|device_id|mac|mac_address|hostname|username|user_name|ip|ip_address)(?:$|[_.:/-])",
    re.I,
)


def _iter_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{index}]")


def _schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema_errors(report: dict[str, Any]) -> list[str]:
    validator = jsonschema.Draft202012Validator(
        _schema(),
        format_checker=jsonschema.FormatChecker(),
    )
    errors = sorted(validator.iter_errors(report), key=lambda item: list(item.absolute_path))
    rendered: list[str] = []
    for error in errors:
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        rendered.append(f"schema:{path}:{error.message}")
    return rendered


def _sensitive_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    for path, value in _iter_strings(report):
        for label, pattern in SENSITIVE_PATTERNS:
            if pattern.search(value):
                findings.append(f"sensitive:{path}:{label}")
    for index, item in enumerate(report.get("configuration", [])):
        key = str(item.get("key", ""))
        if FORBIDDEN_CONFIGURATION_KEY.search(key):
            findings.append(f"sensitive:$.configuration[{index}].key:unique-or-network-identifier-field")
    return findings


def _semantic_findings(report: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    observation = report.get("observation", {})
    evidence = report.get("evidence", {})
    provenance = report.get("provenance", {})
    status = observation.get("status")
    method = evidence.get("method")
    runs = observation.get("reproduction_runs", 0)
    hashes = evidence.get("artifact_hashes", [])
    reporter = provenance.get("reporter_class")
    review = provenance.get("review_status")

    if status in {"VERIFIED_WORKING", "VERIFIED_FAILING"}:
        if method != "REPRODUCIBLE_TEST":
            findings.append("semantic:verified-status-requires-reproducible-test")
        if not isinstance(runs, int) or runs < 1:
            findings.append("semantic:verified-status-requires-at-least-one-reproduction-run")
        if not hashes:
            findings.append("semantic:verified-status-requires-artifact-hash")
        if review == "UNREVIEWED":
            findings.append("semantic:verified-status-cannot-be-unreviewed")

    if status == "SYNTHETIC_CONFORMANCE_ONLY":
        if reporter != "CI_SYNTHETIC":
            findings.append("semantic:synthetic-status-requires-ci-synthetic-reporter")
        if method != "SCHEMA_CONFORMANCE_ONLY":
            findings.append("semantic:synthetic-status-requires-schema-conformance-method")
        if runs != 0:
            findings.append("semantic:synthetic-status-must-not-claim-reproduction-runs")

    if reporter == "CI_SYNTHETIC" and status != "SYNTHETIC_CONFORMANCE_ONLY":
        findings.append("semantic:ci-synthetic-report-cannot-claim-real-hardware-outcome")

    if method == "VENDOR_DOCUMENTATION" and status in {"VERIFIED_WORKING", "VERIFIED_FAILING"}:
        findings.append("semantic:vendor-documentation-alone-is-not-observed-compatibility-proof")

    if method == "COMMUNITY_REPORT" and status in {"VERIFIED_WORKING", "VERIFIED_FAILING"}:
        findings.append("semantic:community-report-alone-is-not-verified-compatibility-proof")

    return findings


def validate_public_report(report: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise IntakeError("report must be a JSON object")

    findings = _schema_errors(report) + _sensitive_findings(report) + _semantic_findings(report)
    if findings:
        raise IntakeError("; ".join(findings))

    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return {
        "schema_version": "0.2",
        "validator": {"name": "hardware_compatibility_intake.py", "version": VERSION},
        "status": "ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED",
        "report_id": report["report_id"],
        "report_sha256": hashlib.sha256(canonical).hexdigest(),
        "schema_validation": "PASS",
        "privacy_prefilter": "PASS",
        "semantic_claim_check": "PASS",
        "uploaded": False,
        "compatibility_verified_by_intake": False,
        "human_review_completed_by_intake": False,
        "safe_to_auto_apply": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a sanitized Hardware Compatibility Commons public report")
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
        result = validate_public_report(payload)
    except (OSError, json.JSONDecodeError, IntakeError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
