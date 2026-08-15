#!/usr/bin/env python3
"""Source-pinned, non-authoritative reference helpers for P-173..P-182."""
from __future__ import annotations
import re
from typing import Any, Iterable
from urllib.parse import urlparse
IDS=tuple(f"P-{n:03d}" for n in range(173,183))
class PublicInfoError(ValueError): pass

def _text(v:str,name:str,limit:int=240)->str:
    if not isinstance(v,str): raise PublicInfoError(f"{name} must be text")
    v=" ".join(v.strip().split())
    if not v or len(v)>limit or any(c in v for c in "\r\n\x00"): raise PublicInfoError(f"invalid {name}")
    return v

def _url(v:str)->str:
    p=urlparse(_text(v,"source_url",500))
    if p.scheme!="https" or not p.netloc or p.username or p.password: raise PublicInfoError("source must be credential-free HTTPS")
    return v

def catalog()->list[dict[str,Any]]:
    names=["Travel Document Organizer","Visa Checklist Assistant","Accessible Itinerary Planner","Government Form Plain-Language Assistant","Government Document Checklist Generator","Legal-Information Document Explainer","Deadline/Evidence Organizer","Legislation Plain-Language Explorer","Public Budget/Data Explorer","Civic Open-Data Visualization Toolkit"]
    return [{"roadmap_id":rid,"name":name,"status":"IN_PROGRESS_REFERENCE","official_determination":False,"external_action":False} for rid,name in zip(IDS,names)]

def document_manifest(kind:str,fields:Iterable[str])->dict[str,Any]:
    return {"roadmap_ids":["P-173","P-177","P-179"],"kind":_text(kind,"kind",60),"fields":sorted({_text(x,"field",80) for x in fields}),"document_values_collected":False,"deadline_verified":False,"document_submitted":False}

def visa_checklist(country:str,source_url:str,source_date:str,items:Iterable[str])->dict[str,Any]:
    if not re.fullmatch(r"20\d\d-\d\d-\d\d",source_date): raise PublicInfoError("source_date must be YYYY-MM-DD")
    return {"roadmap_id":"P-174","country":_text(country,"country",80),"source_url":_url(source_url),"source_date":source_date,"items":[_text(x,"item",160) for x in items],"eligibility_determined":False,"visa_advice":False,"application_submitted":False}

def itinerary_plan(stops:Iterable[dict[str,str]])->dict[str,Any]:
    out=[]
    for s in stops:
        if set(s)!={"place","date","accessibility_note"}: raise PublicInfoError("invalid itinerary fields")
        out.append({k:_text(v,k,160) for k,v in s.items()})
    return {"roadmap_id":"P-175","stops":out,"booking_performed":False,"live_availability_verified":False,"accessibility_needs_require_user_confirmation":True}

def plain_language_plan(document_type:str,source_url:str,language:str="en")->dict[str,Any]:
    return {"roadmap_ids":["P-176","P-178","P-180"],"document_type":_text(document_type,"document_type",100),"source_url":_url(source_url),"language":_text(language,"language",16),"source_text_rewritten":False,"legal_advice":False,"official_interpretation":False,"meaning_preservation_review_required":True}

def open_data_manifest(portal_url:str,dataset_id:str,license_name:str,updated_at:str|None=None)->dict[str,Any]:
    return {"roadmap_ids":["P-181","P-182"],"portal_url":_url(portal_url),"dataset_id":_text(dataset_id,"dataset_id",120),"license":_text(license_name,"license",120),"updated_at":updated_at,"dataset_downloaded":False,"figures_verified":False,"visualization_generated":False,"upstream_candidates":["CKAN","Plotly/Dash"]}
