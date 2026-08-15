#!/usr/bin/env python3
"""Guardrailed health/medical education and operational planning primitives.

This module is not a diagnostic, prescribing, dosing, triage, interaction or
emergency-treatment engine. It accepts metadata/checklist facts and returns
source/evidence requirements without patient-specific clinical decisions.
"""
from __future__ import annotations
import argparse,json,re
from typing import Any
class HealthError(ValueError):pass
SAFE=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$");HEX64=re.compile(r"^[0-9a-fA-F]{64}$")
def _id(v:Any,n:str)->str:
 if not isinstance(v,str) or not SAFE.fullmatch(v):raise HealthError(f"{n} must be a bounded identifier")
 return v
def _bool(v:Any,n:str)->bool:
 if not isinstance(v,bool):raise HealthError(f"{n} must be boolean")
 return v
def _base(pid:str)->dict[str,Any]:return {"schema_version":"0.1","roadmap_id":pid,"clinical_boundary":{"diagnosis_made":False,"treatment_recommended":False,"dose_calculated":False,"interaction_conclusion_made":False,"triage_disposition_made":False}}

def anatomy(data):
 o=_base("P-134");o.update({"structure_id":_id(data.get("structure_id"),"structure_id"),"requirements":["authoritative educational anatomy source","state model/source limitations","no patient-image inference","accessible labels"],"semantics":{"clinical_anatomy_for_patient_proven":False}});return o

def medication_mechanism(data):
 o=_base("P-135");o.update({"drug_concept_id":_id(data.get("drug_concept_id"),"drug_concept_id"),"source_plan":["normalize identity with current NLM RxNorm where applicable","retrieve current FDA-approved/DailyMed labeling where applicable","cite section/date/version","separate labeled facts from explanatory synthesis"],"semantics":{"mechanism_generated":False,"label_currentness_verified_by_this_tool":False}});return o

def calculator_framework(data):
 o=_base("P-136");formula=_id(data.get("formula_id"),"formula_id");version=_id(data.get("formula_version"),"formula_version");validated=_bool(data.get("external_validation_documented"),"external_validation_documented")
 o.update({"formula_id":formula,"formula_version":version,"disposition":"IMPLEMENTATION_REVIEW_ELIGIBLE" if validated else "BLOCKED_VALIDATION_REQUIRED","requirements":["authoritative formula source","population/contraindication scope","unit tests with published examples","input units explicit","rounding rule","independent clinical review"],"execution":{"calculation_performed":False}});return o

def evidence_navigation(data):
 o=_base("P-137");o.update({"topic_id":_id(data.get("topic_id"),"topic_id"),"source_plan":["NCBI PubMed via current E-utilities","guideline/agency primary sources as appropriate","retain PMID/DOI/source date","separate retrieval from appraisal"],"execution":{"literature_search_run":False},"semantics":{"evidence_quality_appraised":False}});return o

def equipment_checklist(data):
 o=_base("P-138");items=data.get("items")
 if not isinstance(items,list) or len(items)>500:raise HealthError("items bounded list required")
 rows=[]
 for x in items:
  if not isinstance(x,dict):raise HealthError("item object required")
  rows.append({"item_id":_id(x.get("item_id"),"item_id"),"present":_bool(x.get("present"),"present"),"in_date":_bool(x.get("in_date"),"in_date"),"functional_check_documented":_bool(x.get("functional_check_documented"),"functional_check_documented")})
 o.update({"gaps":[r for r in rows if not(r["present"] and r["in_date"] and r["functional_check_documented"])],"semantics":{"equipment_function_test_executed":False}});return o

def inventory(data):
 o=_base("P-139");stock=data.get("stock")
 if not isinstance(stock,list) or len(stock)>1000:raise HealthError("stock bounded list required")
 rows=[]
 for x in stock:
  if not isinstance(x,dict):raise HealthError("stock object required")
  q=x.get("quantity");minq=x.get("minimum")
  if isinstance(q,bool) or not isinstance(q,int) or q<0 or isinstance(minq,bool) or not isinstance(minq,int) or minq<0:raise HealthError("quantities non-negative integers")
  rows.append({"item_id":_id(x.get("item_id"),"item_id"),"quantity":q,"minimum":minq,"reorder_review":q<minq})
 o.update({"stock":rows,"privacy":{"patient_data_required":False},"execution":{"order_placed":False,"inventory_modified":False}});return o

def handover(data):
 o=_base("P-140");sections=data.get("sections")
 required={"situation","background","assessment","recommendation","pending_tasks","allergies_medications_reviewed"}
 if not isinstance(sections,dict) or not all(isinstance(k,str) and isinstance(v,bool) for k,v in sections.items()):raise HealthError("sections boolean map required")
 present={_id(k,"section") for k,v in sections.items() if v};o.update({"missing_sections":sorted(required-present),"privacy":{"patient_content_accepted":False,"public_artifact_safe_by_default":True},"semantics":{"handover_clinically_complete":False}});return o

def emergency_workflow(data):
 o=_base("P-141");protocol=_id(data.get("protocol_id"),"protocol_id");version=_id(data.get("protocol_version"),"protocol_version")
 o.update({"protocol_id":protocol,"protocol_version":version,"requirements":["locally approved current protocol","role/scope mapping","call-for-help/escalation path","timestamped checklist","deviation recording","post-event review"],"execution":{"protocol_step_executed":False},"semantics":{"patient_assessment_performed":False}});return o

def public_health(data):
 o=_base("P-142");source=_id(data.get("source_id"),"source_id");date=_id(data.get("source_date"),"source_date")
 o.update({"source_id":source,"source_date":date,"requirements":["public-health authority source","jurisdiction","update date","archive superseded guidance","plain-language summary with source access"],"execution":{"guidance_fetched":False}});return o

def literacy(data):
 o=_base("P-143");language=_id(data.get("language"),"language")
 o.update({"language":language,"principles":["AHRQ health-literacy universal precautions","plain language","teach-back support","qualified interpreter path","preserve medication warnings/dates/numbers"],"execution":{"patient_text_transformed":False},"semantics":{"understanding_verified":False}});return o

def medication_list(data):
 o=_base("P-144");count=data.get("medication_count")
 if isinstance(count,bool) or not isinstance(count,int) or count<0:raise HealthError("medication_count non-negative integer")
 o.update({"medication_count":count,"fields":["normalized drug identifier","display name","strength/form as documented","directions as documented","source","last reconciled"],"requirements":["include prescription/OTC/supplements when user chooses","reconcile with clinician/pharmacist","do not infer missing dose"],"execution":{"medications_read":False,"list_modified":False}});return o

def interaction_info(data):
 o=_base("P-145");drug_count=data.get("drug_count")
 if isinstance(drug_count,bool) or not isinstance(drug_count,int) or drug_count<2:raise HealthError("drug_count must be >=2")
 o.update({"drug_count":drug_count,"source_plan":["normalize medicines using current RxNorm","retrieve current FDA-approved/DailyMed labeling sections as applicable","surface source date/version","pharmacist/clinician verification for decisions"],"warning":"This reference layer does not determine whether two medicines interact and must not be used to clear a combination as safe.","execution":{"drug_data_fetched":False}});return o

def offline_reference(data):
 o=_base("P-146");source=_id(data.get("source_id"),"source_id");version=_id(data.get("version"),"version");digest=data.get("sha256")
 if not isinstance(digest,str) or not HEX64.fullmatch(digest):raise HealthError("sha256 required")
 o.update({"source_id":source,"version":version,"sha256":digest.lower(),"requirements":["authoritative licensed source","visible update date","expiration/review date","integrity check","replacement workflow","emergency disclaimer"],"execution":{"content_downloaded":False,"reference_served":False}});return o

def preparedness(data):
 o=_base("P-147");profile=data.get("profile")
 if profile not in {"general","child_family","pregnancy_infant","chronic_condition_review"}:raise HealthError("unsupported profile")
 o.update({"profile":profile,"source_plan":"current public-health/emergency-management authority checklist","requirements":["water/food/shelter/communications basics","medication/equipment continuity plan with clinician/pharmacy as needed","documents/contact list","expiry/function checks","local hazard adaptation"],"execution":{"personal_plan_created":False,"medical_advice_generated":False}});return o

def evaluate(d):
 fn={"anatomy":anatomy,"mechanism":medication_mechanism,"calculator":calculator_framework,"evidence":evidence_navigation,"equipment":equipment_checklist,"inventory":inventory,"handover":handover,"emergency_workflow":emergency_workflow,"public_health":public_health,"literacy":literacy,"med_list":medication_list,"interaction":interaction_info,"offline_reference":offline_reference,"preparedness":preparedness}.get(d.get("mode"))
 if fn is None:raise HealthError("unsupported mode")
 return fn(d)
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("request");a=p.parse_args();
 with open(a.request,encoding="utf-8") as h:d=json.load(h)
 print(json.dumps(evaluate(d),indent=2,sort_keys=True));return 0
if __name__=="__main__":raise SystemExit(main())
