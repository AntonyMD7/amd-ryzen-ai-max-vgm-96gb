import pytest

from scripts.hardware_upgrade_advisor import AdvisorError, advise


def test_ram_respects_declared_vendor_max():
    result = advise({"kind": "ram", "installed_gb": 16, "target_gb": 128, "vendor_max_gb": 64, "free_slots": 2})
    assert result["roadmap_id"] == "P-011"
    assert result["state"] == "OUTSIDE_DECLARED_VENDOR_MAX"
    assert result["safety"]["purchase_recommended"] is False


def test_ram_requires_slot_review_when_no_free_slots():
    result = advise({"kind": "ram", "installed_gb": 16, "target_gb": 32, "vendor_max_gb": 64, "free_slots": 0})
    assert result["state"] == "REVIEW_SLOT_TOPOLOGY"


def test_gpu_never_calls_basic_fit_a_guarantee():
    result = advise({"kind": "gpu", "candidate_required_psu_w": 650, "system_psu_w": 750, "power_connectors_verified": True, "physical_fit_verified": True})
    assert result["roadmap_id"] == "P-012"
    assert result["state"] == "BASIC_PREFILTER_PASSES"
    assert set(result["semantics"].values()) == {False}


def test_gpu_surfaces_power_and_fit_uncertainty():
    result = advise({"kind": "gpu", "candidate_required_psu_w": 850, "system_psu_w": 650, "power_connectors_verified": False, "physical_fit_verified": False})
    assert result["state"] == "REVIEW_REQUIRED"
    assert len(result["review_reasons"]) == 3


def test_storage_requires_all_three_basic_facts():
    result = advise({"kind": "storage", "interface_match": True, "form_factor_match": False, "slot_available": True})
    assert result["roadmap_id"] == "P-013"
    assert result["state"] == "REVIEW_REQUIRED"
    assert "FORM_FACTOR_MISMATCH_OR_UNVERIFIED" in result["review_reasons"]


def test_thermal_compares_only_against_caller_supplied_limits():
    result = advise({"kind": "thermal_power", "observed_temp_c": 91, "vendor_temp_limit_c": 90, "observed_power_w": 110, "declared_power_limit_w": 120})
    assert result["roadmap_id"] == "P-014"
    assert result["state"] == "REVIEW_REQUIRED"
    assert result["review_reasons"] == ["OBSERVED_TEMP_ABOVE_CALLER_SUPPLIED_VENDOR_LIMIT"]


def test_benchmark_refuses_ranking_when_material_fields_differ():
    result = advise({"kind": "benchmark", "candidate_value": 110, "baseline_value": 100, "higher_is_better": True, "same_workload": True, "same_software": False, "same_settings": True})
    assert result["roadmap_id"] == "P-015"
    assert result["state"] == "REFUSE_RANKING_MATERIAL_FIELDS_DIFFER"
    assert result["relative_change_percent"] is None


def test_benchmark_directionality_for_latency_style_metric():
    result = advise({"kind": "benchmark", "candidate_value": 80, "baseline_value": 100, "higher_is_better": False, "same_workload": True, "same_software": True, "same_settings": True})
    assert result["relative_change_percent"] == -20.0
    assert result["directional_improvement_percent"] == 20.0
    assert result["safety"]["benchmark_executed"] is False


def test_invalid_boolean_or_negative_numeric_inputs_fail_closed():
    with pytest.raises(AdvisorError):
        advise({"kind": "gpu", "candidate_required_psu_w": 650, "system_psu_w": 750, "power_connectors_verified": "yes", "physical_fit_verified": True})
    with pytest.raises(AdvisorError):
        advise({"kind": "ram", "installed_gb": -1, "target_gb": 32, "vendor_max_gb": 64, "free_slots": 2})


def test_unknown_kind_fails_closed():
    with pytest.raises(AdvisorError):
        advise({"kind": "buy_whatever_is_fastest"})
