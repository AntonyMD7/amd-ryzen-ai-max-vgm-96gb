#!/usr/bin/env python3
"""Provenance-first, no-fetch/no-execute reference contracts for P-183..P-194."""
from __future__ import annotations
import hashlib,re
from typing import Any,Iterable
from urllib.parse import urlparse
IDS=tuple(f"P-{n:03d}" for n in range(183,195))
class ResearchError(ValueError): pass

def _t(v:str,n:str,l:int=240)->str:
    if not isinstance(v,str): raise ResearchError(f"{n} must be text")
    v=" ".join(v.strip().split())
    if not v or len(v)>l or any(c in v for c in "\r\n\x00"): raise ResearchError(f"invalid {n}")
    return v

def _u(v:str)->str:
    p=urlparse(_t(v,"url",500))
    if p.scheme!="https" or not p.netloc or p.username or p.password: raise ResearchError("URL must be credential-free HTTPS")
    return v

def catalog()->list[dict[str,Any]]:
    names=["Scientific Paper Comparison Tool","Reproducibility Checklist Assistant","Citation/Evidence Extraction Tool","Research Environment Capture Tool","Dataset Provenance Framework","Experiment Manifest Standard","Open Data Browser","Public API Wrapper Generator","Weather-Risk Dashboard","Water-Quality Visualization Tool","Energy Calculator","Household/Server Energy Efficiency Tool"]
    return [{"roadmap_id":r,"name":n,"status":"IN_PROGRESS_REFERENCE","network":False,"execution":False,"scientific_conclusion":False} for r,n in zip(IDS,names)]

def paper_manifest(doi:str,title:str,source_url:str)->dict[str,Any]:
    if not re.fullmatch(r"10\.\d{4,9}/\S+",doi,re.I): raise ResearchError("invalid DOI")
    return {"roadmap_ids":["P-183","P-185"],"doi":doi.lower(),"title":_t(title,"title"),"source_url":_u(source_url),"metadata_authority":"Crossref candidate","full_text_copied":False,"claims_extracted":False,"quality_ranked":False}

def reproducibility_manifest(artifacts:Iterable[dict[str,str]])->dict[str,Any]:
    out=[]
    for a in artifacts:
        if set(a)!={"path_label","sha256","role"}: raise ResearchError("invalid artifact fields")
        if not re.fullmatch(r"[0-9a-f]{64}",a["sha256"]): raise ResearchError("invalid sha256")
        out.append({"path_label":_t(a["path_label"],"path_label",120),"sha256":a["sha256"],"role":_t(a["role"],"role",80)})
    return {"roadmap_ids":["P-184","P-186","P-188"],"artifacts":out,"environment_captured":False,"experiment_executed":False,"reproducibility_proven":False,"upstream_candidates":["ReproZip","RO-Crate"]}

def dataset_provenance(dataset_id:str,source_url:str,license_name:str,sha256:str)->dict[str,Any]:
    if not re.fullmatch(r"[0-9a-f]{64}",sha256): raise ResearchError("invalid sha256")
    return {"roadmap_id":"P-187","dataset_id":_t(dataset_id,"dataset_id",120),"source_url":_u(source_url),"license":_t(license_name,"license",120),"sha256":sha256,"data_read":False,"rights_verified":False,"upstream_candidates":["RO-Crate","Frictionless Data Package"]}

def open_data_plan(portal_url:str,query:str)->dict[str,Any]:
    return {"roadmap_id":"P-189","portal_url":_u(portal_url),"query":_t(query,"query",200),"request_performed":False,"dataset_selected":False,"upstream_candidates":["CKAN","Frictionless"]}

def api_wrapper_manifest(name:str,base_url:str,operations:Iterable[str])->dict[str,Any]:
    ops=sorted({_t(x,"operation",80) for x in operations})
    return {"roadmap_id":"P-190","name":_t(name,"name",80),"base_url":_u(base_url),"operations":ops,"credentials_accepted":False,"code_generated":False,"network_request_performed":False}

def environmental_dataset(kind:str,source_url:str,observed_at:str,fields:Iterable[str])->dict[str,Any]:
    mapping={"weather":"P-191","water":"P-192"}
    if kind not in mapping: raise ResearchError("kind must be weather or water")
    return {"roadmap_id":mapping[kind],"source_url":_u(source_url),"observed_at":_t(observed_at,"observed_at",64),"fields":sorted({_t(x,"field",80) for x in fields}),"data_fetched":False,"risk_or_safety_determination":False,"visualization_generated":False}

def energy_estimate(power_watts:Any,hours:Any,rate_per_kwh:Any|None=None)->dict[str,Any]:
    try: p=float(power_watts); h=float(hours)
    except (TypeError,ValueError): raise ResearchError("power/hours must be numeric")
    if p<0 or h<0: raise ResearchError("power/hours must be non-negative")
    kwh=p*h/1000; result={"roadmap_ids":["P-193","P-194"],"kwh":round(kwh,6),"measured_energy":False,"efficiency_certification":False}
    if rate_per_kwh is not None:
        try: r=float(rate_per_kwh)
        except (TypeError,ValueError): raise ResearchError("rate must be numeric")
        if r<0: raise ResearchError("rate must be non-negative")
        result["estimated_cost"]=round(kwh*r,6); result["live_tariff_verified"]=False
    return result
