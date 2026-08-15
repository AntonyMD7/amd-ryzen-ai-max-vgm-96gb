#!/usr/bin/env python3
"""Evidence-first, non-executing reference contracts for P-211..P-227."""
from __future__ import annotations
import hashlib,re
from typing import Any,Iterable
IDS=tuple(f"P-{n:03d}" for n in range(211,228))
class InfrastructureError(ValueError): pass

def _id(v:str,n:str)->str:
    v=v.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{1,95}",v): raise InfrastructureError(f"invalid {n}")
    return v

def _hash(v:str)->str:
    if not re.fullmatch(r"[0-9a-f]{64}",v): raise InfrastructureError("invalid sha256")
    return v

def catalog()->list[dict[str,Any]]:
    names=["SafeFix Framework","Universal Evidence Schema","Evidence-First Automation Library","Recovery-First Mutation Framework","Universal Troubleshooting Framework","Device Attestation Toolkit","Fleet Health Snapshot Tool","Home-Lab Management Dashboard","Cross-Platform Multi-Device Orchestrator","Hardware Compatibility Commons","Community Evidence Repository","Public Troubleshooting Knowledge Graph","Open Compatibility Database","Open Technical Evidence Standard","Reference Implementation Library","Reproducible Architecture Starter Kits","Problem → Public Solution Framework"]
    return [{"roadmap_id":r,"name":n,"status":"IN_PROGRESS_REFERENCE","mutation":False,"secret_values":False,"completion_claim":False} for r,n in zip(IDS,names)]

def safefix_plan(operation_id:str,mode:str,recovery_established:bool,approval_present:bool)->dict[str,Any]:
    if mode not in {"READ_ONLY","MUTATING"}: raise InfrastructureError("invalid mode")
    authorized=mode=="READ_ONLY" or (recovery_established and approval_present)
    return {"roadmap_ids":["P-211","P-213","P-214","P-215"],"operation_id":_id(operation_id,"operation_id"),"mode":mode,"recovery_established":recovery_established,"approval_present":approval_present,"authorized":authorized,"executed":False,"lifecycle":["DISCOVER","VERIFY","PREFLIGHT","APPROVE","MUTATE","ATTEST","PUBLISH_EVIDENCE"]}

def evidence_envelope(evidence_id:str,subject_id:str,subject_hash:str,source_standard_refs:Iterable[str])->dict[str,Any]:
    return {"roadmap_ids":["P-212","P-224"],"evidence_id":_id(evidence_id,"evidence_id"),"subject_id":_id(subject_id,"subject_id"),"subject_sha256":_hash(subject_hash),"standard_refs":sorted({_id(x,"standard ref") for x in source_standard_refs}),"interoperability_candidates":["in-toto-attestation","slsa-v1.2","opentelemetry"],"signature_verified":False,"event_truth_proven":False}

def device_attestation(node_id:str,platform:str,facts_hash:str)->dict[str,Any]:
    return {"roadmap_ids":["P-216","P-217"],"node_id":_id(node_id,"node_id"),"platform":_id(platform,"platform"),"facts_sha256":_hash(facts_hash),"probe_executed":False,"unique_identifiers_collected":False,"state":"PLAN_ONLY","upstream_candidates":["osquery","hw-probe"]}

def fleet_snapshot(nodes:Iterable[dict[str,str]])->dict[str,Any]:
    normalized=[]
    for n in nodes:
        if set(n)!={"node_id","evidence_hash","status"}: raise InfrastructureError("invalid node fields")
        normalized.append({"node_id":_id(n["node_id"],"node_id"),"evidence_hash":_hash(n["evidence_hash"]),"status":_id(n["status"],"status")})
    return {"roadmap_ids":["P-217","P-218","P-219"],"nodes":normalized,"remote_command_executed":False,"dashboard_served":False,"orchestration_performed":False}

def compatibility_record(hardware_id:str,software_id:str,observed_behavior:str,evidence_hash:str)->dict[str,Any]:
    if observed_behavior not in {"PASS","FAIL","PARTIAL","UNKNOWN"}: raise InfrastructureError("invalid observed_behavior")
    return {"roadmap_ids":["P-220","P-223"],"hardware_id":_id(hardware_id,"hardware_id"),"software_id":_id(software_id,"software_id"),"observed_behavior":observed_behavior,"evidence_hash":_hash(evidence_hash),"compatibility_guarantee":False,"community_submission_published":False}

def community_evidence_record(record_id:str,evidence_hash:str,redaction_reviewed:bool)->dict[str,Any]:
    return {"roadmap_ids":["P-221","P-224"],"record_id":_id(record_id,"record_id"),"evidence_hash":_hash(evidence_hash),"redaction_reviewed":bool(redaction_reviewed),"contains_secret_values":False,"published":False}

def troubleshooting_graph_case(case_id:str,symptoms:Iterable[str],checks:Iterable[str],evidence_hash:str)->dict[str,Any]:
    return {"roadmap_id":"P-222","case_id":_id(case_id,"case_id"),"symptoms":sorted({_id(x,"symptom") for x in symptoms}),"checks":sorted({_id(x,"check") for x in checks}),"evidence_hash":_hash(evidence_hash),"root_cause_claim":False,"graph_written":False}

def reference_implementation(component_id:str,source_hash:str,tests_present:bool)->dict[str,Any]:
    return {"roadmap_id":"P-225","component_id":_id(component_id,"component_id"),"source_hash":_hash(source_hash),"tests_present":bool(tests_present),"released":False,"production_ready_claim":False}

def architecture_kit(kit_id:str,components:Iterable[str],manifest_hash:str)->dict[str,Any]:
    return {"roadmap_id":"P-226","kit_id":_id(kit_id,"kit_id"),"components":sorted({_id(x,"component") for x in components}),"manifest_hash":_hash(manifest_hash),"infrastructure_deployed":False,"reproducibility_proven":False}

def problem_solution_intake(problem_id:str,problem:str,existing_solution_search_done:bool,safety_review_done:bool)->dict[str,Any]:
    p=" ".join(str(problem).strip().split())
    if not p or len(p)>500: raise InfrastructureError("invalid problem")
    return {"roadmap_id":"P-227","problem_id":_id(problem_id,"problem_id"),"problem":p,"existing_solution_search_done":bool(existing_solution_search_done),"safety_review_done":bool(safety_review_done),"build_authorized":bool(existing_solution_search_done and safety_review_done),"repository_created":False,"solution_complete":False}
