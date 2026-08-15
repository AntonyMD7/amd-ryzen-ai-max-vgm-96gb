#!/usr/bin/env python3
"""Validate DAIS Universal Evidence records and optional artifact hashes.

The validator never executes referenced artifacts. It fails closed on schema errors,
unsafe artifact paths, missing artifacts, or digest mismatches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

VERSION = "0.1.0"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def safe_artifact_path(root: Path, name: str) -> Path:
    candidate = Path(name)
    if candidate.is_absolute():
        raise ValueError("artifact name must be relative")
    root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("artifact path escapes artifact root") from exc
    return resolved


def validate_record(record: dict[str, Any], schema: dict[str, Any], *, artifact_root: Path | None = None) -> dict[str, Any]:
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(record),
        key=lambda e: list(e.absolute_path),
    )
    schema_errors = [
        {
            "path": ".".join(str(x) for x in error.absolute_path) or "$",
            "message": error.message,
        }
        for error in errors
    ]

    artifact_results = []
    artifact_failures = []
    if artifact_root is not None and not schema_errors:
        for item in record.get("artifacts", []):
            name = item["name"]
            expected = item["sha256"].lower()
            try:
                path = safe_artifact_path(artifact_root, name)
                if not path.is_file():
                    raise ValueError("artifact file does not exist")
                actual = sha256_file(path)
                ok = actual == expected
                result = {"name": name, "expected_sha256": expected, "actual_sha256": actual, "match": ok}
                artifact_results.append(result)
                if not ok:
                    artifact_failures.append({"name": name, "reason": "sha256 mismatch"})
            except (OSError, ValueError) as exc:
                artifact_failures.append({"name": name, "reason": str(exc)})

    status = "PASS" if not schema_errors and not artifact_failures else "FAIL"
    return {
        "schema_version": "0.1",
        "validator": {"name": "evidence_validate.py", "version": VERSION},
        "status": status,
        "schema_errors": schema_errors,
        "artifact_results": artifact_results,
        "artifact_failures": artifact_failures,
        "artifact_hash_check_requested": artifact_root is not None,
        "safety": {
            "artifacts_executed": False,
            "network_requests_performed": False,
            "files_changed": False,
        },
        "limitations": [
            "Schema validity and matching hashes do not prove that the claimed operation actually occurred.",
            "Trust in evidence still depends on producer identity, provenance, authorization and independent acceptance appropriate to the claim.",
            "This v0.1 record is not a replacement for signed in-toto/GitHub artifact attestations.",
        ],
    }


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Universal Evidence JSON and optional artifact SHA-256 values")
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--schema", type=Path, default=Path(__file__).parents[1] / "schemas" / "universal-evidence-v0.1.schema.json")
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    try:
        result = validate_record(load_object(args.evidence), load_object(args.schema), artifact_root=args.artifact_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"status": "FAIL", "input_error": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
