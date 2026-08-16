import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_build_completion_contract import audit_record  # noqa: E402

RECORD_PATH = ROOT / "examples/public-build-completion-p050-v0.3.0.json"
RELEASE = "https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/releases/tag/v0.3.0"
HANDOVER = "docs/P050-COMPLETION-RECORD-v0.3.0.md"
RELEASE_SOURCE = "f00ad749a07a9067075c87f5ca20feab04695288"
RELEASE_RUN = "31929278253"


def load_record():
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_p050_completion_record_satisfies_canonical_contract():
    record = load_record()
    report = audit_record(record)
    assert report["errors"] == []
    assert report["declared_status"] == "COMPLETE"
    assert report["readiness"] == "COMPLETE_CONTRACT_SATISFIED"
    assert report["completion_contract_satisfied"] is True
    assert report["blocking_gates"] == []
    assert report["gate_counts"]["PASS"] == 19
    assert report["project_completion_record_populated"] is True
    assert report["safe_public_evidence_prefilter"] is True


def test_p050_completion_identity_is_exact_and_scope_bound():
    record = load_record()
    completion = record["completion_record"]
    assert record["subject_id"] == "P-050"
    assert completion["roadmap_id"] == "P-050"
    assert completion["version"] == "0.3.0"
    assert completion["release_or_tag"] == "v0.3.0"
    assert completion["public_url"] == RELEASE
    assert completion["handover"] == HANDOVER
    assert completion["final_status"] == "COMPLETE"
    assert "Linux x64 / CPython 3.12" in completion["known_limitations"]
    assert "semantic-truth" in completion["known_limitations"]


def test_p050_real_acceptance_and_retained_evidence_remain_explicit():
    record = load_record()
    release_gate = record["gates"]["version_tag_or_release_published"]
    acceptance_gate = record["gates"]["real_world_acceptance_test"]
    retained_gate = record["gates"]["evidence_retained"]
    tests_gate = record["gates"]["tests_and_ci"]

    assert RELEASE in release_gate["evidence"]
    assert RELEASE_SOURCE in release_gate["rationale"]
    assert any(RELEASE_RUN in item for item in acceptance_gate["evidence"])
    assert any("AntonyMD7/learning-git" in item for item in acceptance_gate["evidence"])
    assert any("AntonyMD7/Kimi-Haul" in item for item in acceptance_gate["evidence"])
    assert any("9258798897" in item for item in retained_gate["evidence"])
    assert any("9258800798" in item for item in retained_gate["evidence"])
    assert any("9258802973" in item for item in retained_gate["evidence"])
    assert any("9258802825" in item for item in retained_gate["evidence"])
    assert any("31929156755" in item for item in tests_gate["evidence"])


def test_all_gate_applicability_is_explicitly_reviewed():
    record = load_record()
    assert len(record["gates"]) == 19
    assert all(gate["state"] == "PASS" for gate in record["gates"].values())
    assert all(gate.get("applicability_reviewed") is True for gate in record["gates"].values())
