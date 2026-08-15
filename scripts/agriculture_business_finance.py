#!/usr/bin/env python3
"""Deterministic, non-transactional reference helpers for P-156..P-172."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable

IDS = tuple(f"P-{n:03d}" for n in range(156,173))

class PlanningError(ValueError): pass

def _d(v: Any, name: str) -> Decimal:
    try: x=Decimal(str(v))
    except (InvalidOperation, ValueError): raise PlanningError(f"invalid {name}")
    if not x.is_finite() or x < 0: raise PlanningError(f"{name} must be non-negative")
    return x

def _money(v: Decimal) -> str: return str(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def capability_catalog() -> list[dict[str, Any]]:
    names=["Small-Farm Management Toolkit","Poultry Management Calculator","Feed Calculator","Irrigation Planner","Farm Record System","Small-Business Inventory Tool","Invoice/Quotation Tool","Customer Follow-Up Assistant","Business Plan Validator","Pricing/Break-Even Calculator","Personal Budget Education Tool","Debt/Savings Planner","International Payment Stack Comparator","Merchant Eligibility Mapper","Payment Fee Calculator","Procurement Comparison Tool","Inventory Reconciliation Tool"]
    return [{"roadmap_id":rid,"name":name,"status":"IN_PROGRESS_REFERENCE","mutation":False,"financial_advice":False} for rid,name in zip(IDS,names)]

def feed_requirement(birds:int, grams_per_bird_day:Any, days:int)->dict[str,Any]:
    if not isinstance(birds,int) or birds<0 or not isinstance(days,int) or days<1: raise PlanningError("invalid birds/days")
    kg=_d(grams_per_bird_day,"grams_per_bird_day")*birds*days/Decimal(1000)
    return {"roadmap_ids":["P-157","P-158"],"feed_kg":str(kg.quantize(Decimal("0.001"))),"husbandry_recommendation":False,"inputs_are_user_supplied":True}

def irrigation_volume(area_m2:Any, depth_mm:Any)->dict[str,Any]:
    liters=_d(area_m2,"area_m2")*_d(depth_mm,"depth_mm")
    return {"roadmap_id":"P-159","liters":str(liters.quantize(Decimal("0.01"))),"agronomic_schedule_recommended":False}

def inventory_reconcile(expected:dict[str,int], counted:dict[str,int])->dict[str,Any]:
    if any(not isinstance(v,int) or v<0 for v in [*expected.values(),*counted.values()]): raise PlanningError("counts must be non-negative integers")
    keys=sorted(set(expected)|set(counted)); delta={k:counted.get(k,0)-expected.get(k,0) for k in keys}
    return {"roadmap_ids":["P-161","P-172"],"delta":delta,"inventory_mutated":False,"accounting_entry_created":False}

def quotation(subtotal:Any, tax_rate_percent:Any=0)->dict[str,Any]:
    sub=_d(subtotal,"subtotal"); rate=_d(tax_rate_percent,"tax_rate_percent")
    tax=sub*rate/100
    return {"roadmap_id":"P-162","subtotal":_money(sub),"tax":_money(tax),"total":_money(sub+tax),"tax_compliance_claim":False,"invoice_issued":False}

def break_even(fixed_cost:Any, unit_price:Any, unit_variable_cost:Any)->dict[str,Any]:
    fixed=_d(fixed_cost,"fixed_cost"); price=_d(unit_price,"unit_price"); variable=_d(unit_variable_cost,"unit_variable_cost")
    if price<=variable: return {"roadmap_ids":["P-164","P-165"],"status":"NO_POSITIVE_CONTRIBUTION_MARGIN","units":None,"business_viability_claim":False}
    units=(fixed/(price-variable)).quantize(Decimal("1"),rounding="ROUND_CEILING")
    return {"roadmap_ids":["P-164","P-165"],"status":"ARITHMETIC_ONLY","units":int(units),"business_viability_claim":False}

def budget_snapshot(income:Any, expenses:Iterable[Any])->dict[str,Any]:
    inc=_d(income,"income"); vals=[_d(x,"expense") for x in expenses]; total=sum(vals,Decimal(0));
    return {"roadmap_ids":["P-166","P-167"],"income":_money(inc),"expenses":_money(total),"balance":_money(inc-total),"investment_or_credit_advice":False}

def payment_comparison(options:Iterable[dict[str,Any]], amount:Any)->dict[str,Any]:
    amt=_d(amount,"amount"); rows=[]
    for o in options:
        if set(o)!={"provider","fixed_fee","percent_fee","eligible"}: raise PlanningError("invalid payment option fields")
        fee=_d(o["fixed_fee"],"fixed_fee")+amt*_d(o["percent_fee"],"percent_fee")/100
        rows.append({"provider":str(o["provider"])[:80],"eligible":bool(o["eligible"]),"estimated_fee":_money(fee)})
    return {"roadmap_ids":["P-168","P-169","P-170"],"amount":_money(amt),"options":rows,"live_terms_verified":False,"account_opened":False,"payment_executed":False}

def procurement_compare(items:Iterable[dict[str,Any]])->dict[str,Any]:
    rows=[]
    for x in items:
        if set(x)!={"supplier","unit_cost","quantity"}: raise PlanningError("invalid procurement fields")
        q=x["quantity"]
        if not isinstance(q,int) or q<1: raise PlanningError("quantity must be positive integer")
        rows.append({"supplier":str(x["supplier"])[:80],"quantity":q,"total":_money(_d(x["unit_cost"],"unit_cost")*q)})
    return {"roadmap_id":"P-171","options":rows,"supplier_selected":False,"order_placed":False}

def farm_record_manifest(record_types:Iterable[str])->dict[str,Any]:
    return {"roadmap_ids":["P-156","P-160"],"record_types":sorted({str(x)[:60] for x in record_types}),"personal_data":False,"sensor_or_device_write":False,"upstream_candidate":"farmOS"}

def customer_followup_plan(stage:str)->dict[str,Any]:
    return {"roadmap_id":"P-163","stage":str(stage)[:60],"message_sent":False,"customer_data_collected":False,"crm_upstream_candidates":["Odoo","CiviCRM"]}
