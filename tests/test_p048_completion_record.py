import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_build_completion_contract import audit_record  # noqa: E402

RECORD_PATH = ROOT / "examples/public-build-completion-p048-v0.5.0.json"
RELEASE = "https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/releases/tag/v0.5.0"
HANDOVER = "docs/P048-COMPLETION-RECORD-v0.5.0.md"
RELEASE_SOURCE = "1cc9cb51539e7e39e7141d994d9ad1709c71fece"
PRODUCT_RUN = "31933502139"
RELEASE_RUN = "31933662718"
CONSUMER_ARTIFACT = "9260019794"
LEARNING_COMMIT = "01723a1825113de08810193f37e8047d978433c2"
KIMI_COMMIT = "5905f5be3f812b801ab5f7ec5b33c65c166131fc"
LYCHEE_ARCHIVE_SHA256 = "1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a"


def load_record():
    return json.loads(RECORD_PATH.read_text(encoding="utf-8"))


def test_p048_completion_record_satisfies_canonical_contract():
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


def test_p048_completion_identity_is_exact_and_scope_bound():
    record = load_record()
    completion = record["completion_record"]
    assert record["subject_id"] == "P-048"
    assert completion["roadmap_id"] == "P-048"
    assert completion["version"] == "0.5.0"
    assert completion["release_or_tag"] == "v0.5.0"
    assert completion["public_url"] == RELEASE
    assert completion["handover"] == HANDOVER
    assert completion["final_status"] == "COMPLETE"
    assert "GitHub-hosted Linux x64" in completion["known_limitations"]
    assert "no self-hosted/private/GHES link checking" in completion["known_limitations"]
    assert "destination semantic correctness/security" in completion["known_limitations"]


def test_p048_release_consumers_and_retained_evidence_are_explicit():
    record = load_record()
    release_gate = record["gates"]["version_tag_or_release_published"]
    acceptance_gate = record["gates"]["real_world_acceptance_test"]
    retained_gate = record["gates"]["evidence_retained"]
    tests_gate = record["gates"]["tests_and_ci"]

    assert RELEASE in release_gate["evidence"]
    assert RELEASE_SOURCE in release_gate["rationale"]
    assert any(RELEASE_RUN in item for item in release_gate["evidence"])
    assert any(PRODUCT_RUN in item for item in tests_gate["evidence"])
    assert any(RELEASE_RUN in item for item in tests_gate["evidence"])
    assert any(LEARNING_COMMIT in item for item in acceptance_gate["evidence"])
    assert any(KIMI_COMMIT in item for item in acceptance_gate["evidence"])
    assert "localhost" in acceptance_gate["rationale"]
    assert any(CONSUMER_ARTIFACT in item for item in retained_gate["evidence"])


def test_all_p048_gate_applicability_is_explicitly_reviewed():
    record = load_record()
    assert len(record["gates"]) == 19
    assert all(gate["state"] == "PASS" for gate in record["gates"].values())
    assert all(gate.get("applicability_reviewed") is True for gate in record["gates"].values())


def test_p048_security_and_supply_chain_boundaries_are_not_erased():
    record = load_record()
    security = record["gates"]["security_and_privacy_review"]
    install = record["gates"]["reproducible_installation_or_use_instructions"]
    completion = record["completion_record"]
    text = json.dumps(record, sort_keys=True)

    assert "SSRF" in security["rationale"]
    assert "GitHub-hosted-only" in security["rationale"]
    assert LYCHEE_ARCHIVE_SHA256 in install["rationale"]
    assert "private" in completion["known_limitations"].lower()
    assert "authenticated" in completion["known_limitations"].lower()
    assert "accessibility conformance" in completion["known_limitations"]
    assert "future-availability" in completion["known_limitations"]
    assert "roadmap completion" not in text.lower() or record["status"] == "COMPLETE"
