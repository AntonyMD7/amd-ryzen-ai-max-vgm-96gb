#!/usr/bin/env python3
"""Hardware Compatibility Commons v0.3 conflict-preserving indexer.

Every input must first pass the public intake validator. Reports are grouped only
when their normalized hardware/software/configuration context is identical.
Contradictory verified observations remain contradictory; the index never turns
report counts into a universal compatibility or auto-apply claim.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from hardware_compatibility_intake import IntakeError, validate_public_report

VERSION = "0.3.0"
REAL_OBSERVATIONS = {"VERIFIED_WORKING", "VERIFIED_FAILING", "PARTIAL", "COMMUNITY_REPORTED", "UNKNOWN"}


class CompatibilityIndexError(ValueError):
    pass


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _context(report: dict[str, Any]) -> dict[str, Any]:
    return {
        "hardware": report["hardware"],
        "software": report["software"],
        "configuration": sorted(report["configuration"], key=lambda item: (item["key"], item["value"])),
    }


def _context_id(report: dict[str, Any]) -> str:
    return "HCCCTX-" + hashlib.sha256(_canonical(_context(report))).hexdigest()[:24]


def _aggregate_state(statuses: Counter[str]) -> str:
    if statuses["VERIFIED_WORKING"] and statuses["VERIFIED_FAILING"]:
        return "CONFLICT_REQUIRES_REVIEW"
    if statuses["VERIFIED_FAILING"]:
        return "FAILING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM"
    if statuses["VERIFIED_WORKING"]:
        return "WORKING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM"
    if statuses["PARTIAL"]:
        return "PARTIAL_EVIDENCE_ONLY"
    if statuses["COMMUNITY_REPORTED"]:
        return "COMMUNITY_EVIDENCE_ONLY"
    if statuses["UNKNOWN"]:
        return "UNKNOWN"
    return "SYNTHETIC_ONLY_NOT_REAL_HARDWARE_EVIDENCE"


def build_index(reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    unique: dict[str, dict[str, Any]] = {}
    for report in reports:
        try:
            validated = validate_public_report(report)
        except IntakeError as exc:
            raise CompatibilityIndexError(f"unsafe/invalid report refused: {exc}") from exc
        digest = validated["report_sha256"]
        unique.setdefault(digest, report)

    groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for digest, report in unique.items():
        groups.setdefault(_context_id(report), []).append((digest, report))

    entries: list[dict[str, Any]] = []
    for context_id in sorted(groups):
        items = groups[context_id]
        first = items[0][1]
        statuses = Counter(str(report["observation"]["status"]) for _, report in items)
        methods = Counter(str(report["evidence"]["method"]) for _, report in items)
        reviews = Counter(str(report["provenance"]["review_status"]) for _, report in items)
        real_count = sum(statuses[name] for name in REAL_OBSERVATIONS)
        synthetic_count = statuses["SYNTHETIC_CONFORMANCE_ONLY"]
        entries.append({
            "context_id": context_id,
            "context": _context(first),
            "report_count": len(items),
            "real_observation_count": real_count,
            "synthetic_conformance_count": synthetic_count,
            "status_counts": dict(sorted(statuses.items())),
            "evidence_method_counts": dict(sorted(methods.items())),
            "review_status_counts": dict(sorted(reviews.items())),
            "aggregate_state": _aggregate_state(statuses),
            "report_digests": sorted(digest for digest, _ in items),
            "claims": {
                "universal_compatibility_guaranteed": False,
                "future_versions_guaranteed": False,
                "safe_to_auto_apply": False,
                "majority_vote_used_as_truth": False,
                "synthetic_evidence_counted_as_real_hardware": False,
            },
        })

    return {
        "schema_version": "0.3",
        "indexer": {"name": "hardware_compatibility_index.py", "version": VERSION},
        "status": "PUBLIC_EVIDENCE_INDEX_NOT_COMPATIBILITY_CERTIFICATION",
        "input_report_count": len(unique),
        "context_count": len(entries),
        "contexts": entries,
        "claims": {
            "compatibility_certified": False,
            "conflicts_auto_resolved": False,
            "safe_to_auto_apply": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a conflict-preserving public hardware compatibility index")
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        payloads = [json.loads(path.read_text(encoding="utf-8")) for path in args.reports]
        result = build_index(payloads)
    except (OSError, json.JSONDecodeError, CompatibilityIndexError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
