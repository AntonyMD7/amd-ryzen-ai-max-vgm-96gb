from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from public_build_completion_contract import audit_record  # noqa: E402


COMPLETE = ROOT / "examples" / "public-build-completion-p025-v0.1.0.json"
HANDOVER = ROOT / "docs" / "P025-COMPLETION-RECORD-v0.1.0.md"


def test_p025_v010_completion_record_satisfies_canonical_contract():
    record = json.loads(COMPLETE.read_text(encoding="utf-8"))
    report = audit_record(record)
    assert report["errors"] == []
    assert report["declared_status"] == "COMPLETE"
    assert report["blocking_gates"] == []
    assert report["readiness"] == "COMPLETE_CONTRACT_SATISFIED"
    assert report["completion_contract_satisfied"] is True
    # READY_FOR_CANONICAL_COMPLETION_REVIEW is the pre-completion state.
    # Once the explicit COMPLETE record satisfies the contract, the auditor
    # transitions to the terminal COMPLETE_CONTRACT_SATISFIED state instead.
    assert report["ready_for_canonical_completion_review"] is False
    assert record["completion_record"]["version"] == "0.1.0"
    assert record["completion_record"]["release_or_tag"] == "v0.1.0"
    assert record["completion_record"]["handover"] == "docs/P025-COMPLETION-RECORD-v0.1.0.md"
    assert HANDOVER.is_file()


def test_completion_record_preserves_scope_limitations():
    record = json.loads(COMPLETE.read_text(encoding="utf-8"))
    text = json.dumps(record, sort_keys=True).lower()
    assert "reference configuration" in text
    assert "not a wcag conformance claim" in text
    assert "primarily english" in text
    assert "universal compatibility" not in record["completion_record"]["real_world_test"].lower()


def test_historical_in_progress_fixture_remains_historical_and_incomplete():
    historical = json.loads(
        (ROOT / "examples" / "public-build-completion-p025-in-progress.json").read_text(encoding="utf-8")
    )
    report = audit_record(historical)
    assert report["declared_status"] == "IN_PROGRESS"
    assert set(report["blocking_gates"]) == {
        "version_tag_or_release_published",
        "canonical_handover_or_build_record_updated",
    }
    assert report["completion_contract_satisfied"] is False
