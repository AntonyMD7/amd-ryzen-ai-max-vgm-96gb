from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "release_readiness_verify.py"
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("release_readiness_verify", SCRIPT)
assert spec and spec.loader
release = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = release
spec.loader.exec_module(release)

FIXTURE = ROOT / "examples" / "public-build-completion-p025-in-progress.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def evaluate(record=None, **overrides):
    sha = "a" * 40
    kwargs = {
        "tag": "v0.1.0-rc.1",
        "source_commit": sha,
        "observed_commit": sha,
        "repo_root": ROOT,
    }
    kwargs.update(overrides)
    return release.evaluate_release_readiness(record or load_fixture(), **kwargs)


def test_p025_is_ready_only_for_governed_release_creation_review():
    result = evaluate()
    assert result["decision"] == "READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW"
    assert result["completion_contract"]["blocking_gates"] == [
        "version_tag_or_release_published",
        "canonical_handover_or_build_record_updated",
    ]
    assert result["completion_contract"]["completion_contract_satisfied"] is False
    assert result["truth_boundary"]["readiness_is_completion"] is False
    assert result["execution"]["release_created"] is False
    assert all(value is False for value in result["execution"].values())


def test_third_unresolved_gate_blocks_release_readiness():
    record = copy.deepcopy(load_fixture())
    record["gates"]["tests_and_ci"] = {
        "state": "UNKNOWN",
        "evidence": [],
        "rationale": "test",
        "applicability_reviewed": True,
    }
    result = evaluate(record)
    assert result["decision"] == "BLOCKED"
    assert "only_release_and_final_handover_remain_blocking" in result["failed_checks"]
    assert "all_non_release_completion_gates_satisfied" in result["failed_checks"]


def test_commit_mismatch_fails_closed():
    result = evaluate(source_commit="a" * 40, observed_commit="b" * 40)
    assert result["decision"] == "BLOCKED"
    assert "exact_source_commit_checked_out" in result["failed_checks"]


def test_complete_subject_is_not_a_pre_release_candidate():
    record = copy.deepcopy(load_fixture())
    record["status"] = "COMPLETE"
    record["completion_record"]["final_status"] = "COMPLETE"
    result = evaluate(record)
    assert result["decision"] == "BLOCKED"
    assert "subject_remains_in_progress_before_release" in result["failed_checks"]


def test_invalid_tag_and_non_exact_commit_are_rejected():
    with pytest.raises(release.ReleaseReadinessError):
        evaluate(tag="latest")
    with pytest.raises(release.ReleaseReadinessError):
        evaluate(source_commit="deadbeef")


def test_required_public_file_missing_blocks(tmp_path):
    for name in release.REQUIRED_PUBLIC_FILES:
        if name == "LICENSE":
            continue
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("ok\n", encoding="utf-8")
    result = evaluate(repo_root=tmp_path)
    assert result["decision"] == "BLOCKED"
    assert "required_public_files_present" in result["failed_checks"]


def test_verifier_source_contains_no_release_mutation_executor():
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "gh release create",
        "gh release edit",
        "git tag ",
        "git push --tags",
        "/releases",
        "requests.post",
        "urllib.request",
    )
    for token in forbidden:
        assert token not in source
