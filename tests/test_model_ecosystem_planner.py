import pytest

from scripts.model_ecosystem_planner import ModelEcosystemError, evaluate


def test_space_plan_accepts_only_public_or_synthetic_data():
    result = evaluate({"mode": "space_plan", "runtime": "gradio", "data_class": "public", "public_demo": True})
    assert result["roadmap_id"] == "P-064"
    assert set(result["actions"].values()) == {False}
    with pytest.raises(ModelEcosystemError):
        evaluate({"mode": "space_plan", "runtime": "gradio", "data_class": "private", "public_demo": True})


def test_model_comparison_refuses_ranking_when_dataset_version_differs():
    base = {"task": "classification", "dataset": "demo", "metric": "accuracy", "environment": "cpu", "higher_is_better": True}
    result = evaluate({"mode": "model_compare", "models": [
        {**base, "model_id": "a", "dataset_version": "1", "value": 0.8},
        {**base, "model_id": "b", "dataset_version": "2", "value": 0.9},
    ]})
    assert result["roadmap_id"] == "P-065"
    assert result["all_material_fields_comparable"] is False
    assert result["ranking"] == []


def test_model_comparison_ranks_only_comparable_records():
    base = {"task": "classification", "dataset": "demo", "dataset_version": "1", "metric": "accuracy", "environment": "cpu", "higher_is_better": True}
    result = evaluate({"mode": "model_compare", "models": [
        {**base, "model_id": "a", "value": 0.8},
        {**base, "model_id": "b", "value": 0.9},
    ]})
    assert result["ranking"] == ["b", "a"]
    assert result["semantics"]["ranking_is_statistical_significance"] is False


def test_model_card_and_safety_checklist_reports_missing_fields():
    result = evaluate({
        "mode": "model_card", "model_id": "org/model",
        "license_declared": True,
        "intended_use_documented": True,
        "limitations_documented": False,
        "training_data_provenance_documented": False,
        "evaluation_documented": True,
        "safety_risks_documented": False,
        "privacy_considered": True,
        "environmental_or_compute_context_considered": False,
    })
    assert result["roadmap_ids"] == ["P-066", "P-074"]
    assert "limitations_documented" in result["missing"]
    assert result["semantics"]["safety_certified"] is False


def test_dashboard_normalizes_metrics_but_does_not_verify_them():
    result = evaluate({"mode": "evaluation_dashboard", "records": [
        {"model_id": "org/model", "task": "qa", "dataset": "demo-v1", "metric": "f1", "value": 0.7}
    ]})
    assert result["roadmap_id"] == "P-067"
    assert result["record_count"] == 1
    assert result["semantics"]["values_verified_by_dashboard"] is False


def test_hardware_fit_is_arithmetic_only():
    result = evaluate({"mode": "hardware_fit", "available_memory_gb": 32, "estimated_required_memory_gb": 24})
    assert result["roadmap_id"] == "P-068"
    assert result["headroom_gb"] == 8.0
    assert result["semantics"]["guarantee"] is False


def test_multilingual_manifest_exposes_missing_language_coverage():
    result = evaluate({"mode": "multilingual_eval", "target_languages": ["en", "es", "pt"], "records": [
        {"language": "en", "metric": "accuracy", "value": 0.9},
        {"language": "es", "metric": "accuracy", "value": 0.8},
    ]})
    assert result["roadmap_id"] == "P-076"
    assert result["coverage_complete"] is False
    assert result["missing_languages"] == ["pt"]
    assert result["semantics"]["cross_language_fairness_proven"] is False


def test_duplicate_languages_and_free_text_identifiers_fail_closed():
    with pytest.raises(ModelEcosystemError):
        evaluate({"mode": "multilingual_eval", "target_languages": ["en", "en"], "records": []})
    with pytest.raises(ModelEcosystemError):
        evaluate({"mode": "evaluation_dashboard", "records": [
            {"model_id": "bad model id with spaces", "task": "qa", "dataset": "demo", "metric": "f1", "value": 1}
        ]})


def test_unknown_mode_fails_closed():
    with pytest.raises(ModelEcosystemError):
        evaluate({"mode": "deploy_model"})
