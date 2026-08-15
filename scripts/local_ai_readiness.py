#!/usr/bin/env python3
"""Local AI Doctor v0.1 read-only readiness collector.

The collector intentionally reports capability signals without installing software,
downloading models, changing drivers, probing private network state, or claiming a
specific model will run. Recommendations must be layered on verified runtime and
accelerator evidence rather than guessed from a machine name.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Any

VERSION = "0.1.0"


def total_memory_bytes() -> int | None:
    if os.name == "nt":
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

    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
        return int(pages * page_size)
    except (AttributeError, OSError, ValueError):
        return None


def safe_version(executable: str, args: list[str]) -> str | None:
    path = shutil.which(executable)
    if not path:
        return None
    try:
        completed = subprocess.run(
            [path, *args],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
            env={"PATH": os.environ.get("PATH", "")},
        )
    except (OSError, subprocess.SubprocessError):
        return "present-version-unavailable"
    output = (completed.stdout or completed.stderr).strip().splitlines()
    return output[0][:240] if output else "present-version-unavailable"


def collect() -> dict[str, Any]:
    tools = {
        "ollama": safe_version("ollama", ["--version"]),
        "nvidia_smi": safe_version("nvidia-smi", ["--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"]),
        "rocminfo": "present" if shutil.which("rocminfo") else None,
        "python": platform.python_version(),
    }
    return {
        "schema_version": "0.1",
        "collector": {"name": "local_ai_readiness.py", "version": VERSION, "mode": "READ_ONLY"},
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor() or None,
        },
        "memory": {"total_bytes": total_memory_bytes()},
        "runtime_signals": tools,
        "privacy": {
            "username_collected": False,
            "hostname_collected": False,
            "network_addresses_collected": False,
            "environment_values_collected": False,
            "credentials_collected": False,
        },
        "mutation": {
            "software_installed": False,
            "models_downloaded": False,
            "drivers_changed": False,
            "configuration_changed": False,
        },
        "interpretation": {
            "status": "DISCOVERY_ONLY",
            "next_checks": [
                "Confirm accelerator identity and usable memory with the vendor runtime.",
                "Confirm the intended inference backend supports the detected OS/architecture.",
                "Benchmark a pinned model/backend combination before making performance claims.",
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only Local AI readiness collector")
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    data = collect()
    text = json.dumps(data, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
