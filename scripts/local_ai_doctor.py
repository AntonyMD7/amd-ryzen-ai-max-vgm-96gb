#!/usr/bin/env python3
"""Local AI Doctor v0.2 evidence-gated orchestration layer.

This module composes existing DAIS public reference helpers into one cautious
answer to: what is known, what remains unknown, what might fit, which backend
paths should be reviewed, and what evidence is still required.

It deliberately does *not* download a model, install software, contact a cloud
provider, benchmark inference, allocate accelerator memory, change drivers, or
claim that a model/backend will run. Backend support is allowed to come only from
current upstream documentation plus exact workload acceptance evidence outside
this module.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from local_ai_setup_planner import BACKENDS, Signals, build_plan, normalized_system
from local_cloud_decision import Constraints, decide
from model_memory_estimator import estimate

VERSION = "0.2.0"
GIB = 1024 ** 3
ACCELERATOR_VENDORS = {"nvidia", "amd", "apple", "intel", "cpu", "other", "unknown"}
EVIDENCE_STATES = {"VERIFIED_RUNTIME", "OBSERVED_ONLY", "UNKNOWN"}
SENSITIVITY = {"public", "internal", "sensitive", "regulated"}


class LocalAIDoctorError(ValueError):
    """Raised when normalized public planning input violates the contract."""


@dataclass(frozen=True)
class MachineFacts:
    system: str
    architecture: str
    accelerator_vendor: str
    accelerator_evidence: str
    usable_memory_gib: float | None
    installed_backends: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkloadFacts:
    params_billions: float
    bits_per_weight: float
    sensitivity: str = "internal"
    offline_required: bool = False
    remote_api_allowed: bool = False
    low_bandwidth: bool = False
    availability_priority: str = "normal"


def _validate_machine(machine: MachineFacts) -> MachineFacts:
    system = normalized_system(machine.system)
    if system not in {"linux", "windows", "macos", "unknown"}:
        raise LocalAIDoctorError("system must be linux, windows, macos, or unknown")
    architecture = machine.architecture.strip()
    if not architecture or len(architecture) > 80:
        raise LocalAIDoctorError("architecture must be a short non-empty label")
    vendor = machine.accelerator_vendor.lower().strip()
    if vendor not in ACCELERATOR_VENDORS:
        raise LocalAIDoctorError("unknown accelerator_vendor")
    evidence = machine.accelerator_evidence.upper().strip()
    if evidence not in EVIDENCE_STATES:
        raise LocalAIDoctorError("unknown accelerator_evidence")
    if machine.usable_memory_gib is not None and machine.usable_memory_gib <= 0:
        raise LocalAIDoctorError("usable_memory_gib must be > 0 when supplied")
    installed = tuple(dict.fromkeys(machine.installed_backends))
    if any(item not in BACKENDS for item in installed):
        raise LocalAIDoctorError("installed_backends contains an unsupported label")
    return MachineFacts(
        system=system,
        architecture=architecture,
        accelerator_vendor=vendor,
        accelerator_evidence=evidence,
        usable_memory_gib=machine.usable_memory_gib,
        installed_backends=installed,
    )


def _validate_workload(workload: WorkloadFacts) -> WorkloadFacts:
    if workload.params_billions <= 0:
        raise LocalAIDoctorError("params_billions must be > 0")
    if workload.bits_per_weight <= 0 or workload.bits_per_weight > 64:
        raise LocalAIDoctorError("bits_per_weight must be > 0 and <= 64")
    sensitivity = workload.sensitivity.lower().strip()
    if sensitivity not in SENSITIVITY:
        raise LocalAIDoctorError("unknown sensitivity")
    if workload.availability_priority not in {"normal", "high"}:
        raise LocalAIDoctorError("availability_priority must be normal or high")
    return WorkloadFacts(
        params_billions=workload.params_billions,
        bits_per_weight=workload.bits_per_weight,
        sensitivity=sensitivity,
        offline_required=bool(workload.offline_required),
        remote_api_allowed=bool(workload.remote_api_allowed),
        low_bandwidth=bool(workload.low_bandwidth),
        availability_priority=workload.availability_priority,
    )


def _backend_plans(machine: MachineFacts) -> list[dict[str, Any]]:
    tool_presence = {
        "ollama": "ollama" in machine.installed_backends,
        "cmake": False,
        "git": False,
        "uv": False,
        "python": True,
    }
    signals = Signals(
        system=machine.system,
        machine=machine.architecture,
        python_version="caller-normalized",
        tools=tool_presence,
    )
    accelerator = machine.accelerator_vendor if machine.accelerator_vendor in {"nvidia", "amd", "intel", "apple", "cpu"} else "auto"
    plans: list[dict[str, Any]] = []
    for backend in BACKENDS:
        plan = build_plan(backend, signals, accelerator=accelerator)
        plans.append({
            "backend": backend,
            "presence": "PRESENT_NOT_ACCEPTED" if backend in machine.installed_backends else "NOT_REPORTED_PRESENT",
            "setup_review": plan,
            "support_claimed": False,
            "selection_rank_claimed": False,
        })
    return plans


def assess(machine: MachineFacts, workload: WorkloadFacts) -> dict[str, Any]:
    """Return a deterministic, non-executing Local AI readiness plan."""
    machine = _validate_machine(machine)
    workload = _validate_workload(workload)

    if machine.usable_memory_gib is None:
        memory_prefilter: dict[str, Any] = {
            "status": "USABLE_MEMORY_EVIDENCE_REQUIRED",
            "reason": "Total system RAM is not treated as guaranteed accelerator-usable memory.",
            "guarantee": False,
        }
        overall = "DISCOVERY_REQUIRED"
    else:
        fit = estimate(
            params_billions=workload.params_billions,
            bits_per_weight=workload.bits_per_weight,
            available_gib=machine.usable_memory_gib,
        )
        memory_prefilter = asdict(fit)
        memory_prefilter["source_semantics"] = "CALLER_SUPPLIED_USABLE_MEMORY_EVIDENCE"
        if fit.fit_status == "DOES_NOT_FIT_ESTIMATED_WEIGHTS":
            overall = "MODEL_PREFILTER_REJECTED_FOR_SUPPLIED_CAPACITY"
        else:
            overall = "EXACT_BACKEND_WORKLOAD_ACCEPTANCE_REQUIRED"

    architecture = decide(Constraints(
        sensitivity=workload.sensitivity,
        offline_required=workload.offline_required,
        local_hardware_ready=False,
        remote_api_allowed=workload.remote_api_allowed,
        low_bandwidth=workload.low_bandwidth,
        availability_priority=workload.availability_priority,
    ))

    if machine.accelerator_evidence != "VERIFIED_RUNTIME":
        accelerator_gate = "VENDOR_RUNTIME_VERIFICATION_REQUIRED"
    else:
        accelerator_gate = "RUNTIME_SIGNAL_PRESENT_SUPPORT_STILL_REQUIRES_UPSTREAM_AND_WORKLOAD_ACCEPTANCE"

    return {
        "schema_version": "0.2",
        "doctor": {"name": "local_ai_doctor.py", "version": VERSION, "mode": "PLAN_ONLY"},
        "status": overall,
        "machine_facts": asdict(machine),
        "workload_facts": asdict(workload),
        "accelerator_gate": accelerator_gate,
        "memory_prefilter": memory_prefilter,
        "architecture_prefilter": architecture,
        "backend_review_candidates": _backend_plans(machine),
        "claims": {
            "model_runnable": False,
            "backend_supported_on_exact_hardware": False,
            "performance_established": False,
            "quality_established": False,
            "installation_performed": False,
            "model_downloaded": False,
            "cloud_processing_approved": False,
            "production_ready": False,
        },
        "required_acceptance": [
            "Verify accelerator identity/capability with the current vendor runtime or platform API.",
            "Review the current upstream backend support and installation documentation for the exact OS, architecture and accelerator.",
            "Use backend/model-aware fitting when available (for example llama.cpp fit-params or an appropriate model-memory estimator).",
            "Record model artifact identity, provenance, license and exact quantization rather than relying on a model family name alone.",
            "Run a small pinned workload on the exact backend and retain backend selection, versions, exit status and bounded performance evidence.",
            "Verify context length, KV/cache/workspace requirements and intended task quality separately from weight-memory fit.",
            "Review network binding, authentication, telemetry/update checks and data boundaries before exposing any local inference service.",
            "Do not create an automatic cloud fallback for sensitive/regulated data without separate explicit policy authorization.",
        ],
        "safety": {
            "network_requests_performed": False,
            "provider_contacted": False,
            "software_installed": False,
            "drivers_changed": False,
            "services_changed": False,
            "models_loaded": False,
            "models_downloaded": False,
            "benchmarks_run": False,
            "configuration_changed": False,
            "private_machine_identity_required": False,
        },
        "limitations": [
            "A weight-memory prefilter is not runtime-memory or performance proof.",
            "Installed backend presence is not support or health evidence.",
            "Backend/platform support changes over time and remains authoritative upstream.",
            "The doctor deliberately does not infer accelerator-usable memory from total system RAM.",
            "No recommendation here substitutes for exact model/backend acceptance evidence.",
        ],
    }


def from_readiness(
    readiness: dict[str, Any],
    workload: WorkloadFacts,
    *,
    accelerator_vendor: str = "unknown",
    accelerator_evidence: str = "UNKNOWN",
    usable_memory_gib: float | None = None,
) -> dict[str, Any]:
    """Convert the privacy-minimizing v0.1 discovery record into a v0.2 plan.

    Total memory in the discovery record is intentionally *not* promoted to usable
    accelerator memory. That value must arrive through separate evidence.
    """
    collector = readiness.get("collector", {})
    if collector.get("mode") != "READ_ONLY":
        raise LocalAIDoctorError("readiness input must declare READ_ONLY mode")
    privacy = readiness.get("privacy", {})
    if not privacy or any(value is not False for value in privacy.values()):
        raise LocalAIDoctorError("readiness privacy contract is missing or not fail-closed")
    mutation = readiness.get("mutation", {})
    if not mutation or any(value is not False for value in mutation.values()):
        raise LocalAIDoctorError("readiness mutation contract is missing or not fail-closed")

    platform = readiness.get("platform", {})
    runtime = readiness.get("runtime_signals", {})
    installed: list[str] = []
    if runtime.get("ollama"):
        installed.append("ollama")

    machine = MachineFacts(
        system=str(platform.get("system") or "unknown"),
        architecture=str(platform.get("machine") or "unknown"),
        accelerator_vendor=accelerator_vendor,
        accelerator_evidence=accelerator_evidence,
        usable_memory_gib=usable_memory_gib,
        installed_backends=tuple(installed),
    )
    result = assess(machine, workload)
    result["source_readiness"] = {
        "collector": collector.get("name"),
        "collector_version": collector.get("version"),
        "total_system_memory_observed_gib": (
            round(readiness.get("memory", {}).get("total_bytes") / GIB, 3)
            if isinstance(readiness.get("memory", {}).get("total_bytes"), int)
            else None
        ),
        "total_system_memory_used_as_usable_accelerator_memory": False,
    }
    return result


def _load_input(path: Path) -> tuple[MachineFacts, WorkloadFacts]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"machine", "workload"}:
        raise LocalAIDoctorError("input must contain exactly machine and workload objects")
    machine_raw = payload["machine"]
    workload_raw = payload["workload"]
    if not isinstance(machine_raw, dict) or not isinstance(workload_raw, dict):
        raise LocalAIDoctorError("machine and workload must be objects")
    return MachineFacts(
        system=machine_raw.get("system", "unknown"),
        architecture=machine_raw.get("architecture", "unknown"),
        accelerator_vendor=machine_raw.get("accelerator_vendor", "unknown"),
        accelerator_evidence=machine_raw.get("accelerator_evidence", "UNKNOWN"),
        usable_memory_gib=machine_raw.get("usable_memory_gib"),
        installed_backends=tuple(machine_raw.get("installed_backends", [])),
    ), WorkloadFacts(
        params_billions=workload_raw["params_billions"],
        bits_per_weight=workload_raw["bits_per_weight"],
        sensitivity=workload_raw.get("sensitivity", "internal"),
        offline_required=workload_raw.get("offline_required", False),
        remote_api_allowed=workload_raw.get("remote_api_allowed", False),
        low_bandwidth=workload_raw.get("low_bandwidth", False),
        availability_priority=workload_raw.get("availability_priority", "normal"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Evidence-gated, non-executing Local AI Doctor")
    parser.add_argument("input", type=Path, help="Sanitized normalized machine/workload JSON")
    args = parser.parse_args()
    machine, workload = _load_input(args.input)
    print(json.dumps(assess(machine, workload), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
