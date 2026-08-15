from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from accessibility_acceptance_validate import AcceptanceEvidenceError, validate_record

FIXTURE = ROOT / "examples" / "accessible-ai-acceptance-synthetic-v0.1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_synthetic_fixture_is_explicitly_not_acceptance_or_conformance():
    result = validate_record(load_fixture())
    assert result["status"] == "SYNTHETIC_ONLY_NOT_ACCEPTANCE"
    assert result["schema_validation"] == "PASS"
    assert result["wcag_conformance_certified_by_validator"] is False
    assert result["accessibility_completeness_certified_by_validator"] is False
    assert result["real_user_acceptance_certified_by_validator"] is False
    assert result["production_ready_certified_by_validator"] is False


def test_schema_rejects_wcag_conformance_claim():
    record = load_fixture()
    record["claims"]["wcag_conformance"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_record(record)


def test_schema_rejects_participant_identity_storage():
    record = load_fixture()
    record["privacy"]["participant_identity_stored"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_record(record)


def test_people_evidence_requires_consent():
    record = load_fixture()
    record["evidence_class"] = "MANUAL_ASSISTIVE_TECH"
    record["environment"]["assistive_technology"] = "screen reader"
    with pytest.raises(AcceptanceEvidenceError, match="requires recorded consent"):
        validate_record(record)


def test_automated_evidence_never_becomes_conformance():
    record = load_fixture()
    record["evidence_class"] = "AUTOMATED_TOOL"
    record["environment"]["tool_name"] = "example automated checker"
    record["environment"]["tool_version"] = "1.0"
    record["checks"]["automated_rules"]["status"] = "PASS"
    result = validate_record(record)
    assert result["status"] == "AUTOMATED_SUPPORTING_EVIDENCE_NOT_CONFORMANCE"
    assert result["wcag_conformance_certified_by_validator"] is False


def test_failed_check_is_preserved_not_smoothed_over():
    record = load_fixture()
    record["evidence_class"] = "MANUAL_ASSISTIVE_TECH"
    record["privacy"]["consent_recorded_when_people_involved"] = True
    record["checks"]["keyboard_only"]["status"] = "FAIL"
    result = validate_record(record)
    assert result["status"] == "SUPPORTING_EVIDENCE_HAS_FAILURES"
    assert "keyboard_only" in result["failed_checks"]


@pytest.mark.parametrize(
    "sensitive",
    [
        "password=do-not-publish",
        "api_key: do-not-publish",
        "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "/home/privateuser/report.html",
        r"C:\\Users\\PrivateUser\\report.html",
    ],
)
def test_sensitive_public_evidence_patterns_fail_closed(sensitive):
    record = load_fixture()
    record["checks"]["keyboard_only"]["notes"] = sensitive
    with pytest.raises(AcceptanceEvidenceError, match="sensitive"):
        validate_record(record)


def test_validator_does_not_mutate_input():
    record = load_fixture()
    before = copy.deepcopy(record)
    validate_record(record)
    assert record == before
