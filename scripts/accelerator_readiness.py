#!/usr/bin/env python3
"""Privacy-minimizing GPU/NPU and ROCm readiness discovery.

This module runs a fixed allowlist of vendor read-only inspection commands. It never
installs drivers/runtimes, runs accelerator validation workloads, changes power modes,
changes firmware, downloads models, or accepts arbitrary command input.

Presence/readiness signals are intentionally weaker than support claims. Official
vendor compatibility matrices and a pinned workload remain required before saying a
hardware/runtime combination is supported for a particular framework or model.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Sequence

VERSION = "0.1.0"

_GFX_RE = re.compile(r"\bgfx[0-9a-f]+\b", re.IGNORECASE)
_NPU_RE = re.compile(r"\b(?:RyzenAI[- _]?npu\w*|NPU Compute Accelerator Device)\b", re.IGNORECASE)


@dataclass(frozen=True)
class ProbeResult:
    tool: str
    present: bool
    responded: bool
    return_code: int | None
    signal: str
    architectures: tuple[str, ...] = ()
    device_names: tuple[str, ...] = ()


def _run(executable: str, args: Sequence[str], *, timeout: int = 5) -> tuple[int, str]:
    path = shutil.which(executable)
    if not path:
        raise FileNotFoundError(executable)
    completed = subprocess.run(
        [path, *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env={"PATH": os.environ.get("PATH", "")},
    )
    # Output is retained only in-process for bounded parsing. It is never returned raw.
    return completed.returncode, (completed.stdout or "")[:200_000]


def _architectures(text: str) -> tuple[str, ...]:
    return tuple(sorted({m.group(0).lower() for m in _GFX_RE.finditer(text)}))


def probe_rocm() -> ProbeResult:
    """Use AMD's documented rocminfo installation-verification command."""
    if not shutil.which("rocminfo"):
        return ProbeResult("rocminfo", False, False, None, "NOT_INSTALLED")
    try:
        rc, out = _run("rocminfo", [])
    except (OSError, subprocess.SubprocessError):
        return ProbeResult("rocminfo", True, False, None, "PRESENT_BUT_PROBE_FAILED")
    arches = _architectures(out)
    if rc == 0 and arches:
        signal = "RUNTIME_RESPONDS_ACCELERATOR_ARCH_SEEN"
    elif rc == 0:
        signal = "RUNTIME_RESPONDS_NO_GFX_ARCH_PARSED"
    else:
        signal = "PRESENT_BUT_RUNTIME_DID_NOT_VERIFY"
    return ProbeResult("rocminfo", True, rc == 0, rc, signal, architectures=arches)


def probe_amd_smi() -> ProbeResult:
    """Check AMD SMI CLI presence/version without monitoring or control operations."""
    if not shutil.which("amd-smi"):
        return ProbeResult("amd-smi", False, False, None, "NOT_INSTALLED")
    try:
        rc, _ = _run("amd-smi", ["version"])
    except (OSError, subprocess.SubprocessError):
        return ProbeResult("amd-smi", True, False, None, "PRESENT_BUT_PROBE_FAILED")
    return ProbeResult(
        "amd-smi",
        True,
        rc == 0,
        rc,
        "CLI_RESPONDS" if rc == 0 else "PRESENT_BUT_CLI_DID_NOT_VERIFY",
    )


def probe_ryzen_ai_npu() -> ProbeResult:
    """Run xrt-smi examine only; never validate/configure the NPU."""
    if not shutil.which("xrt-smi"):
        return ProbeResult("xrt-smi", False, False, None, "NOT_INSTALLED")
    try:
        rc, out = _run("xrt-smi", ["examine", "--report", "platform"])
    except (OSError, subprocess.SubprocessError):
        return ProbeResult("xrt-smi", True, False, None, "PRESENT_BUT_PROBE_FAILED")
    names = tuple(sorted({m.group(0) for m in _NPU_RE.finditer(out)}))
    if rc == 0 and names:
        signal = "NPU_EXAMINE_RESPONDS_DEVICE_SIGNAL_SEEN"
    elif rc == 0:
        signal = "NPU_EXAMINE_RESPONDS_DEVICE_NOT_PARSED"
    else:
        signal = "PRESENT_BUT_NPU_EXAMINE_DID_NOT_VERIFY"
    return ProbeResult("xrt-smi", True, rc == 0, rc, signal, device_names=names)


def probe_nvidia() -> ProbeResult:
    """Query non-unique GPU name only; omit UUID/serial/bus identity."""
    if not shutil.which("nvidia-smi"):
        return ProbeResult("nvidia-smi", False, False, None, "NOT_INSTALLED")
    try:
        rc, out = _run(
            "nvidia-smi",
            ["--query-gpu=name", "--format=csv,noheader"],
        )
    except (OSError, subprocess.SubprocessError):
        return ProbeResult("nvidia-smi", True, False, None, "PRESENT_BUT_PROBE_FAILED")
    names = tuple(
        line.strip()[:160]
        for line in out.splitlines()
        if line.strip() and "uuid" not in line.lower()
    )[:16]
    return ProbeResult(
        "nvidia-smi",
        True,
        rc == 0,
        rc,
        "GPU_QUERY_RESPONDS" if rc == 0 and names else "PRESENT_BUT_GPU_QUERY_DID_NOT_VERIFY",
        device_names=names if rc == 0 else (),
    )


def collect() -> dict[str, object]:
    probes = [probe_rocm(), probe_amd_smi(), probe_ryzen_ai_npu(), probe_nvidia()]
    rocm = probes[0]
    npu = probes[2]
    return {
        "schema_version": "0.1",
        "collector": {
            "name": "accelerator_readiness.py",
            "version": VERSION,
            "mode": "READ_ONLY",
        },
        "probes": [asdict(p) for p in probes],
        "interpretation": {
            "rocm_readiness": (
                "DISCOVERY_SIGNAL_PRESENT_REQUIRES_OFFICIAL_COMPATIBILITY_CHECK"
                if rocm.responded and rocm.architectures
                else "NOT_PROVEN"
            ),
            "npu_readiness": (
                "DISCOVERY_SIGNAL_PRESENT_REQUIRES_WORKLOAD_VALIDATION"
                if npu.responded and npu.device_names
                else "NOT_PROVEN"
            ),
            "support_claim": False,
            "performance_claim": False,
        },
        "privacy": {
            "raw_command_output_returned": False,
            "username_collected": False,
            "hostname_collected": False,
            "network_addresses_collected": False,
            "gpu_uuid_or_serial_collected": False,
            "credentials_collected": False,
        },
        "mutation": {
            "packages_installed": False,
            "drivers_changed": False,
            "firmware_changed": False,
            "power_mode_changed": False,
            "validation_workload_executed": False,
            "models_downloaded": False,
        },
        "next_gate": [
            "Check the exact GPU/APU architecture, OS, kernel/driver and ROCm version against AMD's current official compatibility matrix.",
            "For Ryzen AI NPU, use AMD's supported-configuration guidance for the installed Ryzen AI release.",
            "Run a separately governed pinned workload or vendor validation only after discovery and support checks pass.",
        ],
    }


def main() -> int:
    print(json.dumps(collect(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
