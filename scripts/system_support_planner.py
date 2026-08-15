#!/usr/bin/env python3
"""Plan bounded, read-only system-support checks without executing them.

This module is a public reference layer for early DAIS roadmap work around
Windows/Linux repair guidance, drivers, BIOS/UEFI, networking, peripherals,
hardware compatibility and firmware readiness. It deliberately does *not*
repair, install, update, reboot, change firmware, or execute any command.

The output is a reviewable plan. A plan is not diagnostic proof and never
becomes authorization to mutate a machine.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Any


ROADMAP = {
    "windows_repair": "P-003",
    "linux_repair": "P-004",
    "driver": "P-005",
    "bios_uefi": "P-006",
    "network": "P-007",
    "peripheral": "P-008",
    "compatibility": "P-009",
    "firmware": "P-010",
}

PLATFORMS = {"windows", "linux"}

# These are inspection commands only. They are emitted as text and never run.
READ_ONLY_CHECKS: dict[tuple[str, str], tuple[str, ...]] = {
    ("windows", "windows_repair"): (
        "sfc /verifyonly",
        "DISM /Online /Cleanup-Image /CheckHealth",
        "DISM /Online /Cleanup-Image /ScanHealth",
    ),
    ("linux", "linux_repair"): (
        "systemctl --failed --no-pager",
        "journalctl -p err -b --no-pager --lines=100",
    ),
    ("windows", "driver"): (
        "Get-PnpDevice -PresentOnly | Select-Object Status,Class,FriendlyName,InstanceId",
        "Get-CimInstance Win32_PnPSignedDriver | Select-Object DeviceName,DriverVersion,Manufacturer",
    ),
    ("linux", "driver"): (
        "lspci -nnk",
        "lsusb",
    ),
    ("windows", "network"): (
        "Get-NetAdapter | Select-Object Name,Status,LinkSpeed,InterfaceDescription",
        "Get-NetIPConfiguration | Select-Object InterfaceAlias,IPv4Address,IPv6Address,IPv4DefaultGateway",
    ),
    ("linux", "network"): (
        "nmcli general status",
        "nmcli device status",
    ),
    ("windows", "peripheral"): (
        "Get-PnpDevice -PresentOnly | Select-Object Status,Class,FriendlyName",
    ),
    ("linux", "peripheral"): (
        "lsusb",
        "lsblk -o NAME,SIZE,TYPE,MODEL",
    ),
    ("windows", "compatibility"): (
        "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,TotalPhysicalMemory",
        "Get-CimInstance Win32_Processor | Select-Object Name,Architecture,NumberOfCores,NumberOfLogicalProcessors",
    ),
    ("linux", "compatibility"): (
        "lscpu",
        "lspci -nn",
        "lsblk -o NAME,SIZE,TYPE,MODEL",
    ),
    ("linux", "firmware"): (
        "fwupdmgr get-devices --json",
    ),
}

UPSTREAM_AUTHORITIES: dict[str, tuple[str, ...]] = {
    "windows_repair": (
        "Microsoft System File Checker documentation",
        "Microsoft DISM image servicing documentation",
    ),
    "linux_repair": (
        "distribution documentation",
        "systemd manual pages for systemctl/journalctl",
    ),
    "driver": (
        "operating-system/vendor driver documentation",
        "Linux Hardware hw-probe where Linux community evidence is useful",
    ),
    "bios_uefi": (
        "device/OEM firmware manual",
        "UEFI specification where applicable",
    ),
    "network": (
        "Microsoft networking documentation on Windows",
        "NetworkManager documentation on Linux",
    ),
    "peripheral": (
        "device manufacturer documentation",
        "operating-system hardware inventory interfaces",
    ),
    "compatibility": (
        "hardware/OEM compatibility documentation",
        "community evidence only when clearly labeled as such",
    ),
    "firmware": (
        "device/OEM firmware documentation",
        "fwupd/LVFS on supported Linux devices",
    ),
}

# Anything containing these tokens would cross this module's discovery-only boundary.
FORBIDDEN_COMMAND_TOKENS = (
    " /restorehealth",
    " /scannow",
    "fwupdmgr update",
    "fwupdmgr refresh",
    "nmcli connection modify",
    "nmcli connection add",
    "nmcli connection delete",
    "apt ",
    "apt-get ",
    "dnf ",
    "yum ",
    "pacman ",
    "sudo ",
    "reboot",
    "shutdown",
    "setoption",
)


class PlanningError(ValueError):
    """Raised when an input cannot safely map to a bounded plan."""


@dataclass(frozen=True)
class SupportRequest:
    platform: str
    area: str
    observations: dict[str, bool]


def _validate_commands(commands: tuple[str, ...]) -> None:
    for command in commands:
        normalized = f" {command.lower()} "
        hits = [token.strip() for token in FORBIDDEN_COMMAND_TOKENS if token in normalized]
        if hits:
            raise PlanningError(f"catalog contains mutation-capable command token(s): {hits}")


def _normalize_request(data: dict[str, Any]) -> SupportRequest:
    platform = str(data.get("platform", "")).strip().lower()
    area = str(data.get("area", "")).strip().lower()
    observations = data.get("observations", {})

    if platform not in PLATFORMS:
        raise PlanningError("platform must be 'windows' or 'linux'")
    if area not in ROADMAP:
        raise PlanningError(f"unsupported area: {area or '<missing>'}")
    if area == "windows_repair" and platform != "windows":
        raise PlanningError("windows_repair requires platform=windows")
    if area == "linux_repair" and platform != "linux":
        raise PlanningError("linux_repair requires platform=linux")
    if not isinstance(observations, dict) or not all(
        isinstance(k, str) and isinstance(v, bool) for k, v in observations.items()
    ):
        raise PlanningError("observations must be an object of boolean facts")

    # Avoid echoing free text, identifiers, logs, paths or machine-specific data.
    return SupportRequest(platform=platform, area=area, observations=dict(observations))


def make_plan(data: dict[str, Any]) -> dict[str, Any]:
    request = _normalize_request(data)
    commands = READ_ONLY_CHECKS.get((request.platform, request.area), ())
    _validate_commands(commands)

    if request.area == "bios_uefi":
        disposition = "VENDOR_GUIDANCE_REQUIRED"
    elif request.area == "firmware" and request.platform == "windows":
        disposition = "VENDOR_GUIDANCE_REQUIRED"
    else:
        disposition = "READ_ONLY_PREFLIGHT"

    return {
        "schema_version": "0.1",
        "roadmap_id": ROADMAP[request.area],
        "platform": request.platform,
        "area": request.area,
        "disposition": disposition,
        "read_only_checks": list(commands),
        "observed_fact_names": sorted(request.observations),
        "observed_true_count": sum(request.observations.values()),
        "upstream_authorities": list(UPSTREAM_AUTHORITIES[request.area]),
        "safety": {
            "commands_executed": False,
            "mutation_allowed": False,
            "repair_performed": False,
            "driver_installed": False,
            "firmware_updated": False,
            "bios_changed": False,
            "network_changed": False,
            "reboot_requested": False,
            "raw_logs_returned": False,
            "free_text_echoed": False,
        },
        "evidence_semantics": {
            "plan_is_diagnostic_proof": False,
            "plan_is_compatibility_proof": False,
            "plan_is_authorization_to_mutate": False,
            "successful_command_exit_is_fix_proof": False,
        },
        "next_gate": (
            "Collect the bounded evidence locally, review privacy-sensitive output, "
            "and use current vendor/OS documentation before proposing any mutation."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", help="JSON file containing platform, area and boolean observations")
    args = parser.parse_args()

    with open(args.request, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    print(json.dumps(make_plan(data), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
