#!/usr/bin/env python3
"""Offline planning/interpretation primitives for public model ecosystems.

No model, dataset, Space, Hub API, network service or accelerator is contacted.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class ModelEcosystemError(ValueError):
    pass


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ModelEcosystemError(f"{name} must be a bounded identifier")
    return value


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise ModelEcosystemError(f"{name} must be boolean")
    return value


def space_plan(data: dict[str, Any]) -> dict[str, Any]:
    runtime = data.get("runtime")
    data_class = data.get("data_class")
    if runtime not in {"gradio", "static"}:
        raise ModelEcosystemError("runtime must be gradio or static")
    if data_class not in {"synthetic", "public"}:
        raise ModelEcosystemError("reference public Space accepts only synthetic/public data classes")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-064",
        "surface": "HUGGING_FACE_SPACE_PLAN",
        "runtime": runtime,
        "data_class": data_class,
        "public_demo": _bool(data.get("public_demo"), "public_demo"),
        "requirements": [
            "pin dependencies",
            "document model/data provenance",
            "declare hardware/runtime assumptions",
            "add accessibility and safety notes",
            "avoid embedding credentials in repository files",
        ],
        "actions": {"space_created": False, "network_contacted": False, "model_loaded": False},
    }


def compare_models(data: dict[str, Any]) -> dict[str, Any]:
    models = data.get("models")
    if not isinstance(models, list) or len(models) < 2 or len(models) > 50:
        raise ModelEcosystemError("models must contain 2..50 records")
    keys = ("task", "dataset", "dataset_version", "metric", "environment")
    reference = None
    rows = []
    for item in models:
        if not isinstance(item, dict):
            raise ModelEcosystemError("model records must be objects")
        model_id = _id(item.get("model_id"), "model_id")
        signature = tuple(_id(item.get(key), key) for key in keys)
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ModelEcosystemError("metric value must be numeric")
        higher = _bool(item.get("higher_is_better"), "higher_is_better")
        if reference is None:
            reference = (signature, higher)
        comparable = reference == (signature, higher)
        rows.append({"model_id": model_id, "value": float(value), "comparable_to_reference": comparable})
    all_comparable = all(row["comparable_to_reference"] for row in rows)
    ranking = []
    if all_comparable:
        ranking = [row["model_id"] for row in sorted(rows, key=lambda r: r["value"], reverse=reference[1])]
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-065",
        "all_material_fields_comparable": all_comparable,
        "ranking": ranking,
        "records": rows,
        "semantics": {"ranking_is_statistical_significance": False, "model_executed": False},
    }


def model_card_checklist(data: dict[str, Any]) -> dict[str, Any]:
    model_id = _id(data.get("model_id"), "model_id")
    checks = {}
    for key in (
        "license_declared",
        "intended_use_documented",
        "limitations_documented",
        "training_data_provenance_documented",
        "evaluation_documented",
        "safety_risks_documented",
        "privacy_considered",
        "environmental_or_compute_context_considered",
    ):
        checks[key] = _bool(data.get(key), key)
    missing = [key for key, value in checks.items() if not value]
    return {
        "schema_version": "0.1",
        "roadmap_ids": ["P-066", "P-074"],
        "model_id": model_id,
        "checks": checks,
        "missing": missing,
        "status": "DOCUMENTATION_GAPS" if missing else "CHECKLIST_COMPLETE_REVIEW_STILL_REQUIRED",
        "semantics": {"model_card_published": False, "safety_certified": False, "legal_review_complete": False},
    }


def evaluation_dashboard(data: dict[str, Any]) -> dict[str, Any]:
    records = data.get("records")
    if not isinstance(records, list) or not records or len(records) > 500:
        raise ModelEcosystemError("records must contain 1..500 metric records")
    normalized = []
    for item in records:
        if not isinstance(item, dict):
            raise ModelEcosystemError("record must be an object")
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ModelEcosystemError("value must be numeric")
        normalized.append({
            "model_id": _id(item.get("model_id"), "model_id"),
            "task": _id(item.get("task"), "task"),
            "dataset": _id(item.get("dataset"), "dataset"),
            "metric": _id(item.get("metric"), "metric"),
            "value": float(value),
        })
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-067",
        "record_count": len(normalized),
        "records": normalized,
        "semantics": {"dashboard_executes_evaluation": False, "values_verified_by_dashboard": False},
    }


def hardware_fit_bridge(data: dict[str, Any]) -> dict[str, Any]:
    available = data.get("available_memory_gb")
    estimated = data.get("estimated_required_memory_gb")
    if isinstance(available, bool) or not isinstance(available, (int, float)) or available <= 0:
        raise ModelEcosystemError("available_memory_gb must be > 0")
    if isinstance(estimated, bool) or not isinstance(estimated, (int, float)) or estimated <= 0:
        raise ModelEcosystemError("estimated_required_memory_gb must be > 0")
    headroom = round(float(available) - float(estimated), 4)
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-068",
        "state": "ARITHMETIC_PREFILTER_PASSES" if headroom >= 0 else "ESTIMATE_EXCEEDS_AVAILABLE_MEMORY",
        "headroom_gb": headroom,
        "authoritative_next_checks": ["exact model artifact", "backend-specific estimator", "real pinned workload"],
        "semantics": {"guarantee": False, "model_loaded": False, "performance_predicted": False},
    }


def multilingual_eval_manifest(data: dict[str, Any]) -> dict[str, Any]:
    target_languages = data.get("target_languages")
    records = data.get("records")
    if not isinstance(target_languages, list) or not target_languages or len(target_languages) > 100:
        raise ModelEcosystemError("target_languages must contain 1..100 language identifiers")
    languages = [_id(value, "language") for value in target_languages]
    if len(set(languages)) != len(languages):
        raise ModelEcosystemError("target_languages must be unique")
    if not isinstance(records, list) or len(records) > 1000:
        raise ModelEcosystemError("records must be a bounded list")
    covered = set()
    normalized = []
    for item in records:
        if not isinstance(item, dict):
            raise ModelEcosystemError("record must be an object")
        language = _id(item.get("language"), "language")
        metric = _id(item.get("metric"), "metric")
        value = item.get("value")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ModelEcosystemError("value must be numeric")
        covered.add(language)
        normalized.append({"language": language, "metric": metric, "value": float(value)})
    missing = sorted(set(languages) - covered)
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-076",
        "target_languages": languages,
        "covered_languages": sorted(covered & set(languages)),
        "missing_languages": missing,
        "coverage_complete": not missing,
        "records": normalized,
        "semantics": {"cross_language_fairness_proven": False, "benchmark_executed": False},
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    functions = {
        "space_plan": space_plan,
        "model_compare": compare_models,
        "model_card": model_card_checklist,
        "evaluation_dashboard": evaluation_dashboard,
        "hardware_fit": hardware_fit_bridge,
        "multilingual_eval": multilingual_eval_manifest,
    }
    fn = functions.get(mode)
    if fn is None:
        raise ModelEcosystemError("unsupported mode")
    return fn(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(evaluate(request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
