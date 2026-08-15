from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load_module("system_doctor_psutil_adapter", SCRIPTS / "system_doctor_psutil_adapter.py")
binder = load_module("system_doctor_universal_evidence", SCRIPTS / "system_doctor_universal_evidence.py")
evidence_validate = load_module("evidence_validate", SCRIPTS / "evidence_validate.py")

UE_SCHEMA = json.loads((ROOT / "schemas" / "universal-evidence-v0.1.schema.json").read_text(encoding="utf-8"))
F02_SCHEMA = json.loads((ROOT / "schemas" / "system-doctor-observation-case-v0.1.schema.json").read_text(encoding="utf-8"))


def synthetic_source() -> dict:
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
            "memory_total_bytes": 100,
            "memory_available_bytes": 50,
            "storage_total_bytes": 100,
            "storage_free_bytes": 50,
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


def acceptance_record() -> dict:
    source = synthetic_source()
    case = adapter.to_observation_case(
        source,
        collected_at="2026-08-15T09:00:00Z",
        case_id="synthetic-f02-f05-binding",
        environment_class="SYNTHETIC",
    )
    jsonschema.validate(case, F02_SCHEMA)
    fused = adapter.fuse_case(case)
    return {
        "record_version": "0.1",
        "source_evidence": source,
        "source_evidence_sha256": adapter.evidence_sha256(source),
        "observation_case": case,
        "fused_result": fused,
        "acceptance_claims": {
            "real_psutil_runtime_exercised": True,
            "identity_data_collected": False,
            "network_data_collected": False,
            "process_data_collected": False,
            "mutation_performed": False,
            "physical_hardware_health_proven": False,
            "root_cause_proven": False,
            "production_safe_to_infer": False,
            "roadmap_complete": False,
        },
    }


def test_binding_validates_universal_evidence_and_exact_artifacts(tmp_path: Path) -> None:
    envelope = binder.build_binding(
        acceptance_record(),
        output_dir=tmp_path,
        source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
        evidence_id="f02-f05-synthetic-binding-001",
    )
    jsonschema.validate(envelope, UE_SCHEMA)
    result = evidence_validate.validate_record(envelope, UE_SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "PASS"
    assert len(result["artifact_results"]) == 3
    assert all(item["match"] for item in result["artifact_results"])
    assert envelope["operation"]["classification"] == "VERIFY"
    assert envelope["rollback"]["required"] is False
    assert envelope["safety"] == {
        "secrets_redacted": True,
        "private_infrastructure_redacted": True,
        "human_approval_required": False,
        "approval_present": False,
    }
    assert envelope["post_state"]["production_safe_to_infer"] is False
    assert envelope["post_state"]["roadmap_complete"] is False


def test_source_digest_mismatch_is_refused(tmp_path: Path) -> None:
    record = acceptance_record()
    record["source_evidence_sha256"] = "0" * 64
    with pytest.raises(binder.BindingError, match="does not match"):
        binder.build_binding(
            record,
            output_dir=tmp_path,
            source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
            evidence_id="f02-f05-synthetic-binding-002",
        )


def test_observation_digest_chain_mismatch_is_refused(tmp_path: Path) -> None:
    record = acceptance_record()
    record["observation_case"]["observations"][0]["source"]["evidence_sha256"] = "0" * 64
    with pytest.raises(binder.BindingError, match="every F-02 observation"):
        binder.build_binding(
            record,
            output_dir=tmp_path,
            source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
            evidence_id="f02-f05-synthetic-binding-003",
        )


def test_overclaim_or_mutation_flag_is_refused(tmp_path: Path) -> None:
    record = acceptance_record()
    record["acceptance_claims"]["production_safe_to_infer"] = True
    with pytest.raises(binder.BindingError, match="must be false"):
        binder.build_binding(
            record,
            output_dir=tmp_path,
            source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
            evidence_id="f02-f05-synthetic-binding-004",
        )


def test_fused_case_identity_mismatch_is_refused(tmp_path: Path) -> None:
    record = acceptance_record()
    record["fused_result"]["case_id"] = "different-case"
    with pytest.raises(binder.BindingError, match="case_id"):
        binder.build_binding(
            record,
            output_dir=tmp_path,
            source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
            evidence_id="f02-f05-synthetic-binding-005",
        )


def test_universal_evidence_hash_validation_detects_artifact_tamper(tmp_path: Path) -> None:
    envelope = binder.build_binding(
        acceptance_record(),
        output_dir=tmp_path,
        source_commit="4c3774519d32a4c3c787184748bb4b9a76a4180f",
        evidence_id="f02-f05-synthetic-binding-006",
    )
    path = tmp_path / "f02-fused-result.json"
    path.write_bytes(path.read_bytes() + b"\n")
    result = evidence_validate.validate_record(envelope, UE_SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert any(item["name"] == "f02-fused-result.json" for item in result["artifact_failures"])


def test_binding_is_deterministic_for_explicit_inputs(tmp_path: Path) -> None:
    first_dir = tmp_path / "one"
    second_dir = tmp_path / "two"
    kwargs = {
        "source_commit": "4c3774519d32a4c3c787184748bb4b9a76a4180f",
        "evidence_id": "f02-f05-synthetic-binding-007",
    }
    first = binder.build_binding(copy.deepcopy(acceptance_record()), output_dir=first_dir, **kwargs)
    second = binder.build_binding(copy.deepcopy(acceptance_record()), output_dir=second_dir, **kwargs)
    assert first == second
    assert (first_dir / "universal-evidence.json").read_bytes() == (second_dir / "universal-evidence.json").read_bytes()
