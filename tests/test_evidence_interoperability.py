import pytest
from scripts.evidence_interoperability import *

REC={
 "schema_version":"0.1","evidence_id":"DAIS-EV-12345","evidence_type":"verification","roadmap_ids":["F-05"],
 "subject":{"type":"software","id":"demo","version":"1"},
 "operation":{"classification":"VERIFY","name":"test","intended_change":None,"authorization_ref":None},
 "observed_at_utc":"2026-08-15T05:00:00Z","result":{"status":"PASS"},
 "artifacts":[{"name":"artifact.bin","sha256":"a"*64,"media_type":"application/octet-stream"}],
 "rollback":{"required":False,"established":False},
 "safety":{"secrets_redacted":True,"private_infrastructure_redacted":True,"human_approval_required":False,"approval_present":False},
 "provenance":{"producer":"ci","source_commit":"1234567","upstream_refs":[]},"limitations":[]
}

def test_manifest_never_claims_truth_or_signature():
 r=interoperability_manifest(REC); assert not r["truth_claim"]; assert not r["signature_verified"]; assert not r["mappings"]["in_toto"]["semantic_conformance_verified"]

def test_in_toto_plan_is_unsigned_and_maps_hash_only():
 r=in_toto_statement_plan(REC); assert r["statement"]["_type"]=="https://in-toto.io/Statement/v1"; assert r["statement"]["subject"][0]["digest"]["sha256"]=="a"*64; assert not r["signed"]; assert not r["in_toto_conformance_verified"]

def test_slsa_mapping_fails_honestly_on_missing_semantics():
 r=slsa_build_provenance_readiness(REC); assert not r["ready"]; assert "builder_identity" in r["missing_semantics"]; assert r["slsa_level_claim"] is None

def test_otel_plan_excludes_sensitive_content_and_does_not_export():
 r=otel_log_event_plan(REC); assert r["body"] is None; assert r["prompt_content"] is None; assert r["secret_values"] is None; assert not r["export_performed"]

def test_prov_plan_is_conceptual_not_validated_serialization():
 r=w3c_prov_plan(REC); assert not r["serialization_generated"]; assert not r["prov_constraints_validated"]

def test_sbom_links_are_external_not_parsed_or_verified():
 for kind in ("SPDX","CYCLONEDX"):
  r=external_composition_reference(REC,kind,"bom.json","b"*64); assert not r["document_parsed"]; assert not r["schema_validated"]; assert not r["signature_verified"]

def test_unredacted_evidence_is_refused():
 bad={**REC,"safety":{**REC["safety"],"secrets_redacted":False}}
 with pytest.raises(InteropError): interoperability_manifest(bad)
