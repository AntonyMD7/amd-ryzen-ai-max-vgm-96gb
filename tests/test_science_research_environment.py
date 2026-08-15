import pytest
from scripts.science_research_environment import *

def test_catalog_covers_range_without_execution_or_conclusion():
    rows=catalog(); assert [r["roadmap_id"] for r in rows]==list(IDS); assert all(not r["execution"] and not r["scientific_conclusion"] for r in rows)

def test_paper_manifest_does_not_copy_or_rank():
    r=paper_manifest("10.1234/example","Example","https://doi.org/10.1234/example"); assert not r["full_text_copied"]; assert not r["claims_extracted"]; assert not r["quality_ranked"]

def test_reproducibility_manifest_is_evidence_not_proof():
    r=reproducibility_manifest([{"path_label":"results.csv","sha256":"a"*64,"role":"result"}]); assert not r["environment_captured"]; assert not r["experiment_executed"]; assert not r["reproducibility_proven"]

def test_dataset_provenance_does_not_verify_rights():
    r=dataset_provenance("demo","https://example.org/data","CC0","b"*64); assert not r["data_read"]; assert not r["rights_verified"]

def test_open_data_and_api_are_no_network():
    assert not open_data_plan("https://data.example.org","water")["request_performed"]
    r=api_wrapper_manifest("demo","https://api.example.org",["list"]); assert not r["credentials_accepted"]; assert not r["code_generated"]; assert not r["network_request_performed"]

def test_environmental_manifest_is_not_safety_determination():
    r=environmental_dataset("weather","https://example.org/weather","2026-08-15T00:00:00Z",["wind"]); assert not r["data_fetched"]; assert not r["risk_or_safety_determination"]

def test_energy_is_arithmetic_not_measurement():
    r=energy_estimate(100,10,.2); assert r["kwh"]==1.0; assert r["estimated_cost"]==.2; assert not r["measured_energy"]; assert not r["efficiency_certification"]; assert not r["live_tariff_verified"]

def test_invalid_doi_rejected():
    with pytest.raises(ResearchError): paper_manifest("abc","x","https://example.org")
