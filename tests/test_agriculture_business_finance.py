from scripts.agriculture_business_finance import *

def test_catalog_covers_all_ids():
    rows=capability_catalog(); assert [x["roadmap_id"] for x in rows]==list(IDS); assert all(not x["mutation"] for x in rows)

def test_feed_is_arithmetic_only():
    r=feed_requirement(100,"120",7); assert r["feed_kg"]=="84.000"; assert r["husbandry_recommendation"] is False

def test_irrigation_identity():
    r=irrigation_volume(10,5); assert r["liters"]=="50.00"; assert r["agronomic_schedule_recommended"] is False

def test_inventory_delta_without_mutation():
    r=inventory_reconcile({"a":5},{"a":3,"b":2}); assert r["delta"]=={"a":-2,"b":2}; assert not r["inventory_mutated"]

def test_quote_is_not_tax_claim():
    r=quotation(100,10); assert r["total"]=="110.00"; assert not r["tax_compliance_claim"]; assert not r["invoice_issued"]

def test_break_even_refuses_nonpositive_margin():
    r=break_even(1000,5,5); assert r["units"] is None; assert not r["business_viability_claim"]

def test_budget_is_not_financial_advice():
    r=budget_snapshot(1000,[100,200]); assert r["balance"]=="700.00"; assert not r["investment_or_credit_advice"]

def test_payment_comparison_has_no_live_or_transaction_claim():
    r=payment_comparison([{"provider":"demo","fixed_fee":1,"percent_fee":2,"eligible":True}],100)
    assert r["options"][0]["estimated_fee"]=="3.00"; assert not r["live_terms_verified"]; assert not r["account_opened"]; assert not r["payment_executed"]

def test_procurement_does_not_order():
    r=procurement_compare([{"supplier":"A","unit_cost":2,"quantity":3}]); assert r["options"][0]["total"]=="6.00"; assert not r["supplier_selected"]; assert not r["order_placed"]

def test_farm_and_customer_are_plan_only():
    assert farm_record_manifest(["flock","feed"])["upstream_candidate"]=="farmOS"
    r=customer_followup_plan("quote sent"); assert not r["message_sent"]; assert not r["customer_data_collected"]
