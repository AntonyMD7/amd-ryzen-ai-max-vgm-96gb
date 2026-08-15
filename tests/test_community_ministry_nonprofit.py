from __future__ import annotations

import pytest

from scripts.community_ministry_nonprofit import (
    CommunitySafetyError,
    bible_study_plan,
    community_event_manifest,
    donation_admin_manifest,
    language_study_dataset_manifest,
    resource_library_manifest,
    scripture_source_manifest,
    sermon_corpus_manifest,
    volunteer_schedule_plan,
)


def test_volunteer_plan_does_not_assign_people_or_mutate_calendar():
    result = volunteer_schedule_plan([{"role": "greeter", "slots": 2, "skills": ["welcome"]}])
    assert result["roadmap_id"] == "P-148"
    assert result["personal_data"] is False
    assert result["volunteers_assigned"] is False
    assert result["calendar_mutated"] is False


def test_event_manifest_has_no_registration_or_payment_side_effect():
    result = community_event_manifest("clinic-day", "Community clinic day", "America/Guyana", capacity=50)
    assert result["roadmap_id"] == "P-149"
    assert result["registrations_collected"] is False
    assert result["ticketing_or_payment_enabled"] is False


def test_donation_admin_never_collects_payment_credentials():
    result = donation_admin_manifest("school-drive", "GYD", ["education", "supplies"])
    assert result["roadmap_id"] == "P-150"
    assert result["donor_identity_collected"] is False
    assert result["payment_credentials_collected"] is False
    assert result["payment_processed"] is False
    assert result["tax_receipt_claim"] is False


def test_resource_library_requires_explicit_rights_metadata():
    result = resource_library_manifest([
        {"id": "guide-en", "title": "Community guide", "language": "en", "source_url": "https://example.org/guide", "rights": "CC-BY-4.0"}
    ])
    assert result["content_downloaded"] is False
    assert result["redistribution_authorized"] is False
    with pytest.raises(CommunitySafetyError):
        resource_library_manifest([
            {"id": "bad", "title": "No rights", "language": "en", "source_url": "https://example.org/guide"}
        ])


def test_scripture_source_records_rights_without_copying_text():
    result = scripture_source_manifest("step-data", "STEPBible Data", "https://github.com/STEPBible/STEPBible-Data", "CC BY 4.0", "en")
    assert result["roadmap_id"] == "P-152"
    assert result["scripture_text_copied"] is False
    assert result["search_index_built"] is False
    assert result["rights_review_required"] is True


def test_bible_study_is_not_theological_authority():
    result = bible_study_plan("covenant", ["step-data"], "en")
    assert result["roadmap_id"] == "P-153"
    assert result["retrieval_performed"] is False
    assert result["theological_authority_claim"] is False


def test_sermon_manifest_never_embeds_private_corpus():
    result = sermon_corpus_manifest([
        {"document_id": "sermon-001", "title": "Example sermon", "rights": "owner-controlled", "sha256": "a" * 64}
    ])
    assert result["roadmap_id"] == "P-154"
    assert result["content_embedded"] is False
    assert result["private_material_uploaded"] is False
    assert result["index_built"] is False


def test_language_study_manifest_is_metadata_only():
    result = language_study_dataset_manifest("step-lexicon", "https://github.com/STEPBible/STEPBible-Data", "CC BY 4.0", ["lemma", "gloss"])
    assert result["roadmap_id"] == "P-155"
    assert result["dataset_downloaded"] is False
    assert result["linguistic_interpretation_generated"] is False
    assert len(result["manifest_fingerprint"]) == 64


def test_credential_bearing_source_url_is_rejected():
    with pytest.raises(CommunitySafetyError):
        scripture_source_manifest("bad-source", "Bad", "https://user:pass@example.org/text", "unknown", "en")
