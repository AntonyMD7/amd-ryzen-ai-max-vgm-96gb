import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hardware_compatibility_index import build_index  # noqa: E402
from hardware_compatibility_query import CompatibilityQueryError, query_index  # noqa: E402

FIXTURE = ROOT / "examples" / "hardware-compatibility-synthetic-v0.2.json"


def synthetic():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def real_report(report_id: str, status: str, *, feature="disabled"):
    report = synthetic()
    report["report_id"] = report_id
    report["configuration"][0]["value"] = feature
    report["observation"].update(
        {
            "status": status,
            "summary": f"Reproducible public compatibility observation: {status}",
            "reproduction_runs": 1,
        }
    )
    report["evidence"].update(
        {
            "method": "REPRODUCIBLE_TEST",
            "artifact_hashes": [("a" if status == "VERIFIED_WORKING" else "b") * 64],
            "reproduction_steps": ["Run the bounded public compatibility test once."],
        }
    )
    report["provenance"].update(
        {"reporter_class": "OWNER_TEST", "review_status": "HUMAN_REVIEWED"}
    )
    return report


def test_synthetic_contexts_are_excluded_by_default():
    index = build_index([synthetic()])
    result = query_index(index, vendor="example")
    assert result["status"] == "NO_MATCH_NO_COMPATIBILITY_INFERENCE"
    assert result["match_count"] == 0
    assert result["claims"]["absence_of_match_means_incompatible"] is False


def test_synthetic_context_can_be_explicitly_browsed_without_real_claim():
    index = build_index([synthetic()])
    result = query_index(index, vendor="EXAMPLE", include_synthetic=True)
    assert result["match_count"] == 1
    match = result["matches"][0]
    assert match["real_observation_count"] == 0
    assert match["aggregate_state"] == "SYNTHETIC_ONLY_NOT_REAL_HARDWARE_EVIDENCE"
    assert match["claims"]["compatibility_certified"] is False


def test_vendor_model_os_and_configuration_filters_are_composable():
    report = real_report("HCC-QUERY-0001", "VERIFIED_WORKING", feature="enabled")
    index = build_index([report])
    result = query_index(
        index,
        vendor="example vendor",
        model="reference",
        architecture="x86",
        os_name="exampleos",
        os_version="1.0",
        configuration_key="feature_mode",
        configuration_value="enabled",
    )
    assert result["match_count"] == 1
    assert result["matches"][0]["aggregate_state"] == "WORKING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM"


def test_conflict_is_returned_not_resolved_or_ranked_away():
    working = real_report("HCC-QUERY-WORKING", "VERIFIED_WORKING")
    failing = real_report("HCC-QUERY-FAILING", "VERIFIED_FAILING")
    index = build_index([working, failing])
    result = query_index(index, aggregate_state="CONFLICT_REQUIRES_REVIEW")
    assert result["match_count"] == 1
    match = result["matches"][0]
    assert match["aggregate_state"] == "CONFLICT_REQUIRES_REVIEW"
    assert match["status_counts"] == {"VERIFIED_FAILING": 1, "VERIFIED_WORKING": 1}
    assert match["claims"]["conflict_resolved_by_query"] is False
    assert match["claims"]["popularity_used_as_truth"] is False


def test_nonmatching_filter_never_means_incompatible():
    report = real_report("HCC-QUERY-0002", "VERIFIED_WORKING")
    result = query_index(build_index([report]), model="definitely-not-this-model")
    assert result["status"] == "NO_MATCH_NO_COMPATIBILITY_INFERENCE"
    assert result["claims"]["absence_of_match_means_incompatible"] is False


def test_unsafe_upstream_index_claim_is_refused():
    index = build_index([real_report("HCC-QUERY-0003", "VERIFIED_WORKING")])
    index["claims"]["compatibility_certified"] = True
    with pytest.raises(CompatibilityQueryError, match="unsafe index claim"):
        query_index(index)


def test_query_never_performs_external_lookup_or_auto_apply():
    result = query_index(build_index([real_report("HCC-QUERY-0004", "VERIFIED_WORKING")]))
    assert result["claims"]["external_lookup_performed"] is False
    assert result["claims"]["safe_to_auto_apply"] is False
    assert result["claims"]["majority_vote_used_as_truth"] is False
