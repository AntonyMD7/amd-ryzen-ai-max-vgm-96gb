#!/usr/bin/env python3
"""Evidence-first quantization candidate selector.

The selector does not quantize models and does not invent model quality or runtime
compatibility. It ranks user-supplied candidate artifacts using their observed
artifact sizes and an explicit memory/headroom budget. Exact backend acceptance
remains mandatory.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "0.1.0"


class InputError(ValueError):
    pass


def parse_candidates(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, list) or not data:
        raise InputError("candidates must be a non-empty JSON array")
    result: list[dict[str, Any]] = []
    names: set[str] = set()
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise InputError(f"candidate {index} must be an object")
        name = str(item.get("name", "")).strip()
        source = str(item.get("source", "")).strip()
        size = item.get("artifact_size_bytes")
        if not name or name in names:
            raise InputError("candidate names must be non-empty and unique")
        if not source:
            raise InputError(f"candidate {name!r} requires a source/provenance label")
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise InputError(f"candidate {name!r} requires positive integer artifact_size_bytes")
        names.add(name)
        result.append({
            "name": name,
            "artifact_size_bytes": size,
            "source": source,
            "quality_rank": item.get("quality_rank"),
        })
    return result


def select_candidates(
    candidates: list[dict[str, Any]],
    *,
    available_memory_bytes: int,
    reserve_fraction: float = 0.20,
) -> dict[str, Any]:
    if isinstance(available_memory_bytes, bool) or available_memory_bytes <= 0:
        raise InputError("available_memory_bytes must be positive")
    if not (0.0 <= reserve_fraction < 1.0):
        raise InputError("reserve_fraction must be in [0, 1)")

    budget = int(available_memory_bytes * (1.0 - reserve_fraction))
    evaluated = []
    for item in candidates:
        size = item["artifact_size_bytes"]
        evaluated.append({
            **item,
            "artifact_fits_static_budget": size <= budget,
            "static_budget_margin_bytes": budget - size,
            "runtime_fit_proven": False,
            "quality_inferred": False,
        })

    fitting = [x for x in evaluated if x["artifact_fits_static_budget"]]
    # Prefer an explicit user/source supplied quality rank only among statically
    # fitting artifacts. No rank means unknown quality and is never invented.
    ranked_quality = [x for x in fitting if isinstance(x.get("quality_rank"), int) and not isinstance(x.get("quality_rank"), bool)]
    if ranked_quality:
        recommended = sorted(ranked_quality, key=lambda x: (x["quality_rank"], -x["artifact_size_bytes"]))[0]
        basis = "USER_SUPPLIED_QUALITY_RANK_PLUS_STATIC_ARTIFACT_FIT"
    elif fitting:
        recommended = sorted(fitting, key=lambda x: x["artifact_size_bytes"])[0]
        basis = "SMALLEST_STATICALLY_FITTING_ARTIFACT_ONLY"
    else:
        recommended = None
        basis = "NO_STATICALLY_FITTING_ARTIFACT"

    return {
        "schema_version": "0.1",
        "tool": {"name": "quantization_candidate_selector.py", "version": VERSION},
        "status": "PREFILTER_ONLY",
        "inputs": {
            "available_memory_bytes": available_memory_bytes,
            "reserve_fraction": reserve_fraction,
            "static_artifact_budget_bytes": budget,
        },
        "evaluated_candidates": evaluated,
        "recommendation": None if recommended is None else {
            "name": recommended["name"],
            "basis": basis,
            "guarantee": False,
        },
        "safety": {
            "model_loaded": False,
            "model_downloaded": False,
            "model_quantized": False,
            "backend_started": False,
            "configuration_changed": False,
        },
        "required_next_checks": [
            "Verify the candidate artifact provenance and license at its source.",
            "Verify the exact inference backend supports the candidate format/quantization.",
            "Measure actual runtime memory use; artifact size alone is not runtime memory.",
            "Run a pinned quality/task evaluation before comparing answer quality.",
            "Run a pinned performance workload before making speed claims.",
        ],
        "limitations": [
            "Artifact file size is not equivalent to runtime RAM/VRAM use.",
            "KV cache, context length, backend buffers, graph/workspace memory and offload strategy can materially change runtime memory.",
            "Quantization labels are treated as opaque names; this tool does not infer quality from a label.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Select model artifact candidates using observed size and explicit headroom")
    parser.add_argument("candidates", type=Path, help="JSON array of candidate artifact records")
    parser.add_argument("--available-memory-gib", type=float, required=True)
    parser.add_argument("--reserve-fraction", type=float, default=0.20)
    args = parser.parse_args()
    if args.available_memory_gib <= 0:
        raise SystemExit("--available-memory-gib must be positive")
    try:
        candidates = parse_candidates(json.loads(args.candidates.read_text(encoding="utf-8")))
        result = select_candidates(
            candidates,
            available_memory_bytes=int(args.available_memory_gib * 1024**3),
            reserve_fraction=args.reserve_fraction,
        )
    except (OSError, json.JSONDecodeError, InputError) as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
