import pytest
from scripts.cyber_privacy_trust import TrustError,evaluate
H="a"*64

def test_home_network_is_passive_plan_only():
 r=evaluate({"mode":"home_network","facts":{"router_admin_password_changed":True,"guest_network_enabled":False}});assert r["roadmap_id"]=="P-121";assert r["mode"]=="PASSIVE_PLAN_ONLY";assert set(r["execution"].values())=={False}

def test_log_explainer_never_attributes_cause():
 r=evaluate({"mode":"log","event_type":"auth-failure","severity":"warning"});assert r["roadmap_id"]=="P-122";assert r["semantics"]["cause_attributed"] is False

def test_dependency_scan_reuses_specialists_and_claims_no_scan():
 r=evaluate({"mode":"dependency","ecosystem":"python","lockfile_present":True});assert r["roadmap_id"]=="P-123";assert "OSV-Scanner" in r["recommended_engines"];assert r["semantics"]["scan_run"] is False

def test_metadata_and_redaction_require_copy_review_and_do_not_mutate():
 m=evaluate({"mode":"metadata","file_type":"jpeg","backup_ready":False});assert m["roadmap_id"]=="P-124" and m["disposition"]=="BLOCKED_BACKUP_REQUIRED"
 d=evaluate({"mode":"redaction","document_kind":"pdf"});assert d["roadmap_id"]=="P-125" and d["execution"]["file_modified"] is False;assert d["semantics"]["all_sensitive_content_found"] is False

def test_permission_audit_surfaces_sensitive_or_unneeded():
 r=evaluate({"mode":"permissions","permissions":[{"permission":"camera","required":False,"sensitive":True},{"permission":"storage","required":True,"sensitive":False}]});assert r["roadmap_id"]=="P-126";assert len(r["findings"])==1

def test_suspicious_message_and_scam_never_certify_safety():
 m=evaluate({"mode":"message","cues":{"urgency":False,"domain_mismatch":False}});assert m["roadmap_id"]=="P-127";assert m["disposition"]=="NO_CUES_REPORTED_NOT_SAFE_CERTIFICATE";assert m["semantics"]["message_safe_proven"] is False
 s=evaluate({"mode":"scam","facts":{}});assert s["roadmap_id"]=="P-128" and s["disposition"]=="INSUFFICIENT_TO_CERTIFY_SAFE"

def test_invoice_flags_changed_bank_but_does_not_prove_fraud():
 r=evaluate({"mode":"invoice","amount":110,"baseline_amount":100,"bank_details_changed":True,"vendor_identity_changed":False});assert r["roadmap_id"]=="P-129";assert "BANK_DETAILS_CHANGED" in r["flags"];assert r["semantics"]["fraud_proven"] is False

def test_privacy_boundary_denies_sensitive_public_cloud_prefilter():
 r=evaluate({"mode":"privacy","data_class":"sensitive","destination":"public_cloud"});assert r["roadmap_id"]=="P-130";assert r["decision"]=="POLICY_PREFILTER_DENY_OR_REVIEW";assert r["semantics"]["data_sent"] is False

def test_provenance_requires_digest_and_no_external_attestation_claim():
 r=evaluate({"mode":"provenance","source_id":"source-v1","artifact_sha256":H});assert r["roadmap_id"]=="P-131";assert r["semantics"]["provenance_verified_externally"] is False
 with pytest.raises(TrustError):evaluate({"mode":"provenance","source_id":"source-v1","artifact_sha256":"bad"})

def test_claim_evidence_keeps_claim_unproven():
 r=evaluate({"mode":"claim","claim_id":"claim-1","evidence":[{"evidence_id":"e1","supports":True,"independent":True}]});assert r["roadmap_id"]=="P-132";assert r["independent_support_count"]==1;assert r["semantics"]["claim_proven"] is False

def test_agent_permission_denies_out_of_allowlist_and_executes_nothing():
 r=evaluate({"mode":"agent","requested_actions":["read","delete"],"allowed_actions":["read"]});assert r["roadmap_id"]=="P-133";assert r["decision"]=="DENY";assert r["denied_actions"]==["delete"];assert r["semantics"]["action_executed"] is False

def test_unbounded_or_wrong_types_fail_closed():
 with pytest.raises(TrustError):evaluate({"mode":"message","cues":{"raw message text":"hello"}})
 with pytest.raises(TrustError):evaluate({"mode":"invoice","amount":"100","baseline_amount":100,"bank_details_changed":False,"vendor_identity_changed":False})
 with pytest.raises(TrustError):evaluate({"mode":"unknown"})
