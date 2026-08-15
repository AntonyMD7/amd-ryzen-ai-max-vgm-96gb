from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import accelerator_readiness as ar


def test_architecture_parser_deduplicates_and_normalizes() -> None:
    assert ar._architectures("Name: gfx1151\nother gfx1151\nName: GFX1100") == (
        "gfx1100",
        "gfx1151",
    )


def test_missing_rocm_is_fail_honest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ar.shutil, "which", lambda name: None)
    result = ar.probe_rocm()
    assert result.present is False
    assert result.responded is False
    assert result.signal == "NOT_INSTALLED"


def test_rocm_response_is_discovery_not_support_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ar.shutil, "which", lambda name: f"/fake/{name}")
    monkeypatch.setattr(ar, "_run", lambda exe, args, timeout=5: (0, "Agent 2\n  Name: gfx1151\n"))
    result = ar.probe_rocm()
    assert result.architectures == ("gfx1151",)
    assert result.signal == "RUNTIME_RESPONDS_ACCELERATOR_ARCH_SEEN"


def test_xrt_probe_uses_examine_not_validate_or_configure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(ar.shutil, "which", lambda name: f"/fake/{name}")

    def fake_run(exe, args, timeout=5):
        calls.append((exe, tuple(args)))
        return 0, "Device(s) Present\n|RyzenAI-npu4|"

    monkeypatch.setattr(ar, "_run", fake_run)
    result = ar.probe_ryzen_ai_npu()
    assert result.responded is True
    assert result.device_names == ("RyzenAI-npu4",)
    assert calls == [("xrt-smi", ("examine", "--report", "platform"))]
    assert all("validate" not in call[1] and "configure" not in call[1] for call in calls)


def test_nvidia_query_does_not_request_unique_identifiers(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[str, ...]]] = []
    monkeypatch.setattr(ar.shutil, "which", lambda name: f"/fake/{name}")

    def fake_run(exe, args, timeout=5):
        calls.append((exe, tuple(args)))
        return 0, "NVIDIA Example GPU\n"

    monkeypatch.setattr(ar, "_run", fake_run)
    result = ar.probe_nvidia()
    assert result.device_names == ("NVIDIA Example GPU",)
    joined = " ".join(calls[0][1]).lower()
    assert "uuid" not in joined
    assert "serial" not in joined
    assert "pci" not in joined


def test_collect_declares_privacy_mutation_and_no_support_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ar,
        "probe_rocm",
        lambda: ar.ProbeResult("rocminfo", True, True, 0, "ok", architectures=("gfx1151",)),
    )
    monkeypatch.setattr(ar, "probe_amd_smi", lambda: ar.ProbeResult("amd-smi", True, True, 0, "ok"))
    monkeypatch.setattr(
        ar,
        "probe_ryzen_ai_npu",
        lambda: ar.ProbeResult("xrt-smi", True, True, 0, "ok", device_names=("RyzenAI-npu4",)),
    )
    monkeypatch.setattr(ar, "probe_nvidia", lambda: ar.ProbeResult("nvidia-smi", False, False, None, "NOT_INSTALLED"))

    data = ar.collect()
    assert data["collector"]["mode"] == "READ_ONLY"
    assert data["interpretation"]["support_claim"] is False
    assert data["interpretation"]["performance_claim"] is False
    assert data["privacy"]["raw_command_output_returned"] is False
    assert data["privacy"]["gpu_uuid_or_serial_collected"] is False
    assert all(value is False for value in data["mutation"].values())
