#!/usr/bin/env python3
"""Convert Gitleaks JSON into public-safe metadata without retaining secret values."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SENSITIVE_KEYS = {
    "secret", "match", "entropy", "author", "email", "message", "commit",
    "date", "symlinkfile", "tags",
}


class ReportError(ValueError):
    pass


def _metadata_fingerprint(finding: dict) -> str:
    # Deliberately excludes Secret and Match. File/line metadata is hashed and not emitted.
    material = {
        "rule_id": str(finding.get("RuleID", "UNKNOWN_RULE")),
        "file": str(finding.get("File", "")),
        "start_line": finding.get("StartLine"),
        "end_line": finding.get("EndLine"),
        "start_column": finding.get("StartColumn"),
        "end_column": finding.get("EndColumn"),
    }
    raw = json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def sanitize(raw_path: Path, exit_code: int, upstream_version: str, preflight: dict) -> dict:
    if raw_path.exists() and raw_path.stat().st_size:
        try:
            findings = json.loads(raw_path.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ReportError("raw scanner report is not valid JSON") from exc
    else:
        findings = []
    if not isinstance(findings, list) or any(not isinstance(x, dict) for x in findings):
        raise ReportError("raw scanner report must be a JSON array of objects")

    count = len(findings)
    if exit_code == 0 and count != 0:
        raise ReportError("scanner exit/report disagreement: success with findings")
    if exit_code == 1 and count == 0:
        raise ReportError("scanner exit/report disagreement: code 1 without findings")
    if exit_code not in (0, 1):
        status = "ERROR"
    else:
        status = "PASS" if count == 0 else "FINDINGS"

    rule_ids = sorted({str(x.get("RuleID", "UNKNOWN_RULE")) for x in findings})
    fingerprints = sorted({_metadata_fingerprint(x) for x in findings})
    result = {
        "schema_version": "1.0",
        "product": "DAIS Secret Exposure Detection Action",
        "roadmap_id": "P-049",
        "status": status,
        "upstream": {"name": "gitleaks", "version": upstream_version},
        "finding_count": count,
        "rule_count": len(rule_ids),
        "rule_ids": rule_ids,
        "finding_metadata_sha256": fingerprints,
        "scope": {
            "file_count": int(preflight["file_count"]),
            "total_bytes": int(preflight["total_bytes"]),
            "scope_sha256": str(preflight["scope_sha256"]),
            "git_history_scanned": False,
            "repository_code_executed": False,
        },
        "privacy": {
            "secret_values_retained": False,
            "matched_text_retained": False,
            "source_paths_retained": False,
            "raw_report_retained": False,
            "raw_stdout_stderr_retained": False,
        },
        "policy": {
            "repository_config_allowed": False,
            "repository_ignore_file_allowed": False,
            "inline_gitleaks_allow_allowed": False,
            "archive_recursion_depth": 0,
            "decode_recursion_depth": 0,
            "max_target_megabytes": 10,
        },
        "claims": {
            "all_secrets_absent": False,
            "credential_validity_checked": False,
            "git_history_clean": False,
            "repository_secure": False,
            "finding_is_active_credential": False,
            "roadmap_completion": False,
        },
    }
    serialized = json.dumps(result, sort_keys=True)
    lowered = serialized.lower()
    # Defense in depth: no raw scanner-only sensitive key names should be present as output fields.
    for key in SENSITIVE_KEYS:
        if f'"{key}"' in lowered:
            raise ReportError(f"sanitized output unexpectedly contains sensitive field name: {key}")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", required=True)
    parser.add_argument("--exit-code", required=True, type=int)
    parser.add_argument("--version", required=True)
    parser.add_argument("--preflight", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        preflight = json.loads(Path(args.preflight).read_text(encoding="utf-8"))
        result = sanitize(Path(args.raw), args.exit_code, args.version, preflight)
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"P049_STATUS={result['status']}")
        print(f"P049_FINDING_COUNT={result['finding_count']}")
        print(f"P049_RULE_COUNT={result['rule_count']}")
        print("P049_SECRET_VALUES_RETAINED=FALSE")
        return 0
    except (OSError, KeyError, TypeError, ValueError, ReportError, json.JSONDecodeError) as exc:
        print(f"P049_REPORT_SANITIZATION_REFUSED={type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
