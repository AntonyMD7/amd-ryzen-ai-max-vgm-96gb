from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "quantization_candidate_selector.py"
spec = importlib.util.spec_from_file_location("quantization_candidate_selector", MODULE_PATH)
assert spec and spec.loader
selector = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = selector
spec.loader.exec_module(selector)


def candidates():
    return selector.parse_candidates([
        {"name": "artifact-a", "artifact_size_bytes": 4_000_000_000, "source": "model-repo@rev-a", "quality_rank": 2},
        {"name": "artifact-b", "artifact_size_bytes": 6_000_000_000, "source": "model-repo@rev-a", "quality_rank": 1},
        {"name": "artifact-c", "artifact_size_bytes": 9_000_000_000, "source": "model-repo@rev-a"},
    ])


def test_recommendation_uses_supplied_rank_only_inside_static_budget():
    result = selector.select_candidates(candidates(), available_memory_bytes=10_000_000_000, reserve_fraction=0.20)
    assert result["recommendation"] == {
        "name": "artifact-b",
        "basis": "USER_SUPPLIED_QUALITY_RANK_PLUS_STATIC_ARTIFACT_FIT",
        "guarantee": False,
    }
    by_name = {item["name"]: item for item in result["evaluated_candidates"]}
    assert by_name["artifact-c"]["artifact_fits_static_budget"] is False
    assert all(item["runtime_fit_proven"] is False for item in by_name.values())
    assert all(item["quality_inferred"] is False for item in by_name.values())


def test_without_quality_rank_prefers_smallest_fit_and_does_not_infer_quality():
    rows = selector.parse_candidates([
        {"name": "large", "artifact_size_bytes": 7_000, "source": "source@1"},
        {"name": "small", "artifact_size_bytes": 4_000, "source": "source@1"},
    ])
    result = selector.select_candidates(rows, available_memory_bytes=10_000, reserve_fraction=0.20)
    assert result["recommendation"]["name"] == "small"
    assert result["recommendation"]["basis"] == "SMALLEST_STATICALLY_FITTING_ARTIFACT_ONLY"
    assert result["recommendation"]["guarantee"] is False


def test_no_fit_returns_no_recommendation():
    rows = selector.parse_candidates([
        {"name": "too-large", "artifact_size_bytes": 9_000, "source": "source@1"},
    ])
    result = selector.select_candidates(rows, available_memory_bytes=10_000, reserve_fraction=0.20)
    assert result["recommendation"] is None


def test_safety_declares_no_model_or_system_mutation():
    result = selector.select_candidates(candidates(), available_memory_bytes=20_000_000_000)
    assert all(value is False for value in result["safety"].values())
    assert "artifact file size is not equivalent" in " ".join(result["limitations"]).lower()


def test_invalid_candidates_fail_closed():
    with pytest.raises(selector.InputError):
        selector.parse_candidates([])
    with pytest.raises(selector.InputError):
        selector.parse_candidates([{"name": "x", "artifact_size_bytes": 1, "source": ""}])
    with pytest.raises(selector.InputError):
        selector.parse_candidates([
            {"name": "x", "artifact_size_bytes": 1, "source": "s"},
            {"name": "x", "artifact_size_bytes": 2, "source": "s"},
        ])


def test_invalid_budget_and_reserve_fail_closed():
    with pytest.raises(selector.InputError):
        selector.select_candidates(candidates(), available_memory_bytes=0)
    with pytest.raises(selector.InputError):
        selector.select_candidates(candidates(), available_memory_bytes=10_000, reserve_fraction=1.0)
