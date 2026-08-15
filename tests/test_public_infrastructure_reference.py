import pytest
from scripts.public_infrastructure_reference import *

def test_catalog_covers_all_ids_without_completion_claims():
    rows=catalog(); assert [r["roadmap_id"] for r in rows]==list(IDS); assert all(not r["mutation"] and not r["secret_values"] and not r["completion_claim"] for r in rows)

def test_safefix_mutation_requires_recovery_and_approval_and_never_executes():
    assert not safefix_plan("op-1","MUTATING",True,False)["authorized"]
    r=safefix_plan("op-1","MUTATING",True,True); assert r["authorized"]; assert not r["executed"]

def test_evidence_envelope_does_not_equate_hash_with_truth():
    r=evidence_envelope("ev-1","artifact-1","a"*64,["slsa-v1.2"]); assert not r["signature_verified"]; assert not r["event_truth_proven"]

def test_attestation_is_plan_only_and_privacy_minimized():
    r=device_attestation("node-1","linux","b"*64); assert not r["probe_executed"]; assert not r["unique_identifiers_collected"]; assert r["state"]=="PLAN_ONLY"

def test_fleet_has_no_remote_execution_or_orchestration():
    r=fleet_snapshot([{"node_id":"node-1","evidence_hash":"c"*64,"status":"healthy"}]); assert not r["remote_command_executed"]; assert not r["dashboard_served"]; assert not r["orchestration_performed"]

def test_compatibility_is_observation_not_guarantee():
    r=compatibility_record("gpu-1","driver-1","PASS","d"*64); assert not r["compatibility_guarantee"]; assert not r["community_submission_published"]

def test_community_evidence_and_graph_not_published_or_causal():
    r=community_evidence_record("rec-1","e"*64,True); assert not r["contains_secret_values"]; assert not r["published"]
    g=troubleshooting_graph_case("case-1",["no-audio"],["device-present"],"f"*64); assert not g["root_cause_claim"]; assert not g["graph_written"]

def test_reference_and_architecture_are_not_release_or_deployment_claims():
    r=reference_implementation("component-1","1"*64,True); assert not r["released"]; assert not r["production_ready_claim"]
    k=architecture_kit("kit-1",["api","db"],"2"*64); assert not k["infrastructure_deployed"]; assert not k["reproducibility_proven"]

def test_problem_solution_requires_search_and_safety_before_build_authorization():
    assert not problem_solution_intake("p-1","problem",False,True)["build_authorized"]
    r=problem_solution_intake("p-1","problem",True,True); assert r["build_authorized"]; assert not r["repository_created"]; assert not r["solution_complete"]
