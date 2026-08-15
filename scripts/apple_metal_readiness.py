#!/usr/bin/env python3
"""Privacy-minimizing macOS Metal discovery precheck.

The collector uses macOS `system_profiler SPDisplaysDataType -json` only when
running on Darwin. It extracts bounded non-unique GPU model/Metal-related fields and
drops the rest of the profiler output. It does not run a Metal workload, compile a
shader, query hardware serial numbers, or claim feature-family/application support.

For application-grade capability checks Apple recommends querying an MTLDevice and
using supportsFamily(_:). This CLI layer is only a beginner-safe discovery surface.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
from typing import Any

VERSION = "0.1.0"


def _run_system_profiler(timeout: int = 8) -> tuple[int, str]:
    executable = shutil.which("system_profiler")
    if not executable:
        raise FileNotFoundError("system_profiler")
    completed = subprocess.run(
        [executable, "SPDisplaysDataType", "-json"],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env={"PATH": os.environ.get("PATH", "")},
    )
    return completed.returncode, (completed.stdout or "")[:500_000]


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def extract_safe_signals(payload: Any) -> dict[str, tuple[str, ...]]:
    gpu_models: set[str] = set()
    metal_signals: set[str] = set()
    for key, value in _walk(payload):
        if not isinstance(value, str):
            continue
        key_lower = str(key).lower()
        bounded = value.strip()[:160]
        if not bounded:
            continue
        if key_lower in {"sppci_model", "spdisplays_chipset-model", "chipset model"}:
            gpu_models.add(bounded)
        if "metal" in key_lower:
            metal_signals.add(bounded)
    return {
        "gpu_models": tuple(sorted(gpu_models))[:16],
        "metal_signals": tuple(sorted(metal_signals))[:32],
    }


def collect() -> dict[str, object]:
    system = platform.system()
    base: dict[str, object] = {
        "schema_version": "0.1",
        "collector": {"name": "apple_metal_readiness.py", "version": VERSION, "mode": "READ_ONLY"},
        "platform": system,
        "support_claim": False,
        "feature_family_claim": False,
        "workload_validation_performed": False,
        "privacy": {
            "raw_profiler_output_returned": False,
            "serial_numbers_collected": False,
            "hardware_uuid_collected": False,
            "hostname_collected": False,
            "username_collected": False,
            "network_addresses_collected": False,
            "credentials_collected": False,
        },
        "mutation": {
            "software_installed": False,
            "settings_changed": False,
            "shader_compiled": False,
            "metal_workload_executed": False,
        },
    }
    if system != "Darwin":
        base.update({
            "status": "NOT_APPLICABLE_NON_MACOS",
            "gpu_models": [],
            "metal_signals": [],
        })
        return base
    if not shutil.which("system_profiler"):
        base.update({
            "status": "SYSTEM_PROFILER_NOT_AVAILABLE",
            "gpu_models": [],
            "metal_signals": [],
        })
        return base
    try:
        rc, text = _run_system_profiler()
        parsed = json.loads(text) if rc == 0 else None
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        base.update({
            "status": "DISCOVERY_FAILED",
            "gpu_models": [],
            "metal_signals": [],
        })
        return base

    signals = extract_safe_signals(parsed)
    status = "METAL_DISCOVERY_SIGNAL_PRESENT" if signals["metal_signals"] else "METAL_SUPPORT_NOT_PROVEN"
    base.update({
        "status": status,
        "gpu_models": list(signals["gpu_models"]),
        "metal_signals": list(signals["metal_signals"]),
        "next_gate": [
            "Use Apple's current Metal feature-set tables for the target GPU/OS combination.",
            "For app-grade capability checks, query an MTLDevice and supportsFamily(_:) for each feature family actually required.",
            "Run a pinned Metal workload only in a separately governed acceptance step.",
        ],
    })
    return base


def main() -> int:
    print(json.dumps(collect(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
