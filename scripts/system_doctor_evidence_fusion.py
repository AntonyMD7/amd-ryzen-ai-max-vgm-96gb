#!/usr/bin/env python3
"""Universal System Doctor diagnostic evidence fusion v0.1.

This module consumes *already-collected*, privacy-safe diagnostic observations and
combines them without executing probes, repairs, installers, network calls, or
vendor tools. It is deliberately an interpretation/evidence boundary, not a new
cross-platform instrumentation engine.

Truth boundary:
- a fused result summarizes supplied observations only;
- conflicting observations remain visible;
- UNKNOWN never becomes OK;
- recommendations are plan keys, not commands;
- no result authorizes mutation or proves hardware health, root cause, safety,
  production readiness, or roadmap completion.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"

DOMAINS = {
    "CPU",
    "MEMORY",
    "STORAGE",
    "THERMAL",
    "POWER",
    "OS",
    "DRIVER",
    "NETWORK",
    "SERVICE",
    "SECURITY",
    "PERIPHERAL",
}
STATUSES = {"OK", "NOTICE", "REVIEW", "UNKNOWN"}
CONFIDENCE = {"LOW", "MEDIUM", "HIGH"}
ADAPTERS = {
    "SYSTEM_DOCTOR_BASELINE",
    "PSUTIL",
    "OSQUERY",
    "SMARTCTL",
    "WINDOWS_CIM",
    "MACOS_NATIVE",
    "LINUX_NATIVE",
    "VENDOR_DIAGNOSTIC",
    "OTHER_BOUNDED_ADAPTER",
}
ENVIRONMENT_CLASSES = {"SYNTHETIC", "HOSTED_CI", "PHYSICAL_NON_PRODUCTION", "PRODUCTION_OBSERVATION"}

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]{0,95}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TOOL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+:/()-]{0,95}$")
_VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+:/()-]{0,95}$")

_SENSITIVE_PATTERNS = (
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
    re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    re.compile(r"(?:^|[\\/])Users[\\/][^\\/\s]+", re.I),
    re.compile(r"(?:^|/)home/[^/\s]+", re.I),
    re.compile(r"(?:^|/)Users/[^/\s]+"),
    re.compile(r"https?://[^/\s:@]+:[^/\s@]+@", re.I),
    re.compile(r"\b(?:ghp_|github_pat_|AKIA)[A-Za-z0-9_\-]{8,}\b"),
)


class FusionError(ValueError):
    """Fail-closed input validation error."""


def _require_keys(obj: dict[str, Any], required: set[str], allowed: set[str], where: str) -> None:
    missing = required - obj.keys()
    extra = obj.keys() - allowed
    if missing:
        raise FusionError(f"{where}: missing keys: {sorted(missing)}")
    if extra:
        raise FusionError(f"{where}: unsupported keys: {sorted(extra)}")


def _bounded_id(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise FusionError(f"{where}: invalid identifier")
    return value


def _bounded_key(value: Any, where: str) -> str:
    if not isinstance(value, str) or not _KEY_RE.fullmatch(value):
        raise FusionError(f"{where}: expected bounded uppercase semantic key")
    return value


def _safe_literal(value: str, where: str) -> None:
    for pattern in _SENSITIVE_PATTERNS:
        if pattern.search(value):
            raise FusionError(f"{where}: possible sensitive literal refused")


def _parse_utc_timestamp(value: Any, where: str) -> str:
    if not isinstance(value, str) or len(value) > 40 or not value.endswith("Z"):
        raise FusionError(f"{where}: expected UTC RFC3339-like timestamp ending in Z")
    try:
        datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise FusionError(f"{where}: invalid timestamp") from exc
    return value


def _validate_source(source: Any, where: str) -> dict[str, str]:
    if not isinstance(source, dict):
        raise FusionError(f"{where}: source must be an object")
    keys = {"adapter", "tool", "version", "evidence_sha256", "collected_at"}
    _require_keys(source, keys, keys, where)

    adapter = source["adapter"]
    if adapter not in ADAPTERS:
        raise FusionError(f"{where}.adapter: unsupported adapter")
    tool = source["tool"]
    version = source["version"]
    if not isinstance(tool, str) or not _TOOL_RE.fullmatch(tool):
        raise FusionError(f"{where}.tool: invalid tool label")
    if not isinstance(version, str) or not _VERSION_RE.fullmatch(version):
        raise FusionError(f"{where}.version: invalid version label")
    _safe_literal(tool, f"{where}.tool")
    _safe_literal(version, f"{where}.version")

    digest = source["evidence_sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        raise FusionError(f"{where}.evidence_sha256: expected lowercase SHA-256")

    return {
        "adapter": adapter,
        "tool": tool,
        "version": version,
        "evidence_sha256": digest,
        "collected_at": _parse_utc_timestamp(source["collected_at"], f"{where}.collected_at"),
    }


def validate_case(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise FusionError("case: expected object")
    keys = {"schema_version", "case_id", "target", "observations"}
    _require_keys(data, keys, keys, "case")
    if data["schema_version"] != "0.1":
        raise FusionError("case.schema_version: unsupported version")
    case_id = _bounded_id(data["case_id"], "case.case_id")

    target = data["target"]
    if not isinstance(target, dict):
        raise FusionError("case.target: expected object")
    target_keys = {"os_family", "architecture", "environment_class"}
    _require_keys(target, target_keys, target_keys, "case.target")
    os_family = target["os_family"]
    architecture = target["architecture"]
    environment_class = target["environment_class"]
    if os_family not in {"Linux", "Windows", "Darwin", "Other"}:
        raise FusionError("case.target.os_family: unsupported family")
    if not isinstance(architecture, str) or not _TOOL_RE.fullmatch(architecture):
        raise FusionError("case.target.architecture: invalid architecture label")
    if environment_class not in ENVIRONMENT_CLASSES:
        raise FusionError("case.target.environment_class: invalid environment class")
    _safe_literal(architecture, "case.target.architecture")

    observations = data["observations"]
    if not isinstance(observations, list) or not 1 <= len(observations) <= 128:
        raise FusionError("case.observations: expected 1..128 observations")

    seen_ids: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(observations):
        where = f"case.observations[{index}]"
        if not isinstance(raw, dict):
            raise FusionError(f"{where}: expected object")
        obs_keys = {
            "observation_id",
            "domain",
            "status",
            "confidence",
            "summary_key",
            "recommendation_key",
            "verification_key",
            "source",
        }
        _require_keys(raw, obs_keys, obs_keys, where)
        observation_id = _bounded_id(raw["observation_id"], f"{where}.observation_id")
        if observation_id in seen_ids:
            raise FusionError(f"{where}.observation_id: duplicate")
        seen_ids.add(observation_id)
        domain = raw["domain"]
        status = raw["status"]
        confidence = raw["confidence"]
        if domain not in DOMAINS:
            raise FusionError(f"{where}.domain: unsupported domain")
        if status not in STATUSES:
            raise FusionError(f"{where}.status: unsupported status")
        if confidence not in CONFIDENCE:
            raise FusionError(f"{where}.confidence: unsupported confidence")
        normalized.append(
            {
                "observation_id": observation_id,
                "domain": domain,
                "status": status,
                "confidence": confidence,
                "summary_key": _bounded_key(raw["summary_key"], f"{where}.summary_key"),
                "recommendation_key": _bounded_key(raw["recommendation_key"], f"{where}.recommendation_key"),
                "verification_key": _bounded_key(raw["verification_key"], f"{where}.verification_key"),
                "source": _validate_source(raw["source"], f"{where}.source"),
            }
        )

    return {
        "schema_version": "0.1",
        "case_id": case_id,
        "target": {
            "os_family": os_family,
            "architecture": architecture,
            "environment_class": environment_class,
        },
        "observations": normalized,
    }


def _fuse_domain(observations: list[dict[str, Any]]) -> tuple[str, bool]:
    statuses = {item["status"] for item in observations}
    conflict = "OK" in statuses and ("REVIEW" in statuses or "NOTICE" in statuses)
    if conflict:
        return "CONFLICT_REQUIRES_REVIEW", True
    if "REVIEW" in statuses:
        return "REVIEW", False
    if "NOTICE" in statuses:
        return "NOTICE", False
    if statuses == {"OK"}:
        return "OK", False
    if statuses == {"UNKNOWN"}:
        return "UNKNOWN", False
    if "UNKNOWN" in statuses and "OK" in statuses:
        return "PARTIAL_UNKNOWN", False
    return "UNKNOWN", False


def fuse_case(data: Any) -> dict[str, Any]:
    case = validate_case(data)
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for observation in case["observations"]:
        grouped[observation["domain"]].append(observation)

    domains: list[dict[str, Any]] = []
    has_review = False
    has_unknown = False
    has_conflict = False
    for domain in sorted(grouped):
        observations = grouped[domain]
        state, conflict = _fuse_domain(observations)
        has_conflict |= conflict
        has_review |= state in {"REVIEW", "CONFLICT_REQUIRES_REVIEW"}
        has_unknown |= state in {"UNKNOWN", "PARTIAL_UNKNOWN"}
        domains.append(
            {
                "domain": domain,
                "state": state,
                "observation_ids": [item["observation_id"] for item in observations],
                "recommendation_keys": sorted({item["recommendation_key"] for item in observations if item["status"] != "OK"}),
                "verification_keys": sorted({item["verification_key"] for item in observations}),
                "conflict_preserved": conflict,
            }
        )

    if has_conflict:
        overall = "CONFLICT_REQUIRES_REVIEW"
    elif has_review:
        overall = "REVIEW_REQUIRED"
    elif has_unknown:
        overall = "INCOMPLETE_EVIDENCE"
    elif any(item["state"] == "NOTICE" for item in domains):
        overall = "NOTICE"
    else:
        overall = "NO_ISSUE_OBSERVED_IN_SUPPLIED_SCOPE"

    canonical = {
        "schema_version": "0.1",
        "engine": {"name": "system_doctor_evidence_fusion.py", "version": VERSION, "mode": "READ_ONLY_INTERPRETATION"},
        "case_id": case["case_id"],
        "target": case["target"],
        "overall_state": overall,
        "domains": domains,
        "source_evidence_sha256": sorted({item["source"]["evidence_sha256"] for item in case["observations"]}),
        "claims": {
            "root_cause_proven": False,
            "hardware_health_proven": False,
            "repair_authorized": False,
            "production_safe_to_infer": False,
            "roadmap_complete": False,
        },
        "mutation": {
            "probe_executed_by_fusion": False,
            "repair_executed": False,
            "file_changed": False,
            "service_changed": False,
            "software_installed": False,
            "network_requested": False,
            "reboot_requested": False,
        },
        "limitations": [
            "The fusion result summarizes only supplied bounded observations.",
            "Source-tool correctness and source evidence authenticity are not established by this module.",
            "Conflicting observations require review and are never resolved by majority vote.",
            "Recommendations are semantic plan keys, not executable repair commands.",
        ],
    }
    canonical_bytes = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    canonical["result_sha256"] = hashlib.sha256(canonical_bytes).hexdigest()
    return canonical


def main() -> int:
    parser = argparse.ArgumentParser(description="Fuse bounded System Doctor observations without executing probes or repairs")
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    result = fuse_case(data)
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
