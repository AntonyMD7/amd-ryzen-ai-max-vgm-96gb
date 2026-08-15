import pytest
from scripts.health_support_planner import HealthError,evaluate
H="a"*64

def assert_no_clinical_decision(r): assert set(r["clinical_boundary"].values())=={False}

def test_anatomy_and_mechanism_are_education_source_plans():
 a=evaluate({"mode":"anatomy","structure_id":"heart"});m=evaluate({"mode":"mechanism","drug_concept_id":"rxnorm-123"})
 assert a["roadmap_id"]=="P-134";assert m["roadmap_id"]=="P-135";assert_no_clinical_decision(a);assert_no_clinical_decision(m);assert m["semantics"]["mechanism_generated"] is False

def test_calculator_blocks_without_external_validation_and_does_not_calculate():
 r=evaluate({"mode":"calculator","formula_id":"example-score","formula_version":"1","external_validation_documented":False});assert r["roadmap_id"]=="P-136";assert r["disposition"]=="BLOCKED_VALIDATION_REQUIRED";assert r["execution"]["calculation_performed"] is False;assert_no_clinical_decision(r)

def test_evidence_navigation_is_retrieval_plan_only():
 r=evaluate({"mode":"evidence","topic_id":"hypertension"});assert r["roadmap_id"]=="P-137";assert r["execution"]["literature_search_run"] is False;assert r["semantics"]["evidence_quality_appraised"] is False

def test_equipment_and_inventory_surface_gaps_without_orders():
 e=evaluate({"mode":"equipment","items":[{"item_id":"aed","present":True,"in_date":False,"functional_check_documented":True}]});assert e["roadmap_id"]=="P-138" and len(e["gaps"])==1
 i=evaluate({"mode":"inventory","stock":[{"item_id":"gloves","quantity":2,"minimum":5}]});assert i["roadmap_id"]=="P-139" and i["stock"][0]["reorder_review"] is True and i["execution"]["order_placed"] is False

def test_handover_accepts_presence_flags_not_patient_content():
 r=evaluate({"mode":"handover","sections":{"situation":True,"background":True,"assessment":True,"recommendation":False,"pending_tasks":True,"allergies_medications_reviewed":True}});assert r["roadmap_id"]=="P-140";assert r["missing_sections"]==["recommendation"];assert r["privacy"]["patient_content_accepted"] is False

def test_emergency_workflow_never_executes_or_triages():
 r=evaluate({"mode":"emergency_workflow","protocol_id":"local-protocol","protocol_version":"2026-01"});assert r["roadmap_id"]=="P-141";assert r["execution"]["protocol_step_executed"] is False;assert r["clinical_boundary"]["triage_disposition_made"] is False

def test_public_health_and_literacy_preserve_authority_and_no_transform():
 p=evaluate({"mode":"public_health","source_id":"public-health-authority","source_date":"2026-08-15"});l=evaluate({"mode":"literacy","language":"en"});assert p["roadmap_id"]=="P-142";assert l["roadmap_id"]=="P-143";assert l["execution"]["patient_text_transformed"] is False

def test_medication_list_does_not_infer_or_read_medicines():
 r=evaluate({"mode":"med_list","medication_count":4});assert r["roadmap_id"]=="P-144";assert r["execution"]["medications_read"] is False;assert "do not infer missing dose" in r["requirements"]

def test_interaction_interface_never_clears_combination():
 r=evaluate({"mode":"interaction","drug_count":2});assert r["roadmap_id"]=="P-145";assert r["clinical_boundary"]["interaction_conclusion_made"] is False;assert "does not determine" in r["warning"]

def test_offline_medical_reference_requires_digest_and_no_download():
 r=evaluate({"mode":"offline_reference","source_id":"authority","version":"2026-08","sha256":H});assert r["roadmap_id"]=="P-146";assert set(r["execution"].values())=={False}
 with pytest.raises(HealthError):evaluate({"mode":"offline_reference","source_id":"authority","version":"1","sha256":"bad"})

def test_preparedness_is_source_plan_not_patient_advice():
 r=evaluate({"mode":"preparedness","profile":"general"});assert r["roadmap_id"]=="P-147";assert r["execution"]["medical_advice_generated"] is False;assert_no_clinical_decision(r)

def test_invalid_inputs_fail_closed():
 with pytest.raises(HealthError):evaluate({"mode":"interaction","drug_count":1})
 with pytest.raises(HealthError):evaluate({"mode":"calculator","formula_id":"bad formula with spaces","formula_version":"1","external_validation_documented":True})
 with pytest.raises(HealthError):evaluate({"mode":"unknown"})
