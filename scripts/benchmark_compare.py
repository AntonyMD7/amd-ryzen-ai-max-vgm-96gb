#!/usr/bin/env python3
"""Compare already-produced local-AI benchmark evidence without running workloads.

The comparator refuses performance ranking when workload/software identity fields
that materially affect interpretation do not match. Energy is reported separately
with its evidence class and is never converted into a wall-power truth claim.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "0.1.0"

COMPARABILITY_FIELDS = (
    ("software", "backend"),
    ("software", "backend_version"),
    ("workload", "model_id"),
    ("workload", "model_revision"),
    ("workload", "artifact_digest"),
    ("workload", "quantization"),
    ("workload", "task"),
    ("workload", "prompt_tokens"),
    ("workload", "generated_tokens"),
    ("workload", "context_size"),
    ("workload", "batch_size"),
    ("workload", "repetitions"),
    ("workload", "warmup_runs"),
)


def get(record: dict[str, Any], path: tuple[str, str]) -> Any:
    current: Any = record
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    mismatches = []
    for path in COMPARABILITY_FIELDS:
        av = get(a, path)
        bv = get(b, path)
        if av != bv:
            mismatches.append({"field": ".".join(path), "a": av, "b": bv})

    comparable = not mismatches
    perf: dict[str, Any] = {
        "comparable": comparable,
        "mismatches": mismatches,
        "winner": None,
        "basis": None,
        "relative_difference_percent": None,
    }
    if comparable:
        ats = get(a, ("performance", "tokens_per_second"))
        bts = get(b, ("performance", "tokens_per_second"))
        if isinstance(ats, (int, float)) and isinstance(bts, (int, float)) and ats > 0 and bts > 0:
            winner = "tie" if ats == bts else ("a" if ats > bts else "b")
            baseline = min(float(ats), float(bts))
            perf.update(
                winner=winner,
                basis="tokens_per_second",
                relative_difference_percent=0.0 if winner == "tie" else round(abs(float(ats) - float(bts)) / baseline * 100.0, 4),
            )
        else:
            alat = get(a, ("performance", "latency_seconds"))
            blat = get(b, ("performance", "latency_seconds"))
            if isinstance(alat, (int, float)) and isinstance(blat, (int, float)) and alat >= 0 and blat >= 0:
                winner = "tie" if alat == blat else ("a" if alat < blat else "b")
                nonzero = [float(x) for x in (alat, blat) if x > 0]
                relative = None if not nonzero or winner == "tie" else round(abs(float(alat) - float(blat)) / min(nonzero) * 100.0, 4)
                perf.update(winner=winner, basis="latency_seconds_lower_is_better", relative_difference_percent=relative)

    energy = {
        "a": get(a, ("energy", "status")),
        "b": get(b, ("energy", "status")),
        "directly_comparable": False,
        "winner": None,
        "reason": "Energy methods/status must match and contain measured values before numeric comparison.",
    }
    a_status = get(a, ("energy", "status"))
    b_status = get(b, ("energy", "status"))
    a_method = get(a, ("energy", "measurement_method"))
    b_method = get(b, ("energy", "measurement_method"))
    a_kwh = get(a, ("energy", "energy_kwh"))
    b_kwh = get(b, ("energy", "energy_kwh"))
    if (
        comparable
        and a_status == b_status
        and a_status in {"DIRECT_METERED", "SOFTWARE_ESTIMATED", "EXTERNAL_REPORTED"}
        and a_method == b_method
        and isinstance(a_kwh, (int, float))
        and isinstance(b_kwh, (int, float))
    ):
        energy["directly_comparable"] = True
        energy["winner"] = "tie" if a_kwh == b_kwh else ("a" if a_kwh < b_kwh else "b")
        energy["reason"] = "Same workload and declared energy status/method; lower recorded kWh is reported without upgrading the evidence class."

    return {
        "schema_version": "0.1",
        "tool": {"name": "benchmark_compare.py", "version": VERSION},
        "records": {"a": a.get("benchmark_id"), "b": b.get("benchmark_id")},
        "performance_comparison": perf,
        "energy_comparison": energy,
        "safety": {
            "benchmark_executed": False,
            "model_loaded": False,
            "system_mutated": False,
            "energy_measurement_performed": False,
        },
        "limitations": [
            "Matching metadata does not prove identical hidden system state or thermal conditions.",
            "This comparator does not establish statistical significance.",
            "Software-estimated energy remains an estimate and is not relabeled as direct metering.",
        ],
    }


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("benchmark record must be a JSON object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare two compatible Local AI benchmark evidence records")
    parser.add_argument("record_a", type=Path)
    parser.add_argument("record_b", type=Path)
    args = parser.parse_args()
    try:
        result = compare(load(args.record_a), load(args.record_b))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
