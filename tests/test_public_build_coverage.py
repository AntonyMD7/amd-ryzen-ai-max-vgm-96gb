from pathlib import Path

from scripts.public_build_coverage import (
    EXPECTED_IDS,
    FOUNDATION_EVIDENCE,
    FOUNDATION_IDS,
    TRANCHES,
    audit,
    flattened_ids,
)


def test_every_canonical_opportunity_is_mapped_exactly_once():
    actual = flattened_ids()
    assert len(actual) == 227
    assert len(set(actual)) == 227
    assert tuple(sorted(actual)) == EXPECTED_IDS


def test_all_six_foundations_have_evidence_mapping():
    assert tuple(sorted(FOUNDATION_EVIDENCE)) == FOUNDATION_IDS


def test_repository_evidence_paths_exist_and_gate_passes():
    report = audit(Path("."))
    assert report["coverage_gate"] == "PASS"
    assert report["mapped_opportunities"] == 227
    assert report["mapped_foundations"] == 6
    assert report["missing_ids"] == []
    assert report["duplicates"] == []
    assert report["missing_evidence_paths"] == []


def test_coverage_never_becomes_completion_claim():
    report = audit(Path("."))
    assert report["claim"] == "PUBLIC_SOURCE_REFERENCE_COVERAGE_ONLY"
    assert report["roadmap_complete_count"] == 0
    assert report["roadmap_completion_proven"] is False
    assert report["release_proven"] is False
    assert report["real_world_acceptance_proven"] is False


def test_tranches_are_nonempty_and_named():
    assert all(t.name and t.ids and t.evidence_paths for t in TRANCHES)
