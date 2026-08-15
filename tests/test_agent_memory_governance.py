import pytest
from scripts.agent_memory_governance import *

def test_catalog_covers_all_agent_ids_deny_default():
    rows=catalog(); assert [r["roadmap_id"] for r in rows]==list(IDS); assert all(not r["action_authorized"] and not r["secret_values_allowed"] for r in rows)

def test_agent_manifest_has_no_credentials_or_execution():
    r=agent_manifest("agent-1",["read.repo"],["a2a-1.0","mcp"]); assert r["credentials"] is None; assert not r["execution_granted"]

def test_handoff_does_not_delegate_execution_or_reasoning():
    r=handoff("task-1","agent-a","agent-b",["a"*64]); assert not r["target_execution_authorized"]; assert not r["hidden_reasoning_required"]

def test_memory_is_hash_provenance_not_content_export():
    r=memory_record("memory-1","b"*64,"source-1","SENSITIVE",["owner.read"]); assert not r["content_embedded"]; assert not r["cloud_export_authorized"]

def test_approval_gate_fails_closed_for_mutation():
    r=approval_gate("restart-service","HIGH",1); assert not r["authorized"]; assert not r["mutation_performed"]

def test_audit_event_excludes_secrets_prompts_and_hidden_reasoning():
    r=audit_event("event-1","agent-a","read.repo","success","c"*64); assert r["secret_values"] is None; assert r["prompt_content"] is None; assert r["hidden_reasoning"] is None

def test_budget_is_not_billing_or_purchase_authority():
    r=budget_plan("USD",50,2,1000); assert r["remaining"]==48; assert not r["provider_billing_verified"]; assert not r["purchase_authorized"]

def test_sensitive_data_never_gets_implicit_cloud_fallback():
    r=privacy_route("SENSITIVE",False,True); assert r["route"]=="BLOCKED"; assert not r["data_transferred"]; assert not r["implicit_cloud_fallback"]

def test_workflow_is_portable_manifest_not_execution():
    r=portable_workflow("wf-1",[{"id":"step-1","kind":"tool","capability":"read.repo"}]); assert r["vendor_credentials"] is None; assert not r["executed"]

def test_rag_and_voice_are_no_data_action():
    r=rag_manifest("corpus-1","d"*64,4); assert not r["retrieval_executed"]; assert not r["answer_generated"]; assert r["citation_required"]
    v=voice_frontend_manifest(["en","es"]); assert not v["microphone_access"]; assert not v["audio_recorded"]; assert not v["cloud_audio_transfer"]
