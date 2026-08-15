import pytest

from scripts.offline_access_planner import OfflinePlanError, evaluate


DIGEST = "a" * 64


def test_offline_knowledge_requires_license_and_provenance_review():
    result = evaluate({"mode":"knowledge_package","package_id":"kit","version":"1","sha256":DIGEST,"license_id":None,"provenance_documented":False})
    assert result["roadmap_id"] == "P-101"
    assert result["status"] == "REVIEW_REQUIRED"
    assert set(result["execution"].values()) == {False}


def test_low_bandwidth_web_surfaces_reference_budget_gaps_without_fetching():
    result = evaluate({"mode":"low_bandwidth_web","initial_payload_bytes":600000,"javascript_bytes":300000,"core_task_without_js":False,"core_assets_cacheable":False})
    assert result["roadmap_id"] == "P-102"
    assert len(result["findings"]) == 4
    assert result["execution"]["url_fetched"] is False


def test_education_and_emergency_reference_ids():
    for kind, roadmap in (("education","P-103"),("emergency","P-104")):
        result = evaluate({"mode":"reference_manifest","kind":kind,"source_id":"authority","version":"2026-08","reviewed_at":"2026-08-15"})
        assert result["roadmap_id"] == roadmap
        assert result["semantics"]["currency_or_accuracy_certified"] is False


def test_translation_pack_is_metadata_only():
    result = evaluate({"mode":"translation_pack","engine_id":"local-engine","source_language":"en","target_language":"es","artifact_sha256":DIGEST})
    assert result["roadmap_id"] == "P-105"
    assert set(result["execution"].values()) == {False}


def test_offline_rag_does_not_read_or_index_documents():
    result = evaluate({"mode":"offline_rag","corpus_id":"education-v1","document_count":20,"embedding_engine":"local-embed-v1"})
    assert result["roadmap_id"] == "P-106"
    assert set(result["execution"].values()) == {False}
    assert "retrieval citations" in result["requirements"]


def test_chunk_distribution_math_and_no_write():
    result = evaluate({"mode":"distribution","total_bytes":1001,"chunk_bytes":500})
    assert result["roadmap_id"] == "P-107"
    assert result["chunk_count"] == 3
    assert set(result["execution"].values()) == {False}


def test_sync_preserves_conflicts_instead_of_last_writer_wins():
    result = evaluate({"mode":"sync","local_revision":"a1","remote_revision":"b1","same_known_base":True,"local_changed":True,"remote_changed":True})
    assert result["roadmap_id"] == "P-108"
    assert result["disposition"] == "CONFLICT_REQUIRES_POLICY_OR_HUMAN_REVIEW"
    assert set(result["execution"].values()) == {False}


def test_unknown_base_never_auto_merges():
    result = evaluate({"mode":"sync","local_revision":"a1","remote_revision":"b1","same_known_base":False,"local_changed":False,"remote_changed":True})
    assert result["disposition"] == "RECONCILIATION_REQUIRED_UNKNOWN_BASE"


def test_invalid_digests_and_unbounded_identifiers_fail_closed():
    with pytest.raises(OfflinePlanError):
        evaluate({"mode":"knowledge_package","package_id":"bad id with spaces","version":"1","sha256":DIGEST,"license_id":"MIT","provenance_documented":True})
    with pytest.raises(OfflinePlanError):
        evaluate({"mode":"translation_pack","engine_id":"x","source_language":"en","target_language":"es","artifact_sha256":"bad"})
    with pytest.raises(OfflinePlanError):
        evaluate({"mode":"distribution","total_bytes":1,"chunk_bytes":0})


def test_unknown_mode_fails_closed():
    with pytest.raises(OfflinePlanError):
        evaluate({"mode":"sync_everything_without_review"})
