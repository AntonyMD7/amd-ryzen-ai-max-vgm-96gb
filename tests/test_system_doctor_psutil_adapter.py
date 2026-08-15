from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

SCRIPT = SCRIPTS / "system_doctor_psutil_adapter.py"
SCHEMA = ROOT / "schemas" / "system-doctor-observation-case-v0.1.schema.json"

spec = importlib.util.spec_from_file_location("system_doctor_psutil_adapter", SCRIPT)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def synthetic_evidence(*, memory_available: int = 50, memory_total: int = 100, storage_free: int = 50, storage_total: int = 100) -> dict:
    return {
        "schema_version": "0.1",
        "collector": {
            "name": "system_doctor_psutil_adapter.py",
            "version": "0.1.0",
            "mode": "READ_ONLY_BOUNDED",
            "psutil_version": "7.2.2",
        },
        "system": {
            "os_family": "Linux",
            "architecture": "x86_64",
            "cpu_logical_count": 8,
            "memory_total_bytes": memory_total,
            "memory_available_bytes": memory_available,
            "storage_total_bytes": storage_total,
            "storage_free_bytes": storage_free,
        },
        "privacy": {
            "username_collected": False,
            "hostname_collected": False,
            "network_addresses_collected": False,
            "network_interfaces_collected": False,
            "processes_collected": False,
            "process_command_lines_collected": False,
            "environment_values_collected": False,
            "credentials_collected": False,
            "user_files_opened": False,
        },
        "mutation": {
            "files_changed": False,
            "software_installed": False,
            "services_changed": False,
            "configuration_changed": False,
            "network_requested": False,
            "reboot_requested": False,
        },
        "limitations": ["synthetic test evidence"],
    }


def test_pure_mapping_validates_against_fusion_schema() -> None:
    evidence = synthetic_evidence()
    case = adapter.to_observation_case(evidence, collected_at="2026-08-15T09:00:00Z")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.validate(case, schema)

    digest = adapter.evidence_sha256(evidence)
    assert len(digest) == 64
    assert {obs["source"]["evidence_sha256"] for obs in case["observations"]} == {digest}
    result = adapter.fuse_case(case)
    assert result["overall_state"] == "NO_ISSUE_OBSERVED_IN_SUPPLIED_SCOPE"
    assert all(value is False for value in result["claims"].values())
    assert all(value is False for value in result["mutation"].values())


@pytest.mark.parametrize(
    ("available", "total", "expected"),
    [
        (4, 100, "REVIEW"),
        (9, 100, "NOTICE"),
        (10, 100, "OK"),
        (50, 100, "OK"),
        (-1, 100, "UNKNOWN"),
        (0, 0, "UNKNOWN"),
    ],
)
def test_headroom_threshold_mapping_is_explicit(available: int, total: int, expected: str) -> None:
    status, _, _ = adapter._ratio_status(available, total, "MEMORY")
    assert status == expected


def test_review_state_is_plan_only_and_requires_recheck() -> None:
    evidence = synthetic_evidence(memory_available=4, memory_total=100)
    case = adapter.to_observation_case(evidence, collected_at="2026-08-15T09:00:00Z")
    memory = next(obs for obs in case["observations"] if obs["domain"] == "MEMORY")
    assert memory["status"] == "REVIEW"
    assert memory["recommendation_key"] == "REVIEW_CAPACITY_BEFORE_MUTATION"
    assert memory["verification_key"] == "RECHECK_MEMORY_HEADROOM"
    result = adapter.fuse_case(case)
    assert result["overall_state"] == "REVIEW_REQUIRED"
    assert result["claims"]["repair_authorized"] is False


def test_source_contract_has_no_identity_or_mutation_fields_true() -> None:
    evidence = synthetic_evidence()
    assert all(value is False for value in evidence["privacy"].values())
    assert all(value is False for value in evidence["mutation"].values())


def test_optional_dependency_fails_explicitly_when_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adapter, "psutil", None)
    with pytest.raises(RuntimeError, match="psutil is required"):
        adapter.collect_source_evidence()


def test_adapter_source_does_not_enumerate_sensitive_psutil_surfaces_or_execute() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "psutil.users(",
        "psutil.process_iter(",
        "psutil.net_if_addrs(",
        "psutil.net_connections(",
        "psutil.Process(",
        "subprocess",
        "os.system",
        "requests.",
        "urllib.request",
        "socket.",
    )
    assert not any(token in source for token in forbidden)
