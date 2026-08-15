#!/usr/bin/env python3
"""Read-only CUDA driver/toolkit readiness precheck.

Uses nvidia-smi and nvcc only when already installed. It does not install or update
drivers/toolkits, compile or execute CUDA workloads, query unique GPU identifiers, or
claim application compatibility. The version-family floor table is a dated snapshot
of NVIDIA CUDA 13.3 compatibility documentation and must be refreshed as upstream
requirements change.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass

VERSION = "0.1.0"
SOURCE_SNAPSHOT_DATE = "2026-08-15"
# NVIDIA CUDA minor-version compatibility family floors from current CUDA 13.3 docs.
MIN_DRIVER_MAJOR_BY_CUDA_MAJOR = {11: 450, 12: 525, 13: 580}

_DRIVER_RE = re.compile(r"Driver Version:\s*([0-9]+(?:\.[0-9]+)*)", re.IGNORECASE)
_DRIVER_RE_ALT = re.compile(r"KMD Version:\s*([0-9]+(?:\.[0-9]+)*)", re.IGNORECASE)
_CUDA_UMD_RE = re.compile(r"(?:CUDA Version|CUDA UMD Version):\s*([0-9]+(?:\.[0-9]+)*)", re.IGNORECASE)
_NVCC_RELEASE_RE = re.compile(r"release\s+([0-9]+(?:\.[0-9]+)*)", re.IGNORECASE)


@dataclass(frozen=True)
class ToolSignal:
    present: bool
    responded: bool
    driver_version: str | None = None
    driver_cuda_max: str | None = None
    toolkit_version: str | None = None


def _run(executable: str, args: list[str], timeout: int = 5) -> tuple[int, str]:
    path = shutil.which(executable)
    if not path:
        raise FileNotFoundError(executable)
    completed = subprocess.run(
        [path, *args],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        env={"PATH": os.environ.get("PATH", "")},
    )
    return completed.returncode, ((completed.stdout or "") + "\n" + (completed.stderr or ""))[:100_000]


def _match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def inspect_driver() -> ToolSignal:
    if not shutil.which("nvidia-smi"):
        return ToolSignal(False, False)
    try:
        rc, text = _run("nvidia-smi", [])
    except (OSError, subprocess.SubprocessError):
        return ToolSignal(True, False)
    driver = _match(_DRIVER_RE, text) or _match(_DRIVER_RE_ALT, text)
    cuda_max = _match(_CUDA_UMD_RE, text)
    return ToolSignal(True, rc == 0, driver_version=driver, driver_cuda_max=cuda_max)


def inspect_toolkit() -> ToolSignal:
    if not shutil.which("nvcc"):
        return ToolSignal(False, False)
    try:
        rc, text = _run("nvcc", ["--version"])
    except (OSError, subprocess.SubprocessError):
        return ToolSignal(True, False)
    toolkit = _match(_NVCC_RELEASE_RE, text)
    return ToolSignal(True, rc == 0, toolkit_version=toolkit)


def _major(version: str | None) -> int | None:
    if not version:
        return None
    try:
        return int(version.split(".", 1)[0])
    except ValueError:
        return None


def family_precheck(driver_version: str | None, toolkit_version: str | None) -> dict[str, object]:
    toolkit_major = _major(toolkit_version)
    driver_major = _major(driver_version)
    if toolkit_major is None:
        return {"status": "TOOLKIT_VERSION_NOT_PROVEN", "minimum_driver_major": None}
    floor = MIN_DRIVER_MAJOR_BY_CUDA_MAJOR.get(toolkit_major)
    if floor is None:
        return {
            "status": "CUDA_FAMILY_OUTSIDE_SNAPSHOT_REQUIRES_CURRENT_VENDOR_DOCS",
            "minimum_driver_major": None,
        }
    if driver_major is None:
        return {"status": "DRIVER_VERSION_NOT_PROVEN", "minimum_driver_major": floor}
    if driver_major < floor:
        status = "BELOW_DOCUMENTED_MINOR_COMPATIBILITY_FAMILY_FLOOR"
    else:
        status = "FAMILY_FLOOR_PRECHECK_PASSES_MORE_VALIDATION_REQUIRED"
    return {"status": status, "minimum_driver_major": floor}


def collect() -> dict[str, object]:
    driver = inspect_driver()
    toolkit = inspect_toolkit()
    return {
        "schema_version": "0.1",
        "collector": {"name": "cuda_readiness.py", "version": VERSION, "mode": "READ_ONLY"},
        "source_snapshot": {
            "date": SOURCE_SNAPSHOT_DATE,
            "scope": "CUDA 11.x/12.x/13.x minor-version compatibility family floors",
            "must_refresh_against_current_nvidia_docs": True,
        },
        "driver": asdict(driver),
        "toolkit": asdict(toolkit),
        "family_precheck": family_precheck(driver.driver_version, toolkit.toolkit_version),
        "interpretation": {
            "application_compatibility_claim": False,
            "gpu_architecture_support_claim": False,
            "workload_validation_performed": False,
            "note": "nvidia-smi reports the CUDA user-mode capability supported by the installed driver, which may differ from the installed toolkit version.",
        },
        "privacy": {
            "raw_command_output_returned": False,
            "gpu_uuid_collected": False,
            "gpu_serial_collected": False,
            "pci_bus_identity_collected": False,
            "hostname_collected": False,
            "credentials_collected": False,
        },
        "mutation": {
            "driver_changed": False,
            "toolkit_changed": False,
            "packages_installed": False,
            "code_compiled": False,
            "cuda_workload_executed": False,
        },
        "next_gate": [
            "Refresh the exact CUDA Toolkit release-note minimum driver requirement for the target toolkit.",
            "Verify that the target GPU architecture remains supported by that CUDA/toolkit/driver combination.",
            "Compile or run a pinned CUDA sample/workload only in a separately governed acceptance step.",
        ],
    }


def main() -> int:
    print(json.dumps(collect(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
