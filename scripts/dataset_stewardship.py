#!/usr/bin/env python3
"""Privacy-first metadata primitives for dataset stewardship.

The reference layer consumes counts, booleans, identifiers and caller-supplied
record digests. It does not ingest dataset rows, run PII detection, clean data,
or publish artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from typing import Any


class DatasetError(ValueError):
    pass


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise DatasetError(f"{name} must be a bounded identifier")
    return value


def _nonnegative(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DatasetError(f"{name} must be a non-negative integer")
    return value


def quality_profile(data: dict[str, Any]) -> dict[str, Any]:
    rows = _nonnegative(data.get("row_count"), "row_count")
    fields = data.get("fields")
    if not isinstance(fields, list) or len(fields) > 500:
        raise DatasetError("fields must be a bounded list")
    normalized = []
    for item in fields:
        if not isinstance(item, dict):
            raise DatasetError("field entry must be an object")
        name = _id(item.get("name"), "field.name")
        missing = _nonnegative(item.get("missing_count"), "missing_count")
        invalid = _nonnegative(item.get("invalid_count"), "invalid_count")
        if missing > rows or invalid > rows:
            raise DatasetError("field counts cannot exceed row_count")
        normalized.append({
            "name": name,
            "missing_count": missing,
            "invalid_count": invalid,
            "missing_fraction": round(missing / rows, 6) if rows else None,
            "invalid_fraction": round(invalid / rows, 6) if rows else None,
        })
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-069",
        "row_count": rows,
        "fields": normalized,
        "semantics": {"dataset_rows_read": False, "quality_certified": False},
    }


def cleaning_plan(data: dict[str, Any]) -> dict[str, Any]:
    source_digest = data.get("source_sha256")
    if not isinstance(source_digest, str) or not HEX64.fullmatch(source_digest):
        raise DatasetError("source_sha256 must be a SHA-256 hex digest")
    operations = data.get("operations")
    if not isinstance(operations, list) or len(operations) > 100:
        raise DatasetError("operations must be a bounded list")
    allowed = {"drop_exact_duplicate", "normalize_whitespace", "map_missing_to_null", "filter_invalid_by_reviewed_rule"}
    normalized = []
    for item in operations:
        if not isinstance(item, dict) or item.get("operation") not in allowed:
            raise DatasetError("cleaning operation is not allowlisted")
        rule_id = _id(item.get("rule_id"), "rule_id")
        normalized.append({"operation": item["operation"], "rule_id": rule_id})
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-070",
        "source_sha256": source_digest.lower(),
        "operations": normalized,
        "execution": {"dataset_read": False, "dataset_modified": False, "output_written": False},
        "requirements": ["preserve immutable source", "version output", "record row-count deltas", "review semantic-loss risk", "retain provenance"],
    }


def pii_scan_plan(data: dict[str, Any]) -> dict[str, Any]:
    fields = data.get("field_classifications")
    if not isinstance(fields, dict) or not all(isinstance(k, str) and isinstance(v, bool) for k, v in fields.items()):
        raise DatasetError("field_classifications must be boolean facts")
    sensitive = sorted(_id(k, "field") for k, v in fields.items() if v)
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-071",
        "potentially_sensitive_fields": sensitive,
        "recommended_engine": "Presidio or an equivalently reviewed local PII engine",
        "requirements": ["scan locally where feasible", "do not upload raw sensitive rows by default", "measure false positives/negatives", "human-review high-impact redaction"],
        "execution": {"pii_scan_run": False, "data_uploaded": False, "data_redacted": False},
        "semantics": {"field_flag_is_pii_detection": False, "no_flags_means_no_pii": False},
    }


def duplicate_summary(data: dict[str, Any]) -> dict[str, Any]:
    digests = data.get("record_sha256")
    if not isinstance(digests, list) or len(digests) > 100000:
        raise DatasetError("record_sha256 must be a bounded list")
    normalized = []
    for value in digests:
        if not isinstance(value, str) or not HEX64.fullmatch(value):
            raise DatasetError("record digests must be SHA-256 hex")
        normalized.append(value.lower())
    counts = Counter(normalized)
    duplicate_groups = sorted((digest, count) for digest, count in counts.items() if count > 1)
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-072",
        "record_count": len(normalized),
        "unique_digest_count": len(counts),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_record_excess": sum(count - 1 for _, count in duplicate_groups),
        "duplicate_digests": [digest for digest, _ in duplicate_groups],
        "semantics": {"raw_rows_read": False, "semantic_near_duplicates_detected": False},
    }


def provenance_check(data: dict[str, Any]) -> dict[str, Any]:
    dataset_id = _id(data.get("dataset_id"), "dataset_id")
    source_id = _id(data.get("source_id"), "source_id")
    license_id = data.get("license_id")
    source_digest = data.get("source_sha256")
    consent_documented = data.get("consent_or_collection_basis_documented")
    if license_id is not None:
        license_id = _id(license_id, "license_id")
    if not isinstance(source_digest, str) or not HEX64.fullmatch(source_digest):
        raise DatasetError("source_sha256 must be a SHA-256 hex digest")
    if not isinstance(consent_documented, bool):
        raise DatasetError("consent_or_collection_basis_documented must be boolean")
    missing = []
    if license_id is None:
        missing.append("license_id")
    if not consent_documented:
        missing.append("consent_or_collection_basis_documented")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-073",
        "dataset_id": dataset_id,
        "source_id": source_id,
        "source_sha256": source_digest.lower(),
        "license_id": license_id,
        "missing_review_items": missing,
        "status": "REVIEW_REQUIRED" if missing else "METADATA_PREFLIGHT_PASSES",
        "semantics": {"legal_reuse_permission_proven": False, "data_rights_verified": False},
    }


def low_resource_language_plan(data: dict[str, Any]) -> dict[str, Any]:
    languages = data.get("languages")
    if not isinstance(languages, list) or not languages or len(languages) > 200:
        raise DatasetError("languages must contain 1..200 records")
    rows = []
    for item in languages:
        if not isinstance(item, dict):
            raise DatasetError("language entry must be an object")
        language = _id(item.get("language"), "language")
        count = _nonnegative(item.get("validated_example_count"), "validated_example_count")
        provenance = item.get("provenance_documented")
        consent = item.get("consent_or_collection_basis_documented")
        license_ok = item.get("license_reviewed")
        if not all(isinstance(v, bool) for v in (provenance, consent, license_ok)):
            raise DatasetError("language governance fields must be booleans")
        readiness = sum((provenance, consent, license_ok))
        rows.append({"language": language, "validated_example_count": count, "governance_checks_passed": readiness, "collection_ready": readiness == 3})
    rows.sort(key=lambda row: (row["collection_ready"], row["validated_example_count"], row["language"]))
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-075",
        "priority_review_order": rows,
        "requirements": ["community participation", "document consent/collection basis", "license/data-rights review", "cultural review", "quality sampling", "avoid extracting private communications by default"],
        "execution": {"data_collected": False, "community_contacted": False, "dataset_published": False},
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    functions = {
        "quality": quality_profile,
        "cleaning_plan": cleaning_plan,
        "pii_plan": pii_scan_plan,
        "duplicates": duplicate_summary,
        "provenance": provenance_check,
        "low_resource_languages": low_resource_language_plan,
    }
    fn = functions.get(mode)
    if fn is None:
        raise DatasetError("unsupported mode")
    return fn(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(evaluate(request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
