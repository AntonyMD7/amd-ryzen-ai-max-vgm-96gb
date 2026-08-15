from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "release_governance.py"
spec = importlib.util.spec_from_file_location("release_governance", MODULE_PATH)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = release
spec.loader.exec_module(release)


def candidate(**overrides):
    data = {
        "tag": "v0.1.0",
        "source_commit": "a" * 40,
        "project_files": {name: True for name in release.REQUIRED_PROJECT_FILES},
        "ci_passed": True,
        "tests_passed": True,
        "evidence_validated": True,
        "known_limitations_documented": True,
        "security_privacy_reviewed": True,
        "accessibility_reviewed": True,
        "rollback_or_recovery_documented": True,
        "release_notes_present": True,
        "artifacts": [],
        "artifact_attestation_requested": False,
    }
    data.update(overrides)
    return data


def test_ready_candidate_remains_plan_only():
    result = release.validate_candidate(candidate())
    assert result["decision"] == "READY_FOR_GOVERNED_RELEASE_WORKFLOW"
    assert result["failed_gates"] == []
    assert result["proposed_workflow_permissions"] == {"contents": "write"}
    assert all(value is False for value in result["execution"].values())


def test_missing_evidence_or_accessibility_blocks_release():
    result = release.validate_candidate(candidate(evidence_validated=False, accessibility_reviewed=False))
    assert result["decision"] == "BLOCKED"
    assert "evidence_validated" in result["failed_gates"]
    assert "accessibility_reviewed" in result["failed_gates"]


def test_attestation_adds_only_expected_permissions():
    result = release.validate_candidate(candidate(artifact_attestation_requested=True))
    assert result["proposed_workflow_permissions"] == {
        "contents": "write",
        "id-token": "write",
        "attestations": "write",
    }


def test_bad_semver_and_non_exact_sha_fail_closed():
    with pytest.raises(release.CandidateError):
        release.validate_candidate(candidate(tag="latest"))
    with pytest.raises(release.CandidateError):
        release.validate_candidate(candidate(source_commit="deadbeef"))


def test_invalid_artifact_digest_blocks_release():
    result = release.validate_candidate(candidate(artifacts=[{"name": "bundle.zip", "sha256": "bad"}]))
    assert result["decision"] == "BLOCKED"
    assert "artifact_digests_declared" in result["failed_gates"]


def test_missing_public_project_file_blocks_release():
    files = {name: True for name in release.REQUIRED_PROJECT_FILES}
    files["LICENSE"] = False
    result = release.validate_candidate(candidate(project_files=files))
    assert "project_file:LICENSE" in result["failed_gates"]
