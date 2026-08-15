#!/usr/bin/env python3
"""Offline model-weight memory estimator and conservative fit prefilter.

This tool performs arithmetic only. It does not download models, inspect private
files, allocate accelerator memory, benchmark inference, or claim that a model
will run. Use backend-native estimators/fit tools and a real benchmark before
making operational claims.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

GIB = 1024 ** 3


@dataclass(frozen=True)
class Estimate:
    params_billions: float
    bits_per_weight: float
    structural_overhead_percent: float
    runtime_headroom_percent: float
    available_gib: float | None
    raw_weight_bytes: int
    estimated_weight_bytes: int
    estimated_weight_gib: float
    conservative_required_bytes: int
    conservative_required_gib: float
    fit_status: str
    scope: str = "WEIGHTS_PLUS_GENERIC_HEADROOM_ONLY"
    guarantee: bool = False


def estimate(
    *,
    params_billions: float,
    bits_per_weight: float,
    structural_overhead_percent: float = 5.0,
    runtime_headroom_percent: float = 20.0,
    available_gib: float | None = None,
) -> Estimate:
    if params_billions <= 0:
        raise ValueError("params_billions must be > 0")
    if bits_per_weight <= 0 or bits_per_weight > 64:
        raise ValueError("bits_per_weight must be > 0 and <= 64")
    if structural_overhead_percent < 0 or runtime_headroom_percent < 0:
        raise ValueError("overhead percentages must be >= 0")
    if available_gib is not None and available_gib <= 0:
        raise ValueError("available_gib must be > 0 when supplied")

    raw = int(params_billions * 1_000_000_000 * bits_per_weight / 8)
    estimated = int(raw * (1 + structural_overhead_percent / 100))
    conservative = int(estimated * (1 + runtime_headroom_percent / 100))

    if available_gib is None:
        status = "CAPACITY_NOT_SUPPLIED"
    else:
        available = int(available_gib * GIB)
        if available < estimated:
            status = "DOES_NOT_FIT_ESTIMATED_WEIGHTS"
        elif available < conservative:
            status = "BORDERLINE_REQUIRES_BACKEND_VALIDATION"
        else:
            status = "PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION"

    return Estimate(
        params_billions=params_billions,
        bits_per_weight=bits_per_weight,
        structural_overhead_percent=structural_overhead_percent,
        runtime_headroom_percent=runtime_headroom_percent,
        available_gib=available_gib,
        raw_weight_bytes=raw,
        estimated_weight_bytes=estimated,
        estimated_weight_gib=round(estimated / GIB, 3),
        conservative_required_bytes=conservative,
        conservative_required_gib=round(conservative / GIB, 3),
        fit_status=status,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline model-weight memory estimator; not an inference guarantee"
    )
    parser.add_argument("--params-billions", type=float, required=True)
    parser.add_argument("--bits", type=float, required=True, dest="bits_per_weight")
    parser.add_argument("--available-gib", type=float)
    parser.add_argument("--structural-overhead-percent", type=float, default=5.0)
    parser.add_argument("--runtime-headroom-percent", type=float, default=20.0)
    args = parser.parse_args()

    result = estimate(
        params_billions=args.params_billions,
        bits_per_weight=args.bits_per_weight,
        structural_overhead_percent=args.structural_overhead_percent,
        runtime_headroom_percent=args.runtime_headroom_percent,
        available_gib=args.available_gib,
    )
    payload = asdict(result)
    payload["limitations"] = [
        "Does not model KV cache, activations, graph/workspace memory, multimodal towers, adapters, or backend-specific allocations.",
        "Quantization formats can store metadata/scales and may differ materially from nominal bits per weight.",
        "Unified-memory availability is not equivalent to guaranteed accelerator-usable memory.",
        "Validate with the target backend and a pinned real model before making a run/performance claim.",
    ]
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
