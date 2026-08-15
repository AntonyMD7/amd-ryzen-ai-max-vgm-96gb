from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import cuda_readiness as cr


def test_family_floor_snapshot() -> None:
    assert cr.family_precheck("580.65.06", "13.0")["status"] == "FAMILY_FLOOR_PRECHECK_PASSES_MORE_VALIDATION_REQUIRED"
    assert cr.family_precheck("575.57.08", "13.0")["status"] == "BELOW_DOCUMENTED_MINOR_COMPATIBILITY_FAMILY_FLOOR"
    assert cr.family_precheck("525.60.13", "12.9")["status"] == "FAMILY_FLOOR_PRECHECK_PASSES_MORE_VALIDATION_REQUIRED"


def test_unknown_future_cuda_family_fails_honest() -> None:
    result = cr.family_precheck("999.0", "14.0")
    assert result["status"] == "CUDA_FAMILY_OUTSIDE_SNAPSHOT_REQUIRES_CURRENT_VENDOR_DOCS"


def test_missing_versions_do_not_infer_support() -> None:
    assert cr.family_precheck(None, "13.0")["status"] == "DRIVER_VERSION_NOT_PROVEN"
    assert cr.family_precheck("580.1", None)["status"] == "TOOLKIT_VERSION_NOT_PROVEN"


def test_driver_parser_uses_version_text_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cr.shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(
        cr,
        "_run",
        lambda executable, args, timeout=5: (
            0,
            "NVIDIA-SMI 580.65 Driver Version: 580.65.06 CUDA Version: 13.0 GPU UUID: should-not-be-returned",
        ),
    )
    signal = cr.inspect_driver()
    assert signal.driver_version == "580.65.06"
    assert signal.driver_cuda_max == "13.0"
    assert not hasattr(signal, "uuid")


def test_nvcc_release_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cr.shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(
        cr,
        "_run",
        lambda executable, args, timeout=5: (0, "Cuda compilation tools, release 13.0, V13.0.88"),
    )
    signal = cr.inspect_toolkit()
    assert signal.toolkit_version == "13.0"


def test_collect_declares_no_mutation_or_compatibility_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cr,
        "inspect_driver",
        lambda: cr.ToolSignal(True, True, driver_version="580.65.06", driver_cuda_max="13.0"),
    )
    monkeypatch.setattr(
        cr,
        "inspect_toolkit",
        lambda: cr.ToolSignal(True, True, toolkit_version="13.0"),
    )
    data = cr.collect()
    assert data["collector"]["mode"] == "READ_ONLY"
    assert data["interpretation"]["application_compatibility_claim"] is False
    assert data["interpretation"]["workload_validation_performed"] is False
    assert data["source_snapshot"]["must_refresh_against_current_nvidia_docs"] is True
    assert all(value is False for value in data["mutation"].values())
    assert data["privacy"]["gpu_uuid_collected"] is False
