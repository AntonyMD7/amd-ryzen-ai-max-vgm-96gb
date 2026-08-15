from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from model_memory_estimator import GIB, estimate


def test_nominal_7b_q4_weight_arithmetic() -> None:
    result = estimate(
        params_billions=7,
        bits_per_weight=4,
        structural_overhead_percent=0,
        runtime_headroom_percent=0,
    )
    assert result.raw_weight_bytes == 3_500_000_000
    assert result.estimated_weight_bytes == 3_500_000_000
    assert result.fit_status == "CAPACITY_NOT_SUPPLIED"
    assert result.guarantee is False


def test_capacity_below_estimated_weights_fails_prefilter() -> None:
    result = estimate(
        params_billions=70,
        bits_per_weight=4,
        structural_overhead_percent=5,
        runtime_headroom_percent=20,
        available_gib=16,
    )
    assert result.fit_status == "DOES_NOT_FIT_ESTIMATED_WEIGHTS"


def test_headroom_boundary_is_not_a_run_claim() -> None:
    result = estimate(
        params_billions=7,
        bits_per_weight=4,
        structural_overhead_percent=5,
        runtime_headroom_percent=20,
        available_gib=4,
    )
    assert result.fit_status == "BORDERLINE_REQUIRES_BACKEND_VALIDATION"
    assert result.guarantee is False


def test_generous_capacity_still_requires_backend_validation() -> None:
    result = estimate(
        params_billions=7,
        bits_per_weight=4,
        structural_overhead_percent=5,
        runtime_headroom_percent=20,
        available_gib=16,
    )
    assert result.fit_status == "PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION"
    assert result.guarantee is False


def test_invalid_inputs_fail_closed() -> None:
    with pytest.raises(ValueError):
        estimate(params_billions=0, bits_per_weight=4)
    with pytest.raises(ValueError):
        estimate(params_billions=7, bits_per_weight=0)
    with pytest.raises(ValueError):
        estimate(params_billions=7, bits_per_weight=4, available_gib=0)


def test_cli_is_offline_arithmetic_and_emits_limitations() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "model_memory_estimator.py"),
            "--params-billions",
            "7",
            "--bits",
            "4",
            "--available-gib",
            "16",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    assert proc.returncode == 0
    assert '"guarantee": false' in proc.stdout
    assert '"limitations"' in proc.stdout
    assert "PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION" in proc.stdout
    assert proc.stderr == ""
