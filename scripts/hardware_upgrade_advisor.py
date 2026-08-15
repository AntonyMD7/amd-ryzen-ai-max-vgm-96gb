#!/usr/bin/env python3
"""Interpret explicit hardware/benchmark facts without probing or mutating a device."""

from __future__ import annotations

import argparse
import json
from typing import Any


class AdvisorError(ValueError):
    pass


ROADMAP = {
    "ram": "P-011",
    "gpu": "P-012",
    "storage": "P-013",
    "thermal_power": "P-014",
    "benchmark": "P-015",
}


def _number(data: dict[str, Any], key: str, *, minimum: float = 0) -> float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < minimum:
        raise AdvisorError(f"{key} must be a number >= {minimum}")
    return float(value)


def _base(kind: str) -> dict[str, Any]:
    if kind not in ROADMAP:
        raise AdvisorError("kind must be ram, gpu, storage, thermal_power, or benchmark")
    return {
        "schema_version": "0.1",
        "roadmap_id": ROADMAP[kind],
        "kind": kind,
        "safety": {
            "hardware_probed": False,
            "benchmark_executed": False,
            "settings_changed": False,
            "firmware_changed": False,
            "purchase_recommended": False,
        },
        "semantics": {
            "result_is_vendor_compatibility_proof": False,
            "result_is_stability_proof": False,
            "result_is_performance_guarantee": False,
        },
    }


def advise_ram(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("ram")
    installed = _number(data, "installed_gb")
    target = _number(data, "target_gb")
    vendor_max = _number(data, "vendor_max_gb")
    free_slots = int(_number(data, "free_slots"))
    if target <= installed:
        state = "NO_CAPACITY_UPGRADE_NEEDED"
    elif target > vendor_max:
        state = "OUTSIDE_DECLARED_VENDOR_MAX"
    elif free_slots <= 0 and data.get("replacement_required") is not True:
        state = "REVIEW_SLOT_TOPOLOGY"
    else:
        state = "CAPACITY_PREFILTER_PASSES_REVIEW_OTHER_CONSTRAINTS"
    out.update({"state": state, "installed_gb": installed, "target_gb": target, "vendor_max_gb": vendor_max})
    out["next_checks"] = ["OEM memory specification/QVL", "memory type/generation", "module topology", "firmware support", "post-install memory test"]
    return out


def advise_gpu(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("gpu")
    required_psu = _number(data, "candidate_required_psu_w")
    psu = _number(data, "system_psu_w")
    connector_ok = data.get("power_connectors_verified")
    fit_ok = data.get("physical_fit_verified")
    if not isinstance(connector_ok, bool) or not isinstance(fit_ok, bool):
        raise AdvisorError("power_connectors_verified and physical_fit_verified must be booleans")
    reasons = []
    if psu < required_psu:
        reasons.append("DECLARED_PSU_BELOW_CANDIDATE_REQUIREMENT")
    if not connector_ok:
        reasons.append("POWER_CONNECTORS_UNVERIFIED")
    if not fit_ok:
        reasons.append("PHYSICAL_FIT_UNVERIFIED")
    out.update({"state": "REVIEW_REQUIRED" if reasons else "BASIC_PREFILTER_PASSES", "review_reasons": reasons})
    out["next_checks"] = ["GPU/OEM compatibility documentation", "PCIe/interface support", "case clearance", "power connectors", "cooling", "driver/OS support"]
    return out


def advise_storage(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("storage")
    interface_match = data.get("interface_match")
    form_factor_match = data.get("form_factor_match")
    slot_available = data.get("slot_available")
    if not all(isinstance(v, bool) for v in (interface_match, form_factor_match, slot_available)):
        raise AdvisorError("storage compatibility facts must be booleans")
    reasons = []
    if not interface_match:
        reasons.append("INTERFACE_MISMATCH_OR_UNVERIFIED")
    if not form_factor_match:
        reasons.append("FORM_FACTOR_MISMATCH_OR_UNVERIFIED")
    if not slot_available:
        reasons.append("NO_VERIFIED_AVAILABLE_SLOT")
    out.update({"state": "REVIEW_REQUIRED" if reasons else "BASIC_PREFILTER_PASSES", "review_reasons": reasons})
    out["next_checks"] = ["OEM storage specification", "lane/interface constraints", "boot/firmware support", "backup before migration", "drive-health evidence"]
    return out


def advise_thermal_power(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("thermal_power")
    observed_temp = _number(data, "observed_temp_c")
    vendor_limit = _number(data, "vendor_temp_limit_c")
    observed_power = _number(data, "observed_power_w")
    declared_power_limit = _number(data, "declared_power_limit_w")
    temp_ratio = observed_temp / vendor_limit if vendor_limit else 0
    power_ratio = observed_power / declared_power_limit if declared_power_limit else 0
    flags = []
    if observed_temp > vendor_limit:
        flags.append("OBSERVED_TEMP_ABOVE_CALLER_SUPPLIED_VENDOR_LIMIT")
    if observed_power > declared_power_limit:
        flags.append("OBSERVED_POWER_ABOVE_CALLER_SUPPLIED_DECLARED_LIMIT")
    out.update({"state": "REVIEW_REQUIRED" if flags else "WITHIN_SUPPLIED_LIMITS", "review_reasons": flags, "temp_limit_ratio": round(temp_ratio, 4), "power_limit_ratio": round(power_ratio, 4)})
    out["next_checks"] = ["current vendor thermal/power specification", "sensor provenance", "ambient/load conditions", "repeatable workload", "cooling inspection"]
    return out


def interpret_benchmark(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("benchmark")
    candidate = _number(data, "candidate_value")
    baseline = _number(data, "baseline_value")
    higher_is_better = data.get("higher_is_better")
    same_workload = data.get("same_workload")
    same_software = data.get("same_software")
    same_settings = data.get("same_settings")
    if not all(isinstance(v, bool) for v in (higher_is_better, same_workload, same_software, same_settings)):
        raise AdvisorError("benchmark comparability flags must be booleans")
    comparable = same_workload and same_software and same_settings
    out["comparable"] = comparable
    if not comparable:
        out.update({"state": "REFUSE_RANKING_MATERIAL_FIELDS_DIFFER", "relative_change_percent": None})
        return out
    if baseline == 0:
        raise AdvisorError("baseline_value must be > 0 for relative comparison")
    raw_pct = ((candidate - baseline) / baseline) * 100
    improvement_pct = raw_pct if higher_is_better else -raw_pct
    out.update({"state": "COMPARABLE_ARITHMETIC_ONLY", "relative_change_percent": round(raw_pct, 4), "directional_improvement_percent": round(improvement_pct, 4)})
    out["next_checks"] = ["repeat count/variance", "hardware/software identity", "thermal state", "power mode", "benchmark methodology"]
    return out


def advise(data: dict[str, Any]) -> dict[str, Any]:
    kind = str(data.get("kind", "")).strip().lower()
    return {
        "ram": advise_ram,
        "gpu": advise_gpu,
        "storage": advise_storage,
        "thermal_power": advise_thermal_power,
        "benchmark": interpret_benchmark,
    }.get(kind, lambda _: (_ for _ in ()).throw(AdvisorError("unsupported kind")))(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(advise(request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
