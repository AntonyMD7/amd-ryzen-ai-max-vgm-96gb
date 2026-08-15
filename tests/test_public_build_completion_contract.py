import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from public_build_completion_contract import (  # noqa: E402
    COMPLETION_RECORD_FIELDS,
    GATES,
    audit_record,
)


def load_fixture():
    return json.loads((ROOT / "examples/public-build-completion-p025-in-progress.json").read_text(encoding="utf-8"))


def make_ready_record(status="IN_PROGRESS"):
    gates = {
        gate: {
            "state": "PASS",
            "evidence": [f"evidence/{gate}.json"],
            "rationale": "verified fixture evidence",
            "applicability_reviewed": True,
        }
        for gate in GATES
    }
    completion = {field: f"value-{field}" for field in COMPLETION_RECORD_FIELDS}
    completion["roadmap_id"] = "P-001"
    completion["final_status"] = status
    return {
        "schema_version": "0.1",
        "subject_id": "P-001",
        "status": status,
        "gates": gates,
        "completion_record": completion,
    }


def test_in_progress_fixture_is_truthfully_incomplete():
    report = audit_record(load_fixture())
    assert report["errors"] == []
    assert report["declared_status"] == "IN_PROGRESS"
    assert report["readiness"] == "INCOMPLETE"
    assert report["completion_contract_satisfied"] is False
    assert report["source_coverage_alone_is_completion"] is False
    assert report["ci_alone_is_completion"] is False
    assert report["automated_accessibility_check_alone_is_conformance"] is False
    assert set(report["blocking_gates"]) == {
        "accessibility_review",
        "multilingual_path_considered",
        "real_world_acceptance_test",
        "version_tag_or_release_published",
        "canonical_handover_or_build_record_updated",
    }


def test_complete_status_fails_closed_when_gates_are_missing():
    record = load_fixture()
    record["status"] = "COMPLETE"
    record["completion_record"]["final_status"] = "COMPLETE"
    report = audit_record(record)
    assert any("status COMPLETE is forbidden" in error for error in report["errors"])
    assert report["completion_contract_satisfied"] is False


def test_pass_requires_evidence():
    record = make_ready_record()
    record["gates"]["tests_and_ci"]["evidence"] = []
    report = audit_record(record)
    assert any("tests_and_ci cannot PASS without evidence" in error for error in report["errors"])


def test_not_applicable_requires_review_and_rationale():
    record = make_ready_record()
    record["gates"]["recovery_or_rollback_guidance_for_mutating_tools"] = {
        "state": "NOT_APPLICABLE",
        "evidence": [],
        "rationale": "",
        "applicability_reviewed": False,
    }
    report = audit_record(record)
    assert any("NOT_APPLICABLE requires applicability_reviewed=true" in error for error in report["errors"])
    assert any("NOT_APPLICABLE requires a rationale" in error for error in report["errors"])


def test_all_gates_pass_does_not_auto_mark_complete():
    record = make_ready_record("IN_PROGRESS")
    report = audit_record(record)
    assert report["errors"] == []
    assert report["readiness"] == "READY_FOR_CANONICAL_COMPLETION_REVIEW"
    assert report["ready_for_canonical_completion_review"] is True
    assert report["completion_contract_satisfied"] is False


def test_explicit_complete_record_can_satisfy_contract():
    record = make_ready_record("COMPLETE")
    report = audit_record(record)
    assert report["errors"] == []
    assert report["readiness"] == "COMPLETE_CONTRACT_SATISFIED"
    assert report["completion_contract_satisfied"] is True


def test_subject_id_is_bounded_to_canonical_portfolio():
    record = make_ready_record()
    record["subject_id"] = "P-228"
    record["completion_record"]["roadmap_id"] = "P-228"
    report = audit_record(record)
    assert any("subject_id must be canonical" in error for error in report["errors"])


def test_public_record_rejects_secret_patterns():
    record = make_ready_record()
    record["completion_record"]["evidence_location"] = "token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
    report = audit_record(record)
    assert report["safe_public_evidence_prefilter"] is False
    assert any("token/secret/private-key" in error for error in report["errors"])


def test_audit_does_not_mutate_input():
    record = load_fixture()
    before = copy.deepcopy(record)
    audit_record(record)
    assert record == before
