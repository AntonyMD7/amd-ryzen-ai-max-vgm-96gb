import pytest
from scripts.travel_civic_public_info import *

def test_catalog_covers_range_without_authority_claim():
    rows=catalog(); assert [r["roadmap_id"] for r in rows]==list(IDS); assert all(not r["official_determination"] for r in rows)

def test_documents_collect_no_values_or_submit():
    r=document_manifest("travel",["passport","booking"]); assert not r["document_values_collected"]; assert not r["deadline_verified"]; assert not r["document_submitted"]

def test_visa_checklist_is_not_eligibility_or_advice():
    r=visa_checklist("Example","https://example.gov/visa","2026-08-15",["passport"]); assert not r["eligibility_determined"]; assert not r["visa_advice"]; assert not r["application_submitted"]

def test_itinerary_has_no_booking_or_live_claim():
    r=itinerary_plan([{"place":"City","date":"2026-09-01","accessibility_note":"step-free route to confirm"}]); assert not r["booking_performed"]; assert not r["live_availability_verified"]

def test_plain_language_is_plan_not_legal_interpretation():
    r=plain_language_plan("statute","https://example.gov/law"); assert not r["source_text_rewritten"]; assert not r["legal_advice"]; assert not r["official_interpretation"]; assert r["meaning_preservation_review_required"]

def test_open_data_is_manifest_only():
    r=open_data_manifest("https://data.example.gov","budget-2026","Open Government Licence"); assert not r["dataset_downloaded"]; assert not r["figures_verified"]; assert not r["visualization_generated"]

def test_non_https_source_rejected():
    with pytest.raises(PublicInfoError): visa_checklist("Example","http://example.gov","2026-08-15",[])
