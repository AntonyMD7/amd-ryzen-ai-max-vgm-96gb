#!/usr/bin/env python3
"""Defensive, metadata-only cybersecurity/privacy/trust planning primitives.

No network scan, exploit, credential test, message fetch, file redaction, metadata
mutation, financial transaction, or agent action is performed.
"""
from __future__ import annotations
import argparse, json, re
from typing import Any

class TrustError(ValueError): pass
SAFE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")
HEX64=re.compile(r"^[0-9a-fA-F]{64}$")
def _id(v:Any,n:str)->str:
    if not isinstance(v,str) or not SAFE.fullmatch(v): raise TrustError(f"{n} must be a bounded identifier")
    return v
def _bool(v:Any,n:str)->bool:
    if not isinstance(v,bool): raise TrustError(f"{n} must be boolean")
    return v
def _num(v:Any,n:str)->float:
    if isinstance(v,bool) or not isinstance(v,(int,float)): raise TrustError(f"{n} must be numeric")
    return float(v)
def _base(pid:str)->dict[str,Any]:
    return {"schema_version":"0.1","roadmap_id":pid,"execution":{"network_scanned":False,"credential_tested":False,"message_fetched":False,"file_modified":False,"transaction_performed":False,"agent_action_performed":False}}

def home_network(data):
    out=_base("P-121"); facts=data.get("facts")
    if not isinstance(facts,dict) or not all(isinstance(k,str) and isinstance(v,bool) for k,v in facts.items()): raise TrustError("facts must be boolean map")
    out.update({"facts":{_id(k,"fact"):v for k,v in facts.items()},"requirements":["owner-authorized inventory", "router/vendor documentation", "passive inventory first", "no Internet-wide scanning", "separate discovery from remediation"],"mode":"PASSIVE_PLAN_ONLY"}); return out

def log_explainer(data):
    out=_base("P-122"); event_type=_id(data.get("event_type"),"event_type"); severity=data.get("severity")
    if severity not in {"info","warning","error","critical"}: raise TrustError("bad severity")
    out.update({"event_type":event_type,"severity":severity,"requirements":["preserve raw log locally", "redact secrets/tokens", "retain timestamp/source", "distinguish observation from attribution"],"semantics":{"cause_attributed":False,"compromise_proven":False}}); return out

def dependency_scan(data):
    out=_base("P-123"); eco=_id(data.get("ecosystem"),"ecosystem"); lock=_bool(data.get("lockfile_present"),"lockfile_present")
    out.update({"ecosystem":eco,"lockfile_present":lock,"recommended_engines":["OSV-Scanner","GitHub Dependency Review where available"],"semantics":{"scan_run":False,"no_vulnerabilities_claimed":False}}); return out

def metadata_remove(data):
    out=_base("P-124"); file_type=_id(data.get("file_type"),"file_type"); backup=_bool(data.get("backup_ready"),"backup_ready")
    out.update({"file_type":file_type,"disposition":"REVIEWABLE_COPY_WORKFLOW" if backup else "BLOCKED_BACKUP_REQUIRED","recommended_engine":"ExifTool or format-specific reviewed tool","requirements":["work on copy", "preserve original", "verify output metadata", "verify visual/content integrity"],"semantics":{"metadata_removed":False,"all_sensitive_metadata_identified":False}}); return out

def redaction(data):
    out=_base("P-125"); kind=data.get("document_kind")
    if kind not in {"text","pdf","image","office"}: raise TrustError("unsupported document_kind")
    out.update({"document_kind":kind,"recommended_engine":"Presidio or format-specific local redaction pipeline","requirements":["local processing where feasible", "human review", "irreversible output verification", "preserve original", "detect hidden layers/metadata"],"semantics":{"redaction_performed":False,"all_sensitive_content_found":False}}); return out

def permission_audit(data):
    out=_base("P-126"); perms=data.get("permissions")
    if not isinstance(perms,list) or len(perms)>200: raise TrustError("permissions bounded list required")
    rows=[]
    for x in perms:
        if not isinstance(x,dict): raise TrustError("permission object required")
        rows.append({"permission":_id(x.get("permission"),"permission"),"required":_bool(x.get("required"),"required"),"sensitive":_bool(x.get("sensitive"),"sensitive")})
    out.update({"findings":[r for r in rows if r["sensitive"] or not r["required"]],"requirements":["least privilege", "document purpose", "review inherited permissions", "revoke only through separate approval"]}); return out

def suspicious_message(data):
    out=_base("P-127"); cues=data.get("cues")
    if not isinstance(cues,dict) or not all(isinstance(k,str) and isinstance(v,bool) for k,v in cues.items()): raise TrustError("cues boolean map required")
    cue_ids={_id(k,"cue"):v for k,v in cues.items()}; score=sum(cue_ids.values())
    out.update({"cue_count":score,"disposition":"REVIEW_SUSPICIOUS" if score else "NO_CUES_REPORTED_NOT_SAFE_CERTIFICATE","requirements":["verify sender via separate channel", "do not open attachments/links for analysis", "report using platform controls"],"semantics":{"message_read":False,"malice_proven":False,"message_safe_proven":False}}); return out

def scam_store(data):
    out=_base("P-128"); facts=data.get("facts")
    if not isinstance(facts,dict) or not all(isinstance(k,str) and isinstance(v,bool) for k,v in facts.items()): raise TrustError("facts boolean map required")
    flags=[_id(k,"fact") for k,v in facts.items() if v]
    out.update({"warning_flags":sorted(flags),"disposition":"CAUTION_REVIEW" if flags else "INSUFFICIENT_TO_CERTIFY_SAFE","requirements":["independent business/domain verification", "payment protection", "return/refund terms", "avoid urgency pressure"],"semantics":{"site_visited":False,"store_legitimacy_certified":False}}); return out

def invoice_anomaly(data):
    out=_base("P-129"); amount=_num(data.get("amount"),"amount"); baseline=_num(data.get("baseline_amount"),"baseline_amount"); bank_changed=_bool(data.get("bank_details_changed"),"bank_details_changed"); vendor_changed=_bool(data.get("vendor_identity_changed"),"vendor_identity_changed")
    ratio=None if baseline==0 else round((amount-baseline)/baseline,4); flags=[]
    if bank_changed: flags.append("BANK_DETAILS_CHANGED")
    if vendor_changed: flags.append("VENDOR_IDENTITY_CHANGED")
    if ratio is not None and abs(ratio)>0.5: flags.append("AMOUNT_DEVIATES_OVER_REFERENCE_THRESHOLD")
    out.update({"flags":flags,"relative_change":ratio,"note":"0.5 is a reference policy threshold, not a fraud probability.","requirements":["verify payment changes out-of-band", "do not auto-block/pay based on heuristic"],"semantics":{"fraud_proven":False}}); return out

def privacy_boundary(data):
    out=_base("P-130"); classification=data.get("data_class"); destination=data.get("destination")
    if classification not in {"public","internal","private","sensitive"} or destination not in {"local","trusted_cloud","public_cloud"}: raise TrustError("unsupported data class/destination")
    allowed=(classification=="public") or destination=="local" or (classification=="internal" and destination=="trusted_cloud")
    out.update({"data_class":classification,"destination":destination,"decision":"POLICY_PREFILTER_ALLOW" if allowed else "POLICY_PREFILTER_DENY_OR_REVIEW","semantics":{"data_sent":False,"legal_privacy_compliance_proven":False}}); return out

def provenance(data):
    out=_base("P-131"); source=_id(data.get("source_id"),"source_id"); artifact=data.get("artifact_sha256")
    if not isinstance(artifact,str) or not HEX64.fullmatch(artifact): raise TrustError("artifact_sha256 required")
    out.update({"source_id":source,"artifact_sha256":artifact.lower(),"requirements":["capture tool/model/version", "capture retrieval/source version", "timestamp", "transform lineage", "do not treat self-report as external attestation"],"semantics":{"provenance_verified_externally":False}}); return out

def claim_evidence(data):
    out=_base("P-132"); claim=_id(data.get("claim_id"),"claim_id"); evidence=data.get("evidence")
    if not isinstance(evidence,list) or len(evidence)>100: raise TrustError("evidence bounded list required")
    rows=[]
    for e in evidence:
        if not isinstance(e,dict): raise TrustError("evidence object required")
        rows.append({"evidence_id":_id(e.get("evidence_id"),"evidence_id"),"supports":_bool(e.get("supports"),"supports"),"independent":_bool(e.get("independent"),"independent")})
    out.update({"claim_id":claim,"support_count":sum(r["supports"] for r in rows),"independent_support_count":sum(r["supports"] and r["independent"] for r in rows),"status":"EVIDENCE_PRESENT_REVIEW_REQUIRED" if any(r["supports"] for r in rows) else "INSUFFICIENT_EVIDENCE","semantics":{"claim_proven":False}}); return out

def agent_permission(data):
    out=_base("P-133"); requested=data.get("requested_actions"); allowed=data.get("allowed_actions")
    if not isinstance(requested,list) or not isinstance(allowed,list) or len(requested)>100 or len(allowed)>100: raise TrustError("action lists required")
    req=[_id(x,"action") for x in requested]; allow=set(_id(x,"action") for x in allowed); denied=[x for x in req if x not in allow]
    out.update({"requested_actions":req,"denied_actions":denied,"decision":"DENY" if denied else "PREFILTER_ALLOW_REQUIRES_RUNTIME_AUTHORIZATION","requirements":["subject identity", "resource scope", "expiry", "approval", "audit", "revoke path"],"semantics":{"capability_lease_issued":False,"action_executed":False}}); return out

def evaluate(data):
    fn={"home_network":home_network,"log":log_explainer,"dependency":dependency_scan,"metadata":metadata_remove,"redaction":redaction,"permissions":permission_audit,"message":suspicious_message,"scam":scam_store,"invoice":invoice_anomaly,"privacy":privacy_boundary,"provenance":provenance,"claim":claim_evidence,"agent":agent_permission}.get(data.get("mode"))
    if fn is None: raise TrustError("unsupported mode")
    return fn(data)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("request");a=p.parse_args();
    with open(a.request,encoding="utf-8") as h:d=json.load(h)
    print(json.dumps(evaluate(d),indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
