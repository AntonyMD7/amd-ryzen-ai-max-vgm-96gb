from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from local_ai_doctor import (
    LocalAIDoctorError,
    MachineFacts,
    WorkloadFacts,
    assess,
    from_readiness,
)
from local_ai_readiness import collect


def _workload(**overrides) -> WorkloadFacts:
    data = {
        "params_billions": 8.0,
        "bits_per_weight": 4.0,
        "sensitivity": "internal",
        "offline_required": False,
        "remote_api_allowed": False,
        "low_bandwidth": False,
        "availability_priority": "normal",
    }
    data.update(overrides)
    return WorkloadFacts(**data)


def _machine(**overrides) -> MachineFacts:
    data = {
        "system": "linux",
        "architecture": "x86_64",
        "accelerator_vendor": "unknown",
        "accelerator_evidence": "UNKNOWN",
        "usable_memory_gib": None,
        "installed_backends": (),
    }
    data.update(overrides)
    return MachineFacts(**data)


def test_missing_usable_memory_stays_discovery_required() -> None:
    result = assess(_machine(), _workload())
    assert result["status"] == "DISCOVERY_REQUIRED"
    assert result["memory_prefilter"]["status"] == "USABLE_MEMORY_EVIDENCE_REQUIRED"
    assert result["claims"]["model_runnable"] is False
    assert result["claims"]["backend_supported_on_exact_hardware"] is False


def test_total_system_memory_from_discovery_is_not_promoted_to_accelerator_memory() -> None:
    readiness = collect()
    result = from_readiness(readiness, _workload())
    assert result["source_readiness"]["total_system_memory_used_as_usable_accelerator_memory"] is False
    assert result["status"] == "DISCOVERY_REQUIRED"


def test_prefilter_fit_still_requires_exact_backend_acceptance() -> None:
    result = assess(
        _machine(
            accelerator_vendor="nvidia",
            accelerator_evidence="VERIFIED_RUNTIME",
            usable_memory_gib=16.0,
        ),
        _workload(params_billions=7.0, bits_per_weight=4.0),
    )
    assert result["memory_prefilter"]["fit_status"] == "PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION"
    assert result["status"] == "EXACT_BACKEND_WORKLOAD_ACCEPTANCE_REQUIRED"
    assert result["claims"]["model_runnable"] is False
    assert result["claims"]["performance_established"] is False


def test_too_small_supplied_capacity_rejects_weight_prefilter_without_broader_claim() -> None:
    result = assess(
        _machine(usable_memory_gib=1.0),
        _workload(params_billions=8.0, bits_per_weight=8.0),
    )
    assert result["memory_prefilter"]["fit_status"] == "DOES_NOT_FIT_ESTIMATED_WEIGHTS"
    assert result["status"] == "MODEL_PREFILTER_REJECTED_FOR_SUPPLIED_CAPACITY"
    assert result["claims"]["quality_established"] is False


def test_sensitive_offline_workload_never_gets_implicit_cloud_fallback() -> None:
    result = assess(
        _machine(),
        _workload(
            sensitivity="regulated",
            offline_required=True,
            remote_api_allowed=False,
            availability_priority="high",
        ),
    )
    architecture = result["architecture_prefilter"]
    assert architecture["recommended_lane"] == "LOCAL_ONLY_REQUIRED"
    assert architecture["safety"]["data_uploaded"] is False
    assert result["claims"]["cloud_processing_approved"] is False
    assert any("Local hardware/backend readiness" in blocker for blocker in architecture["blockers"])


def test_installed_backend_presence_is_not_health_or_support_evidence() -> None:
    result = assess(
        _machine(installed_backends=("ollama",), accelerator_vendor="amd", accelerator_evidence="OBSERVED_ONLY"),
        _workload(),
    )
    by_name = {item["backend"]: item for item in result["backend_review_candidates"]}
    assert by_name["ollama"]["presence"] == "PRESENT_NOT_ACCEPTED"
    assert by_name["ollama"]["support_claimed"] is False
    assert by_name["ollama"]["selection_rank_claimed"] is False
    assert result["accelerator_gate"] == "VENDOR_RUNTIME_VERIFICATION_REQUIRED"


def test_vllm_windows_plan_stays_plan_only_and_does_not_claim_support() -> None:
    result = assess(
        _machine(system="windows", accelerator_vendor="nvidia", accelerator_evidence="OBSERVED_ONLY"),
        _workload(),
    )
    vllm = next(item for item in result["backend_review_candidates"] if item["backend"] == "vllm")
    assert vllm["setup_review"]["status"] == "NATIVE_WINDOWS_NOT_RECOMMENDED_PLAN_ONLY"
    assert vllm["support_claimed"] is False


def test_readiness_with_privacy_or_mutation_violation_fails_closed() -> None:
    readiness = collect()
    readiness["privacy"]["hostname_collected"] = True
    with pytest.raises(LocalAIDoctorError, match="privacy"):
        from_readiness(readiness, _workload())

    readiness = collect()
    readiness["mutation"]["configuration_changed"] = True
    with pytest.raises(LocalAIDoctorError, match="mutation"):
        from_readiness(readiness, _workload())


def test_invalid_normalized_labels_fail_closed() -> None:
    with pytest.raises(LocalAIDoctorError):
        assess(_machine(accelerator_vendor="mystery-gpu"), _workload())
    with pytest.raises(LocalAIDoctorError):
        assess(_machine(installed_backends=("unknown-backend",)), _workload())


def test_orchestrator_has_no_network_or_subprocess_executor() -> None:
    source = (ROOT / "scripts" / "local_ai_doctor.py").read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "import requests" not in source
    assert "urllib" not in source
    assert "os.system(" not in source
    assert "shell=True" not in source
