#!/usr/bin/env python3
"""Fail-honest interoperability adapters for DAIS Universal Evidence.

Adapters create *mapping plans* and unsigned interchange objects only. They do
not claim signature verification, SLSA conformance, telemetry export, SBOM
validation, or provenance truth merely because fields can be mapped.
"""
from __future__ import annotations
import re
from typing import Any

SHA256=re.compile(r"^[0-9a-fA-F]{64}$")

class InteropError(ValueError): pass

def _require_record(record:dict[str,Any])->None:
    for key in ("evidence_id","evidence_type","subject","operation","observed_at_utc","result","safety","provenance","limitations"):
        if key not in record: raise InteropError(f"missing Universal Evidence field: {key}")
    if record.get("safety",{}).get("secrets_redacted") is not True: raise InteropError("secrets_redacted must be true")
    if record.get("safety",{}).get("private_infrastructure_redacted") is not True: raise InteropError("private_infrastructure_redacted must be true")

def interoperability_manifest(record:dict[str,Any])->dict[str,Any]:
    _require_record(record)
    return {
        "evidence_id":record["evidence_id"],
        "universal_evidence_schema":record.get("schema_version"),
        "mappings":{
            "in_toto":{"mode":"UNSIGNED_STATEMENT_PLAN","semantic_conformance_verified":False},
            "slsa":{"mode":"REFERENCE_ONLY","semantic_conformance_verified":False},
            "opentelemetry":{"mode":"LOG_EVENT_PLAN","export_performed":False},
            "w3c_prov":{"mode":"CONCEPTUAL_MAPPING","semantic_conformance_verified":False},
            "spdx":{"mode":"EXTERNAL_REFERENCE_ONLY","sbom_validated":False},
            "cyclonedx":{"mode":"EXTERNAL_REFERENCE_ONLY","bom_validated":False},
        },
        "truth_claim":False,
        "signature_verified":False,
    }

def in_toto_statement_plan(record:dict[str,Any],predicate_type:str="https://dais.example/spec/universal-evidence/v0.1")->dict[str,Any]:
    _require_record(record)
    if not predicate_type.startswith("https://"): raise InteropError("predicate_type must be HTTPS")
    subjects=[]
    for artifact in record.get("artifacts",[]):
        digest=artifact.get("sha256","")
        if not SHA256.fullmatch(digest): raise InteropError("artifact sha256 required for in-toto subject mapping")
        subjects.append({"name":artifact["name"],"digest":{"sha256":digest.lower()}})
    return {
        "statement":{"_type":"https://in-toto.io/Statement/v1","subject":subjects,"predicateType":predicate_type,"predicate":{"evidence_id":record["evidence_id"],"evidence_type":record["evidence_type"],"result_status":record["result"]["status"]}},
        "signed":False,
        "signature_verified":False,
        "in_toto_conformance_verified":False,
    }

def slsa_build_provenance_readiness(record:dict[str,Any])->dict[str,Any]:
    _require_record(record)
    missing=[]
    # Universal Evidence v0.1 intentionally lacks SLSA builder/buildDefinition fields.
    for name in ("builder_identity","build_definition","resolved_dependencies"):
        missing.append(name)
    return {"standard":"SLSA-1.2","predicate_type":"https://slsa.dev/provenance/v1","ready":False,"missing_semantics":missing,"conversion_performed":False,"slsa_level_claim":None}

def otel_log_event_plan(record:dict[str,Any])->dict[str,Any]:
    _require_record(record)
    return {
        "timestamp":record["observed_at_utc"],
        "event_name":"dais.evidence."+str(record["evidence_type"]),
        "attributes":{
            "dais.evidence.id":record["evidence_id"],
            "dais.subject.type":record["subject"]["type"],
            "dais.operation.classification":record["operation"]["classification"],
            "dais.result.status":record["result"]["status"],
        },
        "body":None,
        "prompt_content":None,
        "message_content":None,
        "secret_values":None,
        "export_performed":False,
        "otel_semconv_stability_claim":False,
    }

def w3c_prov_plan(record:dict[str,Any])->dict[str,Any]:
    _require_record(record)
    eid=str(record["evidence_id"])
    return {
        "entity":{"id":"dais:subject:"+str(record["subject"]["id"]),"type":record["subject"]["type"]},
        "activity":{"id":"dais:activity:"+eid,"type":record["operation"]["name"],"time":record["observed_at_utc"]},
        "agent":{"id":"dais:agent:"+str(record["provenance"]["producer"])},
        "relations":["wasGeneratedBy","wasAssociatedWith"],
        "serialization_generated":False,
        "prov_constraints_validated":False,
    }

def external_composition_reference(record:dict[str,Any],kind:str,name:str,sha256:str)->dict[str,Any]:
    _require_record(record)
    if kind not in {"SPDX","CYCLONEDX"}: raise InteropError("kind must be SPDX or CYCLONEDX")
    if not SHA256.fullmatch(sha256): raise InteropError("sha256 required")
    return {"kind":kind,"name":name[:200],"sha256":sha256.lower(),"linked_evidence_id":record["evidence_id"],"document_parsed":False,"schema_validated":False,"signature_verified":False}
