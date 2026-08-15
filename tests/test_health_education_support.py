from __future__ import annotations

import pytest

from scripts.health_education_support import (
    HealthSafetyError,
    anatomy_education_manifest,
    clinical_calculator_manifest,
    emergency_preparedness_checklist,
    emergency_workflow_manifest,
    evidence_navigation_plan,
    health_literacy_plan,
    medication_education_manifest,
    medication_interaction_information_plan,
    medication_list_manifest,
    medical_inventory_snapshot,
    offline_medical_reference_manifest,
    remote_handover_template,
)


SOURCE = {
    "name": "Example public authority",
    "url": "https://example.org/reference",
    "version": "2026.08",
}


def test_anatomy_manifest_is_education_only():
    result = anatomy_education_manifest("upper limb", [SOURCE])
    assert result["roadmap_id"] == "P-134"
    assert result["clinical_decision_support"] is False
    assert result["diagnosis"] is False
    assert result["treatment_guidance"] is False


def test_medication_manifest_identifies_but_does_not_advise():
    result = medication_education_manifest("Example medicine", "12345", SOURCE)
    assert result["identity_authority"] == "NLM RxNorm"
    assert result["personalized_advice"] is False
    assert result["dose_recommendation"] is False
    assert result["interaction_clearance"] is False


def test_medication_manifest_rejects_non_rxcui():
    with pytest.raises(HealthSafetyError):
        medication_education_manifest("Example medicine", "patient-abc", SOURCE)


def test_source_url_rejects_credential_query():
    bad = dict(SOURCE, url="https://example.org/reference?api_key=secret")
    with pytest.raises(HealthSafetyError):
        anatomy_education_manifest("heart", [bad])


def test_calculator_framework_does_not_execute_formula():
    result = clinical_calculator_manifest(
        "demo-score",
        "1.0",
        SOURCE,
        inputs=[{"name": "age", "unit": "year", "type": "number"}],
        reference_vectors=[{"input": {"age": 50}, "expected": 1}],
    )
    assert result["roadmap_id"] == "P-136"
    assert result["formula_execution_enabled"] is False
    assert result["clinical_use_enabled"] is False
    assert result["reference_vectors_present"] is True


def test_evidence_navigation_is_plan_only():
    result = evidence_navigation_plan("hypertension systematic review")
    assert result["upstream"] == "NCBI Entrez E-utilities"
    assert result["network_request_performed"] is False
    assert result["evidence_quality_claim"] is False


def test_inventory_rejects_person_fields_and_tracks_no_procurement():
    result = medical_inventory_snapshot(
        [{"item": "gauze", "quantity": 10, "unit": "pack", "expiry_month": "2027-06"}]
    )
    assert result["patient_data"] is False
    assert result["procurement_action_performed"] is False
    with pytest.raises(HealthSafetyError):
        medical_inventory_snapshot(
            [{"item": "gauze", "quantity": 10, "patient_name": "Example Person"}]
        )


def test_handover_public_template_contains_no_patient_data():
    result = remote_handover_template()
    assert result["contains_patient_data"] is False
    assert result["public_example_requires_synthetic_data"] is True


def test_emergency_workflow_embeds_no_clinical_steps():
    result = emergency_workflow_manifest(
        "approved-protocol", "2026.1", "example-jurisdiction", "https://example.org/protocol"
    )
    assert result["clinical_steps_embedded"] is False
    assert result["execution_enabled"] is False


def test_health_literacy_requires_review_and_does_not_transform():
    result = health_literacy_plan("public-handout", "en", "es")
    assert result["preserve_numbers_units_warnings"] is True
    assert result["clinical_meaning_review_required"] is True
    assert result["content_transformed"] is False


def test_medication_list_has_no_patient_identifier_or_cloud_authorization():
    result = medication_list_manifest([{"display_name": "Example medicine", "rxcui": "12345"}])
    assert result["patient_identifier"] is None
    assert result["cloud_upload_authorized"] is False
    assert result["clinical_reconciliation_performed"] is False


def test_interaction_plan_never_claims_safe_or_unsafe():
    result = medication_interaction_information_plan(["123", "456"])
    assert result["interaction_check_performed"] is False
    assert result["safe_combination_claim"] is False
    assert result["unsafe_combination_claim"] is False


def test_offline_reference_fails_closed_without_rights():
    digest = "a" * 64
    result = offline_medical_reference_manifest(
        "Reference", "https://example.org/reference", "2026.1", "NOT_CONFIRMED", digest
    )
    assert result["publishable"] is False
    assert result["offline_package_created"] is False
    assert result["clinical_currency_verified"] is False


def test_preparedness_is_general_not_location_specific_or_clinical():
    result = emergency_preparedness_checklist()
    assert result["location_specific_instructions_embedded"] is False
    assert result["emergency_service_contact_inferred"] is False
    assert result["medical_treatment_guidance"] is False
