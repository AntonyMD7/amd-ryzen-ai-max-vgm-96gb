#!/usr/bin/env python3
"""Read-only query layer for the Hardware Compatibility Commons index.

The query layer searches already-sanitized, already-indexed compatibility
contexts. It does not ingest raw device data, contact external services, resolve
conflicts, rank reports by popularity, or convert community evidence into a
compatibility certification.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class CompatibilityQueryError(ValueError):
    pass


ALLOWED_AGGREGATE_STATES = {
    "CONFLICT_REQUIRES_REVIEW",
    "FAILING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM",
    "WORKING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM",
    "PARTIAL_EVIDENCE_ONLY",
    "COMMUNITY_EVIDENCE_ONLY",
    "UNKNOWN",
    "SYNTHETIC_ONLY_NOT_REAL_HARDWARE_EVIDENCE",
}


def _text(value: object) -> str:
    return "" if value is None else str(value)


def _contains(value: object, needle: str | None) -> bool:
    if needle is None:
        return True
    return needle.casefold() in _text(value).casefold()


def _configuration_matches(configuration: object, key: str | None, value: str | None) -> bool:
    if key is None and value is None:
        return True
    if not isinstance(configuration, list):
        return False
    for item in configuration:
        if not isinstance(item, dict):
            continue
        key_match = _contains(item.get("key"), key)
        value_match = _contains(item.get("value"), value)
        if key_match and value_match:
            return True
    return False


def validate_index(index: dict[str, Any]) -> None:
    if index.get("schema_version") != "0.3":
        raise CompatibilityQueryError("query supports Hardware Commons index schema 0.3 only")
    if index.get("status") != "PUBLIC_EVIDENCE_INDEX_NOT_COMPATIBILITY_CERTIFICATION":
        raise CompatibilityQueryError("input is not a Hardware Commons public evidence index")
    contexts = index.get("contexts")
    if not isinstance(contexts, list):
        raise CompatibilityQueryError("index contexts must be an array")
    claims = index.get("claims")
    if not isinstance(claims, dict):
        raise CompatibilityQueryError("index claims are missing")
    for forbidden_true in ("compatibility_certified", "conflicts_auto_resolved", "safe_to_auto_apply"):
        if claims.get(forbidden_true) is not False:
            raise CompatibilityQueryError(f"unsafe index claim refused: {forbidden_true}")


def query_index(
    index: dict[str, Any],
    *,
    vendor: str | None = None,
    model: str | None = None,
    architecture: str | None = None,
    accelerator: str | None = None,
    os_name: str | None = None,
    os_version: str | None = None,
    driver: str | None = None,
    firmware: str | None = None,
    configuration_key: str | None = None,
    configuration_value: str | None = None,
    aggregate_state: str | None = None,
    include_synthetic: bool = False,
) -> dict[str, Any]:
    """Return matching exact-context entries while preserving evidence conflicts."""
    validate_index(index)
    if aggregate_state is not None and aggregate_state not in ALLOWED_AGGREGATE_STATES:
        raise CompatibilityQueryError("unsupported aggregate_state filter")

    active_filters = {
        "vendor": vendor,
        "model": model,
        "architecture": architecture,
        "accelerator": accelerator,
        "os": os_name,
        "os_version": os_version,
        "driver": driver,
        "firmware": firmware,
        "configuration_key": configuration_key,
        "configuration_value": configuration_value,
        "aggregate_state": aggregate_state,
        "include_synthetic": include_synthetic,
    }

    matches: list[dict[str, Any]] = []
    for entry in index["contexts"]:
        if not isinstance(entry, dict):
            raise CompatibilityQueryError("index contains malformed context entry")
        context = entry.get("context")
        if not isinstance(context, dict):
            raise CompatibilityQueryError("index context is malformed")
        hardware = context.get("hardware")
        software = context.get("software")
        if not isinstance(hardware, dict) or not isinstance(software, dict):
            raise CompatibilityQueryError("index hardware/software context is malformed")
        state = entry.get("aggregate_state")
        if state not in ALLOWED_AGGREGATE_STATES:
            raise CompatibilityQueryError("index contains unsupported aggregate state")

        if not include_synthetic and int(entry.get("real_observation_count", 0)) == 0:
            continue
        if aggregate_state is not None and state != aggregate_state:
            continue
        if not _contains(hardware.get("vendor"), vendor):
            continue
        if not _contains(hardware.get("model"), model):
            continue
        if not _contains(hardware.get("architecture"), architecture):
            continue
        if not _contains(hardware.get("accelerator"), accelerator):
            continue
        if not _contains(software.get("os"), os_name):
            continue
        if not _contains(software.get("os_version"), os_version):
            continue
        if not _contains(software.get("driver"), driver):
            continue
        if not _contains(software.get("firmware"), firmware):
            continue
        if not _configuration_matches(context.get("configuration"), configuration_key, configuration_value):
            continue

        matches.append(
            {
                "context_id": entry.get("context_id"),
                "context": context,
                "aggregate_state": state,
                "report_count": entry.get("report_count"),
                "real_observation_count": entry.get("real_observation_count"),
                "synthetic_conformance_count": entry.get("synthetic_conformance_count"),
                "status_counts": entry.get("status_counts"),
                "evidence_method_counts": entry.get("evidence_method_counts"),
                "review_status_counts": entry.get("review_status_counts"),
                "report_digests": entry.get("report_digests"),
                "claims": {
                    "compatibility_certified": False,
                    "universal_compatibility_guaranteed": False,
                    "safe_to_auto_apply": False,
                    "conflict_resolved_by_query": False,
                    "popularity_used_as_truth": False,
                },
            }
        )

    matches.sort(key=lambda item: str(item.get("context_id", "")))
    return {
        "schema_version": "0.1",
        "status": "MATCHES_FOUND" if matches else "NO_MATCH_NO_COMPATIBILITY_INFERENCE",
        "query_mode": "READ_ONLY_PUBLIC_SANITIZED_INDEX",
        "filters": active_filters,
        "match_count": len(matches),
        "matches": matches,
        "claims": {
            "compatibility_certified": False,
            "safe_to_auto_apply": False,
            "conflicts_auto_resolved": False,
            "absence_of_match_means_incompatible": False,
            "majority_vote_used_as_truth": False,
            "external_lookup_performed": False,
        },
    }


def load_index(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CompatibilityQueryError(f"unable to read index: {exc}") from exc
    if not isinstance(value, dict):
        raise CompatibilityQueryError("index must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Query a sanitized Hardware Compatibility Commons index")
    parser.add_argument("index", type=Path)
    parser.add_argument("--vendor")
    parser.add_argument("--model")
    parser.add_argument("--architecture")
    parser.add_argument("--accelerator")
    parser.add_argument("--os", dest="os_name")
    parser.add_argument("--os-version")
    parser.add_argument("--driver")
    parser.add_argument("--firmware")
    parser.add_argument("--configuration-key")
    parser.add_argument("--configuration-value")
    parser.add_argument("--aggregate-state", choices=sorted(ALLOWED_AGGREGATE_STATES))
    parser.add_argument("--include-synthetic", action="store_true")
    args = parser.parse_args()
    try:
        result = query_index(
            load_index(args.index),
            vendor=args.vendor,
            model=args.model,
            architecture=args.architecture,
            accelerator=args.accelerator,
            os_name=args.os_name,
            os_version=args.os_version,
            driver=args.driver,
            firmware=args.firmware,
            configuration_key=args.configuration_key,
            configuration_value=args.configuration_value,
            aggregate_state=args.aggregate_state,
            include_synthetic=args.include_synthetic,
        )
    except CompatibilityQueryError as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
