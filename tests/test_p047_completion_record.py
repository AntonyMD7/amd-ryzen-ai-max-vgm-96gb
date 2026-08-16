import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_build_completion_contract import audit_record  # noqa: E402

RECORD_PATH = ROOT / "examples/public-build-completion-p047-v0.4.0.json"
RELEASE = "https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/releases/tag/v0.4.0"
HANDOVER = "docs/P047-COMPLETION-RECORD-v0.4.0.md"
RELEASE_SOURCE = "e8ec4a6f5dfbaadfaca46c98ad3679dce8e1ddd7"
RELEASE_RUN = "31930292226"
CONSUMER_RUN = "31930402427"
CONSUMER_ARTIFACT = "9259091393"


def load_record():
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_p047_completion_record_satisfies_canonical_contract():
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


def test_p047_completion_identity_is_exact_and_scope_bound():
    record = load_record()
    completion = record["completion_record"]
    assert record["subject_id"] == "P-047"
    assert completion["roadmap_id"] == "P-047"
    assert completion["version"] == "0.4.0"
    assert completion["release_or_tag"] == "v0.4.0"
    assert completion["public_url"] == RELEASE
    assert completion["handover"] == HANDOVER
    assert completion["final_status"] == "COMPLETE"
    assert "README Markdown style/structure" in completion["known_limitations"]
    assert "no documentation correctness" in completion["known_limitations"]


def test_p047_release_consumer_and_retained_evidence_are_explicit():
    record = load_record()
    release_gate = record["gates"]["version_tag_or_release_published"]
    acceptance_gate = record["gates"]["real_world_acceptance_test"]
    retained_gate = record["gates"]["evidence_retained"]
    tests_gate = record["gates"]["tests_and_ci"]

    assert RELEASE in release_gate["evidence"]
    assert RELEASE_SOURCE in release_gate["rationale"]
    assert any(RELEASE_RUN in item for item in release_gate["evidence"])
    assert any(CONSUMER_RUN in item for item in acceptance_gate["evidence"])
    assert any("AntonyMD7/learning-git" in item for item in acceptance_gate["evidence"])
    assert any("AntonyMD7/Kimi-Haul" in item for item in acceptance_gate["evidence"])
    assert any(CONSUMER_ARTIFACT in item for item in retained_gate["evidence"])
    assert any(CONSUMER_RUN in item for item in tests_gate["evidence"])


def test_all_p047_gate_applicability_is_explicitly_reviewed():
    record = load_record()
    assert len(record["gates"]) == 19
    assert all(gate["state"] == "PASS" for gate in record["gates"].values())
    assert all(gate.get("applicability_reviewed") is True for gate in record["gates"].values())


def test_p047_completion_does_not_overclaim_adjacent_tools():
    text = json.dumps(load_record(), sort_keys=True)
    limitations = load_record()["completion_record"]["known_limitations"]
    assert "link health" in limitations
    assert "accessibility conformance" in limitations
    assert "security/DLP" in limitations
    assert "auto-fix/custom plugins" in limitations
    assert "documentation correctness" in text
