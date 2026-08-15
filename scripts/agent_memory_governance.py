#!/usr/bin/env python3
"""Deny-by-default interoperability/memory/governance contracts for P-195..P-210."""
from __future__ import annotations
import hashlib,re
from typing import Any,Iterable
IDS=tuple(f"P-{n:03d}" for n in range(195,211))
class AgentGovernanceError(ValueError): pass

def _id(v:str,n:str)->str:
    v=v.strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{1,95}",v): raise AgentGovernanceError(f"invalid {n}")
    return v

def catalog()->list[dict[str,Any]]:
    names=["AI Agent Interoperability Standard","Common Agent Manifest Schema","Agent Task-Handoff Protocol","Portable Shared AI Memory Schema","Memory Provenance & Permission Framework","AI Approval-Gate Framework","AI Action Audit Ledger","AI Observability Dashboard","Model/Tool/Data-Source Provenance Viewer","AI Cost & Token Budget Tracker","Local-vs-Cloud Privacy Router","Prompt/Workflow Portability Framework","Universal RAG Toolkit","Personal Knowledge Vault Standard","Universal Voice Front End","Visual No-Code Agent Workflow Interface"]
    return [{"roadmap_id":r,"name":n,"status":"IN_PROGRESS_REFERENCE","action_authorized":False,"secret_values_allowed":False} for r,n in zip(IDS,names)]

def agent_manifest(agent_id:str,capabilities:Iterable[str],protocols:Iterable[str])->dict[str,Any]:
    return {"roadmap_ids":["P-195","P-196"],"agent_id":_id(agent_id,"agent_id"),"capabilities":sorted({_id(x,"capability") for x in capabilities}),"protocols":sorted({_id(x,"protocol") for x in protocols}),"protocol_candidates":["A2A","MCP"],"credentials":None,"execution_granted":False}

def handoff(task_id:str,source_agent:str,target_agent:str,artifact_hashes:Iterable[str])->dict[str,Any]:
    hashes=[]
    for x in artifact_hashes:
        if not re.fullmatch(r"[0-9a-f]{64}",x): raise AgentGovernanceError("invalid artifact hash")
        hashes.append(x)
    return {"roadmap_id":"P-197","task_id":_id(task_id,"task_id"),"source_agent":_id(source_agent,"source_agent"),"target_agent":_id(target_agent,"target_agent"),"artifact_hashes":hashes,"target_execution_authorized":False,"hidden_reasoning_required":False}

def memory_record(memory_id:str,content_hash:str,source_ref:str,classification:str,permissions:Iterable[str])->dict[str,Any]:
    if not re.fullmatch(r"[0-9a-f]{64}",content_hash): raise AgentGovernanceError("invalid content hash")
    if classification not in {"PUBLIC","PRIVATE","SENSITIVE","EPHEMERAL"}: raise AgentGovernanceError("invalid classification")
    return {"roadmap_ids":["P-198","P-199","P-208"],"memory_id":_id(memory_id,"memory_id"),"content_hash":content_hash,"source_ref":_id(source_ref,"source_ref"),"classification":classification,"permissions":sorted({_id(x,"permission") for x in permissions}),"content_embedded":False,"cloud_export_authorized":False,"provenance_model":"W3C-PROV-compatible-direction"}

def approval_gate(action_id:str,risk:str,approvals_required:int)->dict[str,Any]:
    if risk not in {"READ_ONLY","LOW","MEDIUM","HIGH"}: raise AgentGovernanceError("invalid risk")
    if not isinstance(approvals_required,int) or approvals_required<0: raise AgentGovernanceError("invalid approvals_required")
    return {"roadmap_id":"P-200","action_id":_id(action_id,"action_id"),"risk":risk,"approvals_required":approvals_required,"approvals_present":0,"authorized":risk=="READ_ONLY" and approvals_required==0,"mutation_performed":False}

def audit_event(event_id:str,actor:str,action:str,outcome:str,evidence_hash:str)->dict[str,Any]:
    if not re.fullmatch(r"[0-9a-f]{64}",evidence_hash): raise AgentGovernanceError("invalid evidence hash")
    return {"roadmap_ids":["P-201","P-202","P-203"],"event_id":_id(event_id,"event_id"),"actor":_id(actor,"actor"),"action":_id(action,"action"),"outcome":_id(outcome,"outcome"),"evidence_hash":evidence_hash,"secret_values":None,"prompt_content":None,"hidden_reasoning":None}

def budget_plan(currency:str,hard_cap:float,spent:float,tokens:int)->dict[str,Any]:
    if hard_cap<0 or spent<0 or tokens<0: raise AgentGovernanceError("budget values must be non-negative")
    return {"roadmap_id":"P-204","currency":currency[:3].upper(),"hard_cap":hard_cap,"spent":spent,"tokens":tokens,"remaining":max(0.0,hard_cap-spent),"provider_billing_verified":False,"purchase_authorized":False}

def privacy_route(data_class:str,local_available:bool,cloud_allowed:bool)->dict[str,Any]:
    if data_class not in {"PUBLIC","PRIVATE","SENSITIVE"}: raise AgentGovernanceError("invalid data class")
    route="LOCAL" if data_class in {"PRIVATE","SENSITIVE"} and local_available else "CLOUD" if data_class=="PUBLIC" and cloud_allowed else "BLOCKED"
    return {"roadmap_id":"P-205","data_class":data_class,"route":route,"data_transferred":False,"implicit_cloud_fallback":False}

def portable_workflow(workflow_id:str,steps:Iterable[dict[str,str]])->dict[str,Any]:
    normalized=[]
    for s in steps:
        if set(s)!={"id","kind","capability"}: raise AgentGovernanceError("invalid workflow step")
        normalized.append({k:_id(v,k) for k,v in s.items()})
    digest=hashlib.sha256(repr(normalized).encode()).hexdigest()
    return {"roadmap_ids":["P-206","P-210"],"workflow_id":_id(workflow_id,"workflow_id"),"steps":normalized,"digest":digest,"vendor_credentials":None,"executed":False}

def rag_manifest(corpus_id:str,index_hash:str,source_count:int)->dict[str,Any]:
    if not re.fullmatch(r"[0-9a-f]{64}",index_hash) or source_count<0: raise AgentGovernanceError("invalid RAG evidence")
    return {"roadmap_id":"P-207","corpus_id":_id(corpus_id,"corpus_id"),"index_hash":index_hash,"source_count":source_count,"retrieval_executed":False,"answer_generated":False,"citation_required":True}

def voice_frontend_manifest(languages:Iterable[str])->dict[str,Any]:
    return {"roadmap_id":"P-209","languages":sorted({str(x)[:16] for x in languages}),"microphone_access":False,"audio_recorded":False,"cloud_audio_transfer":False,"accessibility_review_required":True}
