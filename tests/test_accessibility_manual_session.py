from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from accessibility_manual_session import ManualSessionError, to_supporting_record, validate_record
from accessibility_acceptance_validate import validate_record as validate_supporting_record

FIXTURE = ROOT / "examples" / "accessible-ai-manual-session-synthetic-v0.1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def manual_record_all_pass():
    record = load_fixture()
    record["session_mode"] = "MANUAL_ASSISTIVE_TECH"
    record["subject"] = {
        "artifact_kind": "HTML",
        "artifact_ref": "artifacts/accessibility-report-example.html",
        "sha256": "a" * 64,
    }
    record["environment"] = {
        "os_family": "example-os",
        "os_version": "example-reviewed-version",
        "browser_family": "example-browser",
        "browser_version": "example-reviewed-version",
        "assistive_technology_name": "example-screen-reader",
        "assistive_technology_version": "example-reviewed-version",
        "input_method": "KEYBOARD_AND_SCREEN_READER_COMMANDS",
    }
    record["privacy"]["people_involved"] = True
    record["privacy"]["consent_prerequisite_satisfied"] = True
    for task in record["tasks"]:
        task["status"] = "PASS"
        task["notes"] = "Reviewed task passed in this exact example session."
    return record


def test_synthetic_fixture_is_protocol_only_and_maps_without_overclaim():
    record = load_fixture()
    result = validate_record(record)
    assert result["status"] == "SYNTHETIC_ONLY_NOT_ACCEPTANCE"
    assert result["wcag_conformance_certified_by_validator"] is False
    assert result["roadmap_completion_certified_by_validator"] is False

    supporting = to_supporting_record(record)
    summary = validate_supporting_record(supporting)
    assert supporting["evidence_class"] == "SYNTHETIC_CONFORMANCE"
    assert summary["status"] == "SYNTHETIC_ONLY_NOT_ACCEPTANCE"
    assert all(value is False for value in supporting["claims"].values())


def test_manual_session_requires_people_and_external_consent_prerequisite():
    record = manual_record_all_pass()
    record["privacy"]["people_involved"] = False
    with pytest.raises(ManualSessionError, match="people_involved"):
        validate_record(record)

    record = manual_record_all_pass()
    record["privacy"]["consent_prerequisite_satisfied"] = False
    with pytest.raises(ManualSessionError, match="consent"):
        validate_record(record)


@pytest.mark.parametrize("field", ["os_version", "browser_version", "assistive_technology_version"])
def test_manual_session_requires_reproducible_environment_versions(field):
    record = manual_record_all_pass()
    record["environment"][field] = "unknown"
    with pytest.raises(ManualSessionError, match="reproducible"):
        validate_record(record)


def test_manual_session_requires_exact_canonical_tasks_once_each():
    record = manual_record_all_pass()
    record["tasks"].pop()
    with pytest.raises(ManualSessionError, match="task set mismatch"):
        validate_record(record)

    record = manual_record_all_pass()
    record["tasks"][-1] = copy.deepcopy(record["tasks"][0])
    with pytest.raises(ManualSessionError, match="duplicate"):
        validate_record(record)


def test_manual_failure_is_preserved_and_maps_to_screen_reader_failure():
    record = manual_record_all_pass()
    for task in record["tasks"]:
        if task["task_id"] == "status_and_safety_announcement":
            task["status"] = "FAIL"
            task["notes"] = "Safety status was not announced clearly in this example session."

    result = validate_record(record)
    assert result["status"] == "MANUAL_SESSION_HAS_FAILURES"
    assert "status_and_safety_announcement" in result["failed_tasks"]

    supporting = to_supporting_record(record)
    assert supporting["checks"]["screen_reader"]["status"] == "FAIL"
    assert validate_supporting_record(supporting)["status"] == "SUPPORTING_EVIDENCE_HAS_FAILURES"


def test_blocked_task_stays_incomplete_and_maps_to_not_run():
    record = manual_record_all_pass()
    for task in record["tasks"]:
        if task["task_id"] == "zoom_reflow_400":
            task["status"] = "BLOCKED"
            task["notes"] = "Environment could not exercise the required zoom mode."

    result = validate_record(record)
    assert result["status"] == "MANUAL_SESSION_INCOMPLETE"
    assert "zoom_reflow_400" in result["blocked_tasks"]

    supporting = to_supporting_record(record)
    assert supporting["checks"]["zoom_reflow_400"]["status"] == "NOT_RUN"
    assert validate_supporting_record(supporting)["status"] == "SUPPORTING_EVIDENCE_INCOMPLETE"


def test_all_pass_manual_session_remains_supporting_evidence_not_conformance():
    record = manual_record_all_pass()
    result = validate_record(record)
    assert result["status"] == "MANUAL_SUPPORTING_ACCEPTANCE_NOT_CONFORMANCE"
    assert result["cross_at_compatibility_certified_by_validator"] is False
    assert result["production_ready_certified_by_validator"] is False

    supporting = to_supporting_record(record)
    summary = validate_supporting_record(supporting)
    assert supporting["evidence_class"] == "MANUAL_ASSISTIVE_TECH"
    assert summary["status"] == "SUPPORTING_EVIDENCE_INCOMPLETE"
    assert supporting["checks"]["automated_rules"]["status"] == "NOT_RUN"
    assert all(value is False for value in supporting["claims"].values())


@pytest.mark.parametrize(
    "sensitive",
    [
        "password=do-not-publish",
        "api_key: do-not-publish",
        "ghp_abcdefghijklmnopqrstuvwxyz123456",
        "/home/privateuser/report.html",
        r"C:\\Users\\PrivateUser\\report.html",
        "person@example.com",
    ],
)
def test_sensitive_or_contact_patterns_fail_closed(sensitive):
    record = manual_record_all_pass()
    record["tasks"][0]["notes"] = sensitive
    with pytest.raises(ManualSessionError, match="sensitive"):
        validate_record(record)


def test_schema_rejects_roadmap_completion_claim():
    record = manual_record_all_pass()
    record["claims"]["roadmap_complete"] = True
    with pytest.raises(jsonschema.ValidationError):
        validate_record(record)


def test_validator_and_mapper_do_not_mutate_input():
    record = manual_record_all_pass()
    before = copy.deepcopy(record)
    validate_record(record)
    to_supporting_record(record)
    assert record == before
