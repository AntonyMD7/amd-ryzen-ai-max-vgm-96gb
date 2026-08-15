from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "local_cloud_decision.py"
spec = importlib.util.spec_from_file_location("local_cloud_decision", MODULE_PATH)
assert spec and spec.loader
advisor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = advisor
spec.loader.exec_module(advisor)


def constraints(**overrides):
    values = dict(
        sensitivity="internal",
        offline_required=False,
        local_hardware_ready=True,
        remote_api_allowed=True,
        low_bandwidth=False,
        availability_priority="normal",
    )
    values.update(overrides)
    return advisor.Constraints(**values)


def test_offline_requirement_forces_local_lane():
    result = advisor.decide(constraints(offline_required=True, remote_api_allowed=True))
    assert result["recommended_lane"] == "LOCAL_ONLY_REQUIRED"
    assert result["provider_selected"] is False
    assert result["guarantee"] is False


def test_sensitive_without_remote_policy_defaults_local():
    result = advisor.decide(constraints(sensitivity="sensitive", remote_api_allowed=False))
    assert result["recommended_lane"] == "LOCAL_ONLY_REQUIRED"


def test_missing_local_readiness_is_exposed_as_blocker():
    result = advisor.decide(constraints(offline_required=True, local_hardware_ready=False))
    assert any("readiness" in blocker.lower() for blocker in result["blockers"])


def test_high_availability_can_surface_hybrid_candidate_when_remote_allowed():
    result = advisor.decide(constraints(availability_priority="high", remote_api_allowed=True))
    assert result["recommended_lane"] == "HYBRID_CANDIDATE"
    assert any("must not silently send" in item.lower() for item in result["required_next_checks"])


def test_decision_tool_performs_no_network_or_mutation():
    result = advisor.decide(constraints())
    assert all(value is False for value in result["safety"].values())


def test_offline_starter_is_manifest_only_and_has_privacy_acceptance():
    result = advisor.offline_starter_manifest(runtime="ollama", interface="web", document_rag=True)
    assert result["status"] == "PLAN_ONLY_NOT_DEPLOYED"
    assert result["tool"]["mode"] == "MANIFEST_ONLY"
    assert all(value is False for value in result["mutation"].values())
    assert any("external network" in item.lower() for item in result["acceptance"])
    assert any(component["role"] == "document_rag" for component in result["components"])


def test_invalid_runtime_and_interface_fail_closed():
    with pytest.raises(ValueError):
        advisor.offline_starter_manifest(runtime="mystery", interface="cli", document_rag=False)
    with pytest.raises(ValueError):
        advisor.offline_starter_manifest(runtime="ollama", interface="gui", document_rag=False)
