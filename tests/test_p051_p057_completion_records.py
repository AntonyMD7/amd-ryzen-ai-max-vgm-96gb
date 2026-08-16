import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_build_completion_contract import audit_record  # noqa: E402

EXPECTED = {
    "P-051": ROOT / "examples/public-build-completion-p051-v0.2.0.json",
    "P-057": ROOT / "examples/public-build-completion-p057-v0.2.0.json",
}
RELEASE = "https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/releases/tag/v0.2.0"
HANDOVER = "docs/P051-P057-COMPLETION-RECORD-v0.2.0.md"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_p051_and_p057_completion_records_satisfy_canonical_contract():
    for subject, path in EXPECTED.items():
        record = load(path)
        report = audit_record(record)
        assert report["errors"] == [], (subject, report["errors"])
        assert report["declared_status"] == "COMPLETE"
        assert report["readiness"] == "COMPLETE_CONTRACT_SATISFIED"
        assert report["completion_contract_satisfied"] is True
        assert report["blocking_gates"] == []
        assert report["gate_counts"]["PASS"] == 19
        assert report["project_completion_record_populated"] is True
        assert report["safe_public_evidence_prefilter"] is True


def test_completion_records_bind_same_released_toolkit_without_cross_id_drift():
    p051 = load(EXPECTED["P-051"])
    p057 = load(EXPECTED["P-057"])
    for expected_id, record in (("P-051", p051), ("P-057", p057)):
        completion = record["completion_record"]
        assert record["subject_id"] == expected_id
        assert completion["roadmap_id"] == expected_id
        assert completion["version"] == "0.2.0"
        assert completion["release_or_tag"] == "v0.2.0"
        assert completion["public_url"] == RELEASE
        assert completion["handover"] == HANDOVER
        assert completion["final_status"] == "COMPLETE"


def test_release_gate_keeps_exact_source_and_real_acceptance_evidence_visible():
    for path in EXPECTED.values():
        record = load(path)
        release_gate = record["gates"]["version_tag_or_release_published"]
        acceptance_gate = record["gates"]["real_world_acceptance_test"]
        retained_gate = record["gates"]["evidence_retained"]
        assert RELEASE in release_gate["evidence"]
        assert any("31926735521" in item for item in acceptance_gate["evidence"])
        assert any("9258058715" in item for item in retained_gate["evidence"])
        assert any("9258056770" in item for item in retained_gate["evidence"])
        assert "7fa66e4dd3d851b7fe6750cf7ee3d1f084d9811e" in release_gate["rationale"]
