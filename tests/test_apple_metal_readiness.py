from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apple_metal_readiness as amr


def test_safe_extractor_ignores_serial_and_keeps_bounded_metal_signals() -> None:
    payload = {
        "SPDisplaysDataType": [
            {
                "sppci_model": "Apple M4",
                "spdisplays_metal": "Supported, feature set macOS GPUFamily2 v1",
                "spdisplays_display-serial-number": "DO-NOT-COLLECT-123",
            }
        ]
    }
    signals = amr.extract_safe_signals(payload)
    assert signals["gpu_models"] == ("Apple M4",)
    assert signals["metal_signals"] == ("Supported, feature set macOS GPUFamily2 v1",)
    assert "DO-NOT-COLLECT-123" not in repr(signals)


def test_non_macos_fails_honest_without_running_profiler(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(amr.platform, "system", lambda: "Linux")
    monkeypatch.setattr(amr, "_run_system_profiler", lambda: (_ for _ in ()).throw(AssertionError("must not run")))
    data = amr.collect()
    assert data["status"] == "NOT_APPLICABLE_NON_MACOS"
    assert data["support_claim"] is False


def test_macos_signal_is_discovery_not_feature_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(amr.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(amr.shutil, "which", lambda name: f"/usr/sbin/{name}")
    monkeypatch.setattr(
        amr,
        "_run_system_profiler",
        lambda timeout=8: (
            0,
            '{"SPDisplaysDataType":[{"sppci_model":"Apple M4","spdisplays_metal":"Supported"}]}',
        ),
    )
    data = amr.collect()
    assert data["status"] == "METAL_DISCOVERY_SIGNAL_PRESENT"
    assert data["gpu_models"] == ["Apple M4"]
    assert data["support_claim"] is False
    assert data["feature_family_claim"] is False
    assert data["workload_validation_performed"] is False
    assert data["privacy"]["serial_numbers_collected"] is False
    assert all(value is False for value in data["mutation"].values())


def test_invalid_profiler_json_fails_honest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(amr.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(amr.shutil, "which", lambda name: f"/usr/sbin/{name}")
    monkeypatch.setattr(amr, "_run_system_profiler", lambda timeout=8: (0, "not-json"))
    data = amr.collect()
    assert data["status"] == "DISCOVERY_FAILED"
