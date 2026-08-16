#!/usr/bin/env python3
"""Validate DAIS Universal Evidence records and optional artifact hashes.

The validator never executes referenced artifacts. It fails closed on schema errors,
unsafe or ambiguous artifact paths, missing/oversized artifacts, digest mismatches, and
bounded-resource violations. Machine-readable results can be written atomically for CI
wrappers without changing evidence or artifact bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

VERSION = "0.2.0"
DEFAULT_MAX_ARTIFACTS = 256
DEFAULT_MAX_ARTIFACT_BYTES = 1024 * 1024 * 1024  # 1 GiB per referenced artifact


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_json(data: dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def safe_artifact_path(root: Path, name: str) -> Path:
    candidate = Path(name)
    if not name or candidate.is_absolute():
        raise ValueError("artifact name must be a non-empty relative path")
    root = root.resolve()
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("artifact path escapes artifact root") from exc
    return resolved


def validate_record(
    record: dict[str, Any],
    schema: dict[str, Any],
    *,
    artifact_root: Path | None = None,
    max_artifacts: int = DEFAULT_MAX_ARTIFACTS,
    max_artifact_bytes: int = DEFAULT_MAX_ARTIFACT_BYTES,
) -> dict[str, Any]:
    if max_artifacts < 0:
        raise ValueError("max_artifacts must be >= 0")
    if max_artifact_bytes < 0:
        raise ValueError("max_artifact_bytes must be >= 0")

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

    artifacts = record.get("artifacts", []) if isinstance(record.get("artifacts", []), list) else []
    artifact_results: list[dict[str, Any]] = []
    artifact_failures: list[dict[str, str]] = []

    names = [item.get("name") for item in artifacts if isinstance(item, dict)]
    duplicates = sorted({name for name in names if isinstance(name, str) and names.count(name) > 1})
    for name in duplicates:
        artifact_failures.append({"name": name, "reason": "duplicate artifact name is ambiguous"})

    if len(artifacts) > max_artifacts:
        artifact_failures.append(
            {
                "name": "$artifacts",
                "reason": f"artifact count {len(artifacts)} exceeds configured maximum {max_artifacts}",
            }
        )

    if artifact_root is not None and not schema_errors and len(artifacts) <= max_artifacts and not duplicates:
        for item in artifacts:
            name = item["name"]
            expected = item["sha256"].lower()
            try:
                path = safe_artifact_path(artifact_root, name)
                if not path.is_file():
                    raise ValueError("artifact file does not exist or is not a regular file")
                size = path.stat().st_size
                if size > max_artifact_bytes:
                    raise ValueError(f"artifact size {size} exceeds configured maximum {max_artifact_bytes}")
                actual = sha256_file(path)
                ok = actual == expected
                result = {
                    "name": name,
                    "size_bytes": size,
                    "expected_sha256": expected,
                    "actual_sha256": actual,
                    "match": ok,
                }
                artifact_results.append(result)
                if not ok:
                    artifact_failures.append({"name": name, "reason": "sha256 mismatch"})
            except (OSError, ValueError) as exc:
                artifact_failures.append({"name": name, "reason": str(exc)})

    status = "PASS" if not schema_errors and not artifact_failures else "FAIL"
    verified_count = sum(1 for item in artifact_results if item["match"])
    return {
        "schema_version": "0.2",
        "validator": {"name": "evidence_validate.py", "version": VERSION},
        "status": status,
        "record_sha256": sha256_json(record),
        "schema_sha256": sha256_json(schema),
        "schema_errors": schema_errors,
        "artifact_results": artifact_results,
        "artifact_failures": artifact_failures,
        "counts": {
            "declared_artifacts": len(artifacts),
            "verified_artifacts": verified_count,
            "schema_errors": len(schema_errors),
            "artifact_failures": len(artifact_failures),
        },
        "bounds": {
            "max_artifacts": max_artifacts,
            "max_artifact_bytes": max_artifact_bytes,
        },
        "artifact_hash_check_requested": artifact_root is not None,
        "safety": {
            "artifacts_executed": False,
            "network_requests_performed": False,
            "files_changed": False,
        },
        "limitations": [
            "Schema validity and matching hashes do not prove that the claimed operation actually occurred.",
            "Trust in evidence still depends on producer identity, provenance, authorization and independent acceptance appropriate to the claim.",
            "This validator does not replace signed in-toto/GitHub artifact attestations or verify producer identity.",
        ],
    }


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent), text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Universal Evidence JSON and optional artifact SHA-256 values")
    parser.add_argument("evidence", type=Path)
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parents[1] / "schemas" / "universal-evidence-v0.1.schema.json",
    )
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--result-file", type=Path, help="Atomically write the complete machine-readable validation result")
    parser.add_argument("--max-artifacts", type=int, default=DEFAULT_MAX_ARTIFACTS)
    parser.add_argument("--max-artifact-bytes", type=int, default=DEFAULT_MAX_ARTIFACT_BYTES)
    args = parser.parse_args()
    try:
        result = validate_record(
            load_object(args.evidence),
            load_object(args.schema),
            artifact_root=args.artifact_root,
            max_artifacts=args.max_artifacts,
            max_artifact_bytes=args.max_artifact_bytes,
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {"status": "FAIL", "input_error": str(exc), "validator": {"name": "evidence_validate.py", "version": VERSION}}
        if args.result_file:
            write_json_atomic(args.result_file, result)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 2

    if args.result_file:
        write_json_atomic(args.result_file, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
