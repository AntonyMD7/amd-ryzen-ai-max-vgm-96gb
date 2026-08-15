from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator

ROOT = Path(__file__).parents[1]
SCHEMA = json.loads((ROOT / "schemas" / "local-ai-benchmark-v0.1.schema.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "examples" / "local-ai-benchmark-example.json").read_text(encoding="utf-8"))
MODULE_PATH = ROOT / "scripts" / "benchmark_compare.py"
spec = importlib.util.spec_from_file_location("benchmark_compare", MODULE_PATH)
assert spec and spec.loader
comparator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = comparator
spec.loader.exec_module(comparator)


def valid(record):
    Draft202012Validator(SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER).validate(record)


def test_sanitized_example_validates():
    valid(EXAMPLE)


def test_schema_rejects_privacy_leak_flag():
    record = copy.deepcopy(EXAMPLE)
    record["privacy"]["credentials_included"] = True
    errors = list(Draft202012Validator(SCHEMA).iter_errors(record))
    assert errors


def test_energy_not_measured_requires_null_value():
    record = copy.deepcopy(EXAMPLE)
    record["energy"]["energy_kwh"] = 0.1
    errors = list(Draft202012Validator(SCHEMA).iter_errors(record))
    assert errors


def test_comparator_refuses_mismatched_workload():
    other = copy.deepcopy(EXAMPLE)
    other["benchmark_id"] = "b"
    other["workload"]["context_size"] = 8192
    result = comparator.compare(EXAMPLE, other)
    assert result["performance_comparison"]["comparable"] is False
    assert any(x["field"] == "workload.context_size" for x in result["performance_comparison"]["mismatches"])
    assert result["performance_comparison"]["winner"] is None


def test_comparator_reports_higher_tokens_per_second_only_for_matching_records():
    other = copy.deepcopy(EXAMPLE)
    other["benchmark_id"] = "b"
    other["performance"]["tokens_per_second"] = 63.0
    result = comparator.compare(EXAMPLE, other)
    assert result["performance_comparison"]["comparable"] is True
    assert result["performance_comparison"]["winner"] == "b"
    assert result["performance_comparison"]["basis"] == "tokens_per_second"
    assert result["performance_comparison"]["relative_difference_percent"] == 50.0


def test_energy_evidence_class_is_not_upgraded_or_cross_compared():
    direct = copy.deepcopy(EXAMPLE)
    direct["benchmark_id"] = "direct"
    direct["energy"] = {
        "status": "DIRECT_METERED",
        "measurement_method": "external-meter-v1",
        "energy_kwh": 0.02,
        "method_version": "1",
        "evidence_ref": "sha256:example"
    }
    estimated = copy.deepcopy(direct)
    estimated["benchmark_id"] = "estimated"
    estimated["energy"]["status"] = "SOFTWARE_ESTIMATED"
    result = comparator.compare(direct, estimated)
    assert result["energy_comparison"]["directly_comparable"] is False
    assert result["energy_comparison"]["winner"] is None


def test_matching_energy_method_can_be_compared_without_changing_status():
    a = copy.deepcopy(EXAMPLE)
    b = copy.deepcopy(EXAMPLE)
    a["benchmark_id"] = "a"
    b["benchmark_id"] = "b"
    for record, value in ((a, 0.03), (b, 0.02)):
        record["energy"] = {
            "status": "SOFTWARE_ESTIMATED",
            "measurement_method": "CodeCarbon-example",
            "energy_kwh": value,
            "method_version": "example",
            "evidence_ref": None
        }
    result = comparator.compare(a, b)
    assert result["energy_comparison"]["directly_comparable"] is True
    assert result["energy_comparison"]["winner"] == "b"
    assert all(v is False for v in result["safety"].values())
