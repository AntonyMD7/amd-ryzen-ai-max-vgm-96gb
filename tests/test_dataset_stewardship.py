import pytest

from scripts.dataset_stewardship import DatasetError, evaluate


H1 = "a" * 64
H2 = "b" * 64


def test_quality_profile_uses_counts_not_rows():
    result = evaluate({"mode": "quality", "row_count": 100, "fields": [
        {"name": "text", "missing_count": 5, "invalid_count": 2}
    ]})
    assert result["roadmap_id"] == "P-069"
    assert result["fields"][0]["missing_fraction"] == 0.05
    assert result["semantics"]["dataset_rows_read"] is False


def test_quality_counts_cannot_exceed_rows():
    with pytest.raises(DatasetError):
        evaluate({"mode": "quality", "row_count": 2, "fields": [{"name": "x", "missing_count": 3, "invalid_count": 0}]})


def test_cleaning_plan_is_allowlisted_and_non_mutating():
    result = evaluate({"mode": "cleaning_plan", "source_sha256": H1, "operations": [
        {"operation": "normalize_whitespace", "rule_id": "ws-v1"},
        {"operation": "drop_exact_duplicate", "rule_id": "dedupe-v1"},
    ]})
    assert result["roadmap_id"] == "P-070"
    assert set(result["execution"].values()) == {False}
    with pytest.raises(DatasetError):
        evaluate({"mode": "cleaning_plan", "source_sha256": H1, "operations": [{"operation": "llm_rewrite_every_row", "rule_id": "x"}]})


def test_pii_plan_does_not_claim_to_scan_content():
    result = evaluate({"mode": "pii_plan", "field_classifications": {"email": True, "public_category": False}})
    assert result["roadmap_id"] == "P-071"
    assert result["potentially_sensitive_fields"] == ["email"]
    assert result["execution"]["pii_scan_run"] is False
    assert result["semantics"]["no_flags_means_no_pii"] is False


def test_duplicate_summary_uses_only_caller_supplied_hashes():
    result = evaluate({"mode": "duplicates", "record_sha256": [H1, H2, H1]})
    assert result["roadmap_id"] == "P-072"
    assert result["duplicate_group_count"] == 1
    assert result["duplicate_record_excess"] == 1
    assert result["semantics"]["raw_rows_read"] is False


def test_provenance_missing_license_or_collection_basis_requires_review():
    result = evaluate({
        "mode": "provenance", "dataset_id": "demo-v1", "source_id": "public-source",
        "source_sha256": H1, "license_id": None, "consent_or_collection_basis_documented": False,
    })
    assert result["roadmap_id"] == "P-073"
    assert result["status"] == "REVIEW_REQUIRED"
    assert set(result["missing_review_items"]) == {"license_id", "consent_or_collection_basis_documented"}
    assert result["semantics"]["legal_reuse_permission_proven"] is False


def test_low_resource_plan_prioritizes_gaps_without_collecting_data():
    result = evaluate({"mode": "low_resource_languages", "languages": [
        {"language": "lang-a", "validated_example_count": 1000, "provenance_documented": True, "consent_or_collection_basis_documented": True, "license_reviewed": True},
        {"language": "lang-b", "validated_example_count": 20, "provenance_documented": False, "consent_or_collection_basis_documented": True, "license_reviewed": False},
    ]})
    assert result["roadmap_id"] == "P-075"
    assert result["priority_review_order"][0]["language"] == "lang-b"
    assert set(result["execution"].values()) == {False}


def test_free_text_or_invalid_hashes_fail_closed():
    with pytest.raises(DatasetError):
        evaluate({"mode": "pii_plan", "field_classifications": {"notes": "contains a person name"}})
    with pytest.raises(DatasetError):
        evaluate({"mode": "duplicates", "record_sha256": ["raw record text"]})


def test_unknown_mode_fails_closed():
    with pytest.raises(DatasetError):
        evaluate({"mode": "publish_dataset"})
