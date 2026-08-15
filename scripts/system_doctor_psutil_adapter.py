#!/usr/bin/env python3
"""Bounded psutil adapter for Universal System Doctor F-02.

The adapter intentionally collects only coarse, non-identity system-capacity facts
from psutil and maps them into the existing System Doctor observation/fusion
contract. It never enumerates processes, users, network interfaces, connections,
open files, environment values, or credentials, and it performs no mutation.

This is a hosted/non-production acceptance adapter. A PASS does not prove physical
hardware health, root cause, production safety, or roadmap completion.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
from typing import Any

try:
    import psutil  # type: ignore
except ImportError:  # core repository CI does not need the optional adapter dependency
    psutil = None  # type: ignore

from system_doctor_evidence_fusion import fuse_case

VERSION = "0.1.0"


def _ratio_status(available: int, total: int, kind: str) -> tuple[str, str, str]:
    if total <= 0 or available < 0:
        return "UNKNOWN", f"{kind}_CAPACITY_UNKNOWN", f"VERIFY_{kind}_CAPACITY"
    ratio = available / total
    if ratio < 0.05:
        return "REVIEW", f"{kind}_HEADROOM_BELOW_5_PERCENT", f"RECHECK_{kind}_HEADROOM"
    if ratio < 0.10:
        return "NOTICE", f"{kind}_HEADROOM_BELOW_10_PERCENT", f"RECHECK_{kind}_HEADROOM"
    return "OK", f"{kind}_HEADROOM_AT_LEAST_10_PERCENT", f"RECHECK_{kind}_HEADROOM"


def collect_source_evidence(root: Path | None = None) -> dict[str, Any]:
    if psutil is None:
        raise RuntimeError("psutil is required for this optional bounded adapter")
    checked_root = root or Path(Path.cwd().anchor or "/")
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(checked_root))
    cpu_count = psutil.cpu_count(logical=True)

    return {
        "schema_version": "0.1",
        "collector": {
            "name": "system_doctor_psutil_adapter.py",
            "version": VERSION,
            "mode": "READ_ONLY_BOUNDED",
            "psutil_version": psutil.__version__,
        },
        "system": {
            "os_family": platform.system() or "Other",
            "architecture": platform.machine() or "unknown",
            "cpu_logical_count": int(cpu_count) if cpu_count is not None else None,
            "memory_total_bytes": int(memory.total),
            "memory_available_bytes": int(memory.available),
            "storage_total_bytes": int(disk.total),
            "storage_free_bytes": int(disk.free),
        },
        "privacy": {
            "username_collected": False,
            "hostname_collected": False,
            "network_addresses_collected": False,
            "network_interfaces_collected": False,
            "processes_collected": False,
            "process_command_lines_collected": False,
            "environment_values_collected": False,
            "credentials_collected": False,
            "user_files_opened": False,
        },
        "mutation": {
            "files_changed": False,
            "software_installed": False,
            "services_changed": False,
            "configuration_changed": False,
            "network_requested": False,
            "reboot_requested": False,
        },
        "limitations": [
            "Capacity/utilization facts are not hardware diagnostics.",
            "The adapter does not enumerate processes, users, interfaces, connections, or user files.",
            "Hosted-runner acceptance does not establish physical-device or production readiness.",
        ],
    }


def evidence_sha256(evidence: dict[str, Any]) -> str:
    payload = json.dumps(evidence, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def to_observation_case(
    evidence: dict[str, Any],
    *,
    collected_at: str,
    case_id: str = "f02-psutil-bounded",
    environment_class: str = "HOSTED_CI",
) -> dict[str, Any]:
    system = evidence["system"]
    digest = evidence_sha256(evidence)
    source = {
        "adapter": "PSUTIL",
        "tool": "psutil",
        "version": evidence["collector"]["psutil_version"],
        "evidence_sha256": digest,
        "collected_at": collected_at,
    }

    cpu_count = system["cpu_logical_count"]
    if cpu_count is None or cpu_count <= 0:
        cpu_status = "UNKNOWN"
        cpu_summary = "CPU_COUNT_UNKNOWN"
        cpu_recommendation = "VERIFY_CPU_INVENTORY"
    else:
        cpu_status = "OK"
        cpu_summary = "CPU_LOGICAL_COUNT_OBSERVED"
        cpu_recommendation = "NO_ACTION_FROM_THIS_OBSERVATION"

    memory_status, memory_summary, memory_verify = _ratio_status(
        system["memory_available_bytes"], system["memory_total_bytes"], "MEMORY"
    )
    storage_status, storage_summary, storage_verify = _ratio_status(
        system["storage_free_bytes"], system["storage_total_bytes"], "STORAGE"
    )

    recommendation_for_status = {
        "OK": "NO_ACTION_FROM_THIS_OBSERVATION",
        "NOTICE": "REVIEW_CAPACITY_TREND",
        "REVIEW": "REVIEW_CAPACITY_BEFORE_MUTATION",
        "UNKNOWN": "OBTAIN_SPECIALIST_EVIDENCE",
    }

    observations = [
        {
            "observation_id": "psutil-cpu-capacity",
            "domain": "CPU",
            "status": cpu_status,
            "confidence": "MEDIUM",
            "summary_key": cpu_summary,
            "recommendation_key": cpu_recommendation,
            "verification_key": "RECHECK_CPU_INVENTORY",
            "source": source,
        },
        {
            "observation_id": "psutil-memory-headroom",
            "domain": "MEMORY",
            "status": memory_status,
            "confidence": "MEDIUM",
            "summary_key": memory_summary,
            "recommendation_key": recommendation_for_status[memory_status],
            "verification_key": memory_verify,
            "source": source,
        },
        {
            "observation_id": "psutil-storage-headroom",
            "domain": "STORAGE",
            "status": storage_status,
            "confidence": "MEDIUM",
            "summary_key": storage_summary,
            "recommendation_key": recommendation_for_status[storage_status],
            "verification_key": storage_verify,
            "source": source,
        },
    ]

    os_family = system["os_family"]
    if os_family not in {"Linux", "Windows", "Darwin"}:
        os_family = "Other"

    return {
        "schema_version": "0.1",
        "case_id": case_id,
        "target": {
            "os_family": os_family,
            "architecture": system["architecture"],
            "environment_class": environment_class,
        },
        "observations": observations,
    }


def build_acceptance_record(*, collected_at: str | None = None) -> dict[str, Any]:
    timestamp = collected_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    evidence = collect_source_evidence()
    case = to_observation_case(evidence, collected_at=timestamp)
    fused = fuse_case(case)
    return {
        "record_version": "0.1",
        "source_evidence": evidence,
        "source_evidence_sha256": evidence_sha256(evidence),
        "observation_case": case,
        "fused_result": fused,
        "acceptance_claims": {
            "real_psutil_runtime_exercised": True,
            "identity_data_collected": False,
            "network_data_collected": False,
            "process_data_collected": False,
            "mutation_performed": False,
            "physical_hardware_health_proven": False,
            "root_cause_proven": False,
            "production_safe_to_infer": False,
            "roadmap_complete": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run bounded psutil System Doctor adapter")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record = build_acceptance_record()
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"SYSTEM_DOCTOR_PSUTIL_ADAPTER=PASS output={args.output}")
    print("PRODUCTION_SAFE_TO_INFER=FALSE")
    print("ROADMAP_COMPLETE=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
