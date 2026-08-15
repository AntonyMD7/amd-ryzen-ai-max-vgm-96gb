#!/usr/bin/env python3
"""F-04 Hardware Compatibility Commons governed external-source adapter v0.1.

The adapter does not fetch or scrape external datasets. It accepts only a narrow,
already-normalized external observation whose exact source snapshot digest, rights
review state, and privacy review state are explicit. It can currently promote
reviewed derived facts from the CC-BY-4.0 linuxhw/HWInfo dataset into a DAIS HCC
v0.2 *community-reported* candidate. LVFS metadata is intentionally reference-only
until a separate rights/redistribution review approves an import contract.

No external observation is promoted to VERIFIED_WORKING/VERIFIED_FAILING. The
result must pass the existing HCC public intake validator before it is emitted.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

import jsonschema

from hardware_compatibility_intake import IntakeError, _sensitive_findings, validate_public_report

VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "hardware-external-observation-v0.1.schema.json"
_COMMIT_RE = re.compile(r"^[a-fA-F0-9]{7,64}$")


class ExternalSourceError(ValueError):
    """Invalid or unsafe normalized external observation."""


class ExternalSourceBlocked(ExternalSourceError):
    """Valid external reference that is not authorized for public derived-fact import."""


def _load_schema(path: Path = DEFAULT_SCHEMA) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_schema(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ExternalSourceError("external observation must be a JSON object")
    validator = jsonschema.Draft202012Validator(_load_schema(), format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.absolute_path))
    if errors:
        rendered = []
        for error in errors:
            path = "$" + "".join(
                f"[{part}]" if isinstance(part, int) else f".{part}"
                for part in error.absolute_path
            )
            rendered.append(f"{path}:{error.message}")
        raise ExternalSourceError("schema: " + "; ".join(rendered))
    return payload


def _source_policy(source: dict[str, Any]) -> dict[str, str]:
    parsed = urlparse(source["dataset_url"])
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ExternalSourceError("source dataset URL must be credential-free canonical HTTPS without query/fragment")

    source_class = source["source_class"]
    if source_class == "LINUXHW_HWINFO_CC_BY_4_0":
        if parsed.hostname != "github.com" or not parsed.path.rstrip("/").startswith("/linuxhw/HWInfo"):
            raise ExternalSourceError("LINUXHW source must use the canonical github.com/linuxhw/HWInfo dataset URL")
        if source["license_expression"] != "CC-BY-4.0":
            raise ExternalSourceError("LINUXHW_HWINFO source must declare CC-BY-4.0")
        if source["rights_status"] != "DERIVED_FACTS_PUBLICATION_REVIEWED":
            raise ExternalSourceBlocked("LinuxHW normalized observation is reference-only until derived-fact publication rights are reviewed")
        if source["privacy_status"] != "NORMALIZED_IDENTIFIERS_REMOVED":
            raise ExternalSourceBlocked("LinuxHW observation is blocked until unique-device/private identifiers are removed and reviewed")
        return {"evidence_method": "COMMUNITY_REPORT", "reporter_class": "COMMUNITY"}

    if source_class == "LVFS_PUBLIC_METADATA_REFERENCE":
        if parsed.hostname not in {"fwupd.org", "www.fwupd.org", "cdn.fwupd.org", "fwupd.github.io"}:
            raise ExternalSourceError("LVFS source must use an approved fwupd/LVFS public metadata host")
        if source["license_expression"] != "UNRESOLVED_REFERENCE_ONLY":
            raise ExternalSourceError("LVFS import is not enabled; license/derived-fact rights must remain explicitly unresolved")
        if source["rights_status"] != "REFERENCE_ONLY":
            raise ExternalSourceError("LVFS source cannot be marked import-authorized in v0.1")
        raise ExternalSourceBlocked("LVFS public metadata remains reference-only until explicit rights/redistribution and field-level privacy review")

    raise ExternalSourceError("unsupported external source class")


def adapt_external_observation(payload: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    payload = _validate_schema(payload)
    source = payload["source"]
    source_policy = _source_policy(source)

    findings = _sensitive_findings(payload)
    if findings:
        raise ExternalSourceError("normalized external input failed public privacy prefilter: " + "; ".join(findings))

    try:
        datetime.fromisoformat(source["reviewed_at_utc"].replace("Z", "+00:00"))
        datetime.fromisoformat(payload["observation"]["observed_at_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExternalSourceError("invalid review/observation timestamp") from exc

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    report_id = "HCC-EXT-" + hashlib.sha256(canonical).hexdigest()[:20].upper()
    source_status = payload["observation"]["source_status"]
    hcc_status = "UNKNOWN" if source_status == "UNKNOWN" else "COMMUNITY_REPORTED"
    snapshot_ref = source["snapshot_ref"]

    report = {
        "schema_version": "0.2",
        "report_id": report_id,
        "hardware": dict(payload["hardware"]),
        "software": dict(payload["software"]),
        "configuration": list(payload["configuration"]),
        "observation": {
            "status": hcc_status,
            "observed_at_utc": payload["observation"]["observed_at_utc"],
            "summary": (
                f"External normalized observation {payload['observation']['summary_key']} "
                f"({source_status}); not independently reproduced by DAIS."
            ),
            "reproduction_runs": 0,
        },
        "evidence": {
            "method": source_policy["evidence_method"],
            "source_commit": snapshot_ref if _COMMIT_RE.fullmatch(snapshot_ref) else None,
            "artifact_hashes": [source["snapshot_sha256"]],
            "source_urls": [source["dataset_url"]],
            "reproduction_steps": [
                "Independently reproduce the reported behavior on matching non-production hardware before any verified compatibility promotion.",
                "Retain new DAIS test evidence and re-submit through the Hardware Compatibility Commons public intake contract.",
            ],
        },
        "provenance": {
            "reporter_class": source_policy["reporter_class"],
            "submitted_at_utc": source["reviewed_at_utc"],
            "review_status": "AUTOMATED_CHECKED",
        },
        "privacy": {
            "secrets_removed": True,
            "personal_data_removed": True,
            "private_network_data_removed": True,
            "unique_device_identifiers_removed": True,
            "raw_logs_excluded": True,
            "user_paths_removed": True,
        },
        "claims": {
            "universal_compatibility_guaranteed": False,
            "future_versions_guaranteed": False,
            "safe_to_auto_apply": False,
        },
        "limitations": [
            f"External source class: {source['source_class']}; declared source license: {source['license_expression']}.",
            f"Upstream normalized aggregate_count={payload['observation']['aggregate_count']} is not a DAIS reproduction count.",
            "This record imports a reviewed derived fact only; raw external logs, probe IDs, serials, UUIDs, hashes of unique devices, and user/network identifiers are excluded.",
            "External community evidence is never promoted by this adapter to VERIFIED_WORKING or VERIFIED_FAILING.",
            "The source snapshot SHA-256 binds bytes but does not by itself prove source authenticity, correctness, or currentness.",
            "Source-license recording and rights gating are not legal advice or a guarantee of downstream license compliance.",
        ],
    }

    try:
        intake = validate_public_report(report)
    except IntakeError as exc:
        raise ExternalSourceError(f"generated HCC report failed existing public intake: {exc}") from exc
    if intake["status"] != "ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED":
        raise ExternalSourceError("unexpected HCC public intake state")
    return report, intake


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt governed normalized external evidence into an HCC public-review candidate")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        report, intake = adapt_external_observation(payload)
    except ExternalSourceBlocked as exc:
        print(json.dumps({
            "status": "BLOCKED_EXTERNAL_SOURCE_NOT_IMPORTABLE",
            "reason": str(exc),
            "report_written": False,
            "compatibility_verified": False,
            "safe_to_auto_apply": False,
        }, indent=2, sort_keys=True))
        return 3
    except (OSError, json.JSONDecodeError, ExternalSourceError) as exc:
        print(json.dumps({
            "status": "REJECTED_EXTERNAL_SOURCE",
            "reason": str(exc),
            "report_written": False,
        }, indent=2, sort_keys=True))
        return 2

    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "ELIGIBLE_EXTERNAL_DERIVED_FACT_FOR_PUBLIC_REVIEW_NOT_VERIFIED",
        "report_id": report["report_id"],
        "report_sha256": intake["report_sha256"],
        "output": str(args.output),
        "compatibility_verified": False,
        "safe_to_auto_apply": False,
        "roadmap_complete": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
