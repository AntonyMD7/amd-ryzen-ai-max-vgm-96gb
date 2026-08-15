from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from local_ai_readiness import collect
from safefix_contract import ContractError, GateContext, Stage, transition_path, validate_transition


def test_evidence_example_validates() -> None:
    schema = json.loads((ROOT / "schemas/universal-evidence-v0.1.schema.json").read_text())
    example = json.loads((ROOT / "examples/universal-evidence-readonly-example.json").read_text())
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(example)


def test_hardware_compatibility_schema_is_valid_json_schema() -> None:
    schema = json.loads((ROOT / "schemas/hardware-compatibility-report-v0.1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)


def test_mutation_requires_recovery() -> None:
    try:
        validate_transition(
            Stage.APPROVE,
            Stage.MUTATE,
            GateContext(recovery_established=False, approval_required=True, approval_present=True),
        )
    except ContractError as exc:
        assert "recovery" in str(exc)
    else:
        raise AssertionError("mutation without recovery must fail closed")


def test_mutation_requires_approval_when_declared() -> None:
    try:
        validate_transition(
            Stage.APPROVE,
            Stage.MUTATE,
            GateContext(recovery_established=True, approval_required=True, approval_present=False),
        )
    except ContractError as exc:
        assert "approval" in str(exc)
    else:
        raise AssertionError("mutation without required approval must fail closed")


def test_evidence_publication_requires_attestation_and_record() -> None:
    try:
        validate_transition(Stage.ATTEST, Stage.PUBLISH_EVIDENCE, GateContext())
    except ContractError as exc:
        assert "attestation" in str(exc)
    else:
        raise AssertionError("unattested success must not be publishable")


def test_restart_and_no_restart_paths() -> None:
    assert Stage.RESTART in transition_path(restart_required=True)
    assert Stage.RESTART not in transition_path(restart_required=False)


def test_readonly_schema_cannot_smuggle_mutation_without_controls() -> None:
    schema = json.loads((ROOT / "schemas/universal-evidence-v0.1.schema.json").read_text())
    example = json.loads((ROOT / "examples/universal-evidence-readonly-example.json").read_text())
    example["operation"]["classification"] = "MUTATING"
    example["evidence_type"] = "mutation"
    validator = jsonschema.Draft202012Validator(schema)
    errors = list(validator.iter_errors(example))
    assert errors, "mutating evidence without approval/recovery controls must be rejected"


def test_local_ai_collector_declares_read_only_privacy_contract() -> None:
    data = collect()
    assert data["collector"]["mode"] == "READ_ONLY"
    assert data["interpretation"]["status"] == "DISCOVERY_ONLY"
    assert data["privacy"] == {
        "username_collected": False,
        "hostname_collected": False,
        "network_addresses_collected": False,
        "environment_values_collected": False,
        "credentials_collected": False,
    }
    assert all(value is False for value in data["mutation"].values())
