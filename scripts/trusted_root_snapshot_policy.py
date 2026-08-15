#!/usr/bin/env python3
"""Evaluate archived trusted-root snapshot metadata against a local refresh policy.

This module does not fetch TUF metadata, verify TUF signatures, validate a
Sigstore TrustedRoot, perform artifact cryptography, query revocation state, or
prove that a root is current. It evaluates a deliberately narrow archival
record so an offline verifier can fail closed when its *local* refresh window
has elapsed and can verify an optional hash link to the previous record.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SNAPSHOT_ID = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
VERSION = re.compile(r"^v?[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


class SnapshotPolicyError(ValueError):
    """Raised when an archival record violates the v0.1 contract."""


def _exact_keys(value: object, expected: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise SnapshotPolicyError(f"{field} fields must be exactly {sorted(expected)}")
    return value


def _parse_utc(value: object, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise SnapshotPolicyError(f"{field} must be RFC3339 UTC ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise SnapshotPolicyError(f"{field} is not a valid RFC3339 timestamp") from exc
    if parsed.utcoffset() != timedelta(0):
        raise SnapshotPolicyError(f"{field} must be UTC")
    return parsed.astimezone(timezone.utc)


def _sha(value: object, field: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise SnapshotPolicyError(f"{field} must be lowercase SHA-256")
    return value


def validate_record(record: dict[str, Any]) -> None:
    _exact_keys(
        record,
        {"schema_version", "snapshot_id", "source", "acquired_at", "trusted_root", "tooling", "refresh_policy", "claims"},
        "record",
    )
    if record.get("schema_version") != "0.1":
        raise SnapshotPolicyError("unsupported schema_version")
    if not isinstance(record.get("snapshot_id"), str) or not SNAPSHOT_ID.fullmatch(record["snapshot_id"]):
        raise SnapshotPolicyError("invalid snapshot_id")

    source = _exact_keys(record.get("source"), {"ecosystem", "retrieval_method", "source_uri"}, "source")
    if source.get("ecosystem") != "SIGSTORE_PUBLIC_GOOD":
        raise SnapshotPolicyError("v0.1 supports SIGSTORE_PUBLIC_GOOD records only")
    if source.get("retrieval_method") not in {"TUF_CLIENT", "COSIGN_INITIALIZE"}:
        raise SnapshotPolicyError("unsupported retrieval_method")
    uri = source.get("source_uri")
    if not isinstance(uri, str) or len(uri) > 1000:
        raise SnapshotPolicyError("source.source_uri must be a bounded HTTPS URI")
    parsed_uri = urlparse(uri)
    if parsed_uri.scheme != "https" or not parsed_uri.netloc or parsed_uri.username or parsed_uri.password:
        raise SnapshotPolicyError("source.source_uri must be HTTPS without embedded credentials")

    acquired = _parse_utc(record.get("acquired_at"), "acquired_at")

    root = _exact_keys(
        record.get("trusted_root"),
        {"media_type", "sha256", "size_bytes", "certificate_authority_count", "transparency_log_count", "timestamp_authority_count"},
        "trusted_root",
    )
    media_type = root.get("media_type")
    if not isinstance(media_type, str) or not media_type.startswith("application/vnd.dev.sigstore.trustedroot.v"):
        raise SnapshotPolicyError("trusted_root.media_type is not a Sigstore TrustedRoot media type")
    _sha(root.get("sha256"), "trusted_root.sha256")
    if not isinstance(root.get("size_bytes"), int) or isinstance(root.get("size_bytes"), bool) or root["size_bytes"] <= 0:
        raise SnapshotPolicyError("trusted_root.size_bytes must be a positive integer")
    for field in ("certificate_authority_count", "transparency_log_count", "timestamp_authority_count"):
        value = root.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise SnapshotPolicyError(f"trusted_root.{field} must be a positive integer")

    tooling = _exact_keys(record.get("tooling"), {"verifier", "verifier_version"}, "tooling")
    if tooling.get("verifier") != "cosign":
        raise SnapshotPolicyError("v0.1 supports cosign verifier records only")
    if not isinstance(tooling.get("verifier_version"), str) or not VERSION.fullmatch(tooling["verifier_version"]):
        raise SnapshotPolicyError("tooling.verifier_version must be a concrete semantic version")

    policy = _exact_keys(
        record.get("refresh_policy"),
        {"max_age_hours", "refresh_due_at", "previous_snapshot_record_sha256", "offline_import_approved"},
        "refresh_policy",
    )
    max_age = policy.get("max_age_hours")
    if not isinstance(max_age, int) or isinstance(max_age, bool) or not 1 <= max_age <= 8760:
        raise SnapshotPolicyError("refresh_policy.max_age_hours must be an integer from 1 to 8760")
    due = _parse_utc(policy.get("refresh_due_at"), "refresh_policy.refresh_due_at")
    if due <= acquired:
        raise SnapshotPolicyError("refresh_due_at must be after acquired_at")
    if due > acquired + timedelta(hours=max_age):
        raise SnapshotPolicyError("refresh_due_at exceeds the declared max_age_hours")
    _sha(policy.get("previous_snapshot_record_sha256"), "refresh_policy.previous_snapshot_record_sha256", nullable=True)
    if not isinstance(policy.get("offline_import_approved"), bool):
        raise SnapshotPolicyError("refresh_policy.offline_import_approved must be boolean")

    claims = _exact_keys(
        record.get("claims"),
        {
            "tuf_metadata_verified_by_this_module",
            "trusted_root_current_proven",
            "future_revocation_awareness_proven",
            "artifact_goodness_proven",
            "semantic_truth_proven",
            "production_readiness_proven",
            "roadmap_completion_proven",
        },
        "claims",
    )
    for field, value in claims.items():
        if value is not False:
            raise SnapshotPolicyError(f"claims.{field} must remain false in v0.1")


def evaluate(
    record: dict[str, Any],
    *,
    as_of: datetime,
    previous_record_bytes: bytes | None = None,
) -> dict[str, Any]:
    validate_record(record)
    if as_of.tzinfo is None or as_of.utcoffset() != timedelta(0):
        raise SnapshotPolicyError("as_of must be timezone-aware UTC")
    as_of = as_of.astimezone(timezone.utc)
    acquired = _parse_utc(record["acquired_at"], "acquired_at")
    due = _parse_utc(record["refresh_policy"]["refresh_due_at"], "refresh_policy.refresh_due_at")
    if as_of < acquired:
        raise SnapshotPolicyError("as_of predates snapshot acquisition")

    expected_previous = record["refresh_policy"]["previous_snapshot_record_sha256"]
    if expected_previous is None:
        previous_link = "NOT_DECLARED"
        if previous_record_bytes is not None:
            raise SnapshotPolicyError("previous record supplied but no previous hash is declared")
    elif previous_record_bytes is None:
        previous_link = "DECLARED_NOT_VERIFIED"
    else:
        observed = hashlib.sha256(previous_record_bytes).hexdigest()
        previous_link = "VERIFIED" if observed == expected_previous else "MISMATCH"

    within_window = as_of <= due
    local_status = "WITHIN_LOCAL_REFRESH_WINDOW" if within_window else "LOCAL_REFRESH_OVERDUE"
    chain_ok = previous_link != "MISMATCH"
    policy_status = "ARCHIVE_POLICY_SATISFIED" if within_window and chain_ok else "ARCHIVE_POLICY_REJECTED"

    return {
        "schema_version": "0.1",
        "snapshot_id": record["snapshot_id"],
        "policy_status": policy_status,
        "local_refresh_status": local_status,
        "previous_snapshot_link_status": previous_link,
        "offline_import_approved_recorded": record["refresh_policy"]["offline_import_approved"],
        "tuf_metadata_verified_by_this_module": False,
        "trusted_root_current_proven": False,
        "future_revocation_awareness_proven": False,
        "cryptography_performed": False,
        "network_contact_performed": False,
        "artifact_goodness_proven": False,
        "semantic_truth_proven": False,
        "production_readiness_proven": False,
        "roadmap_completion_proven": False,
    }


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SnapshotPolicyError(f"{path} must contain a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    parser.add_argument("--as-of", required=True, help="Explicit RFC3339 UTC evaluation time, e.g. 2026-08-15T12:00:00Z")
    parser.add_argument("--previous-record", type=Path)
    args = parser.parse_args(argv)
    as_of = _parse_utc(args.as_of, "--as-of")
    previous = args.previous_record.read_bytes() if args.previous_record else None
    result = evaluate(load_json(args.record), as_of=as_of, previous_record_bytes=previous)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["policy_status"] == "ARCHIVE_POLICY_SATISFIED" else 3


if __name__ == "__main__":
    raise SystemExit(main())
