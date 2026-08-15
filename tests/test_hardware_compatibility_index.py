from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hardware_compatibility_index import CompatibilityIndexError, build_index

FIXTURE = ROOT / "examples" / "hardware-compatibility-synthetic-v0.2.json"


def synthetic():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def real_report(report_id: str, status: str):
    report = synthetic()
    report["report_id"] = report_id
    report["observation"].update({
        "status": status,
        "summary": f"Reproducible test outcome: {status}",
        "reproduction_runs": 1,
    })
    report["evidence"].update({
        "method": "REPRODUCIBLE_TEST",
        "artifact_hashes": ["a" * 64],
        "reproduction_steps": ["Run the bounded public compatibility test once."],
    })
    report["provenance"].update({
        "reporter_class": "OWNER_TEST",
        "review_status": "HUMAN_REVIEWED",
    })
    return report


def test_synthetic_fixture_never_becomes_real_compatibility_claim():
    result = build_index([synthetic()])
    entry = result["contexts"][0]
    assert entry["aggregate_state"] == "SYNTHETIC_ONLY_NOT_REAL_HARDWARE_EVIDENCE"
    assert entry["real_observation_count"] == 0
    assert entry["synthetic_conformance_count"] == 1
    assert result["claims"]["compatibility_certified"] is False


def test_verified_working_evidence_is_preserved_without_universal_claim():
    result = build_index([real_report("HCC-WORKING-0001", "VERIFIED_WORKING")])
    entry = result["contexts"][0]
    assert entry["aggregate_state"] == "WORKING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM"
    assert entry["status_counts"] == {"VERIFIED_WORKING": 1}
    assert entry["claims"]["universal_compatibility_guaranteed"] is False
    assert entry["claims"]["safe_to_auto_apply"] is False


def test_contradictory_verified_reports_remain_conflicted():
    working = real_report("HCC-WORKING-0002", "VERIFIED_WORKING")
    failing = real_report("HCC-FAILING-0002", "VERIFIED_FAILING")
    failing["evidence"]["artifact_hashes"] = ["b" * 64]
    result = build_index([working, failing])
    assert result["context_count"] == 1
    entry = result["contexts"][0]
    assert entry["aggregate_state"] == "CONFLICT_REQUIRES_REVIEW"
    assert entry["status_counts"] == {"VERIFIED_FAILING": 1, "VERIFIED_WORKING": 1}
    assert entry["claims"]["majority_vote_used_as_truth"] is False


def test_identical_report_digest_is_deduplicated():
    report = real_report("HCC-WORKING-0003", "VERIFIED_WORKING")
    result = build_index([report, copy.deepcopy(report)])
    assert result["input_report_count"] == 1
    assert result["contexts"][0]["report_count"] == 1


def test_different_exact_configuration_forms_distinct_contexts():
    a = real_report("HCC-WORKING-0004", "VERIFIED_WORKING")
    b = real_report("HCC-WORKING-0005", "VERIFIED_WORKING")
    b["configuration"][0]["value"] = "enabled"
    result = build_index([a, b])
    assert result["context_count"] == 2


def test_unsafe_report_is_refused_not_indexed():
    report = real_report("HCC-WORKING-0006", "VERIFIED_WORKING")
    report["observation"]["summary"] = "contact me at person@example.com"
    with pytest.raises(CompatibilityIndexError, match="unsafe/invalid"):
        build_index([report])
