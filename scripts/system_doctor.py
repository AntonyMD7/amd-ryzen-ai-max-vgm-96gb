#!/usr/bin/env python3
"""Universal System Doctor v0.1 — read-only baseline collector and explainer.

The default contract is non-mutating and privacy-minimizing. It gathers a small set
of cross-platform machine-health signals, classifies observations, and renders the
same facts for beginner, intermediate, or engineer audiences. It deliberately does
not inspect user documents, browser data, network addresses, environment values,
credentials, or process command lines.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Any

VERSION = "0.1.0"


def total_memory_bytes() -> int | None:
    try:
        if os.name == "nt":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MEMORYSTATUSEX()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys)
            return None
        return int(os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None


def disk_summary(path: Path) -> dict[str, int | None]:
    try:
        usage = shutil.disk_usage(path)
        return {"total_bytes": usage.total, "used_bytes": usage.used, "free_bytes": usage.free}
    except OSError:
        return {"total_bytes": None, "used_bytes": None, "free_bytes": None}


def bounded_version(executable: str, args: list[str]) -> str | None:
    binary = shutil.which(executable)
    if not binary:
        return None
    try:
        run = subprocess.run(
            [binary, *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.SubprocessError):
        return "present-version-unavailable"
    lines = (run.stdout or run.stderr).strip().splitlines()
    return lines[0][:240] if lines else "present-version-unavailable"


def classify_disk(disk: dict[str, int | None]) -> dict[str, Any]:
    total = disk["total_bytes"]
    free = disk["free_bytes"]
    if not total or free is None:
        return {"status": "UNKNOWN", "summary": "Storage capacity could not be measured."}
    free_ratio = free / total
    if free_ratio < 0.05:
        return {"status": "REVIEW", "summary": "Less than 5% of the checked filesystem is free."}
    if free_ratio < 0.10:
        return {"status": "NOTICE", "summary": "Less than 10% of the checked filesystem is free."}
    return {"status": "OK", "summary": "The checked filesystem has at least 10% free space."}


def collect(root: Path | None = None) -> dict[str, Any]:
    checked_root = root or Path(Path.cwd().anchor or "/")
    storage = disk_summary(checked_root)
    return {
        "schema_version": "0.1",
        "collector": {"name": "system_doctor.py", "version": VERSION, "mode": "READ_ONLY"},
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
            "python": platform.python_version(),
            "memory_total_bytes": total_memory_bytes(),
        },
        "storage": storage,
        "checks": {
            "storage_headroom": classify_disk(storage),
            "git_available": {"status": "OK" if shutil.which("git") else "NOTICE", "version": bounded_version("git", ["--version"])},
            "python_available": {"status": "OK", "version": platform.python_version()},
        },
        "privacy": {
            "username_collected": False,
            "hostname_collected": False,
            "network_addresses_collected": False,
            "environment_values_collected": False,
            "credentials_collected": False,
            "user_files_opened": False,
            "process_command_lines_collected": False,
        },
        "mutation": {
            "files_changed": False,
            "software_installed": False,
            "services_changed": False,
            "configuration_changed": False,
            "reboot_requested": False,
        },
        "limitations": [
            "This baseline is intentionally shallow and is not a hardware failure diagnosis.",
            "A REVIEW or NOTICE result is an observation, not permission to perform a repair.",
            "Vendor-specific diagnostics should run as separate bounded adapters with their own evidence.",
        ],
    }


def render(report: dict[str, Any], audience: str) -> str:
    storage = report["checks"]["storage_headroom"]
    if audience == "beginner":
        if storage["status"] == "OK":
            return "Basic read-only checks completed. Storage headroom looks acceptable. No changes were made."
        return f"Basic read-only checks completed. Storage needs attention: {storage['summary']} No changes were made."
    if audience == "intermediate":
        rows = [f"Storage: {storage['status']} — {storage['summary']}"]
        rows.append(f"Git: {report['checks']['git_available']['status']}")
        rows.append("Mode: READ_ONLY; no repair has been authorized or attempted.")
        return "\n".join(rows)
    return json.dumps(report, indent=2, sort_keys=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Privacy-safe read-only system health baseline")
    parser.add_argument("--audience", choices=["beginner", "intermediate", "engineer"], default="beginner")
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    report = collect()
    if args.json_output:
        args.json_output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(render(report, args.audience))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
