from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "scripts" / "evidence_validate.py"
spec = importlib.util.spec_from_file_location("evidence_validate", MODULE_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)
SCHEMA = json.loads((ROOT / "schemas" / "universal-evidence-v0.1.schema.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "examples" / "universal-evidence-readonly-example.json").read_text(encoding="utf-8"))


def test_existing_sanitized_example_passes_schema_validation():
    result = validator.validate_record(EXAMPLE, SCHEMA)
    assert result["status"] == "PASS"
    assert result["schema_errors"] == []
    assert all(value is False for value in result["safety"].values())


def test_invalid_mutation_fails_schema_gate():
    record = copy.deepcopy(EXAMPLE)
    record["operation"]["classification"] = "MUTATING"
    record["operation"]["authorization_ref"] = None
    record["rollback"]["required"] = False
    record["rollback"]["established"] = False
    record["safety"]["human_approval_required"] = False
    record["safety"]["approval_present"] = False
    result = validator.validate_record(record, SCHEMA)
    assert result["status"] == "FAIL"
    assert result["schema_errors"]


def test_artifact_hash_matches_without_execution(tmp_path):
    artifact = tmp_path / "evidence.txt"
    artifact.write_bytes(b"bounded evidence\n")
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{
        "name": "evidence.txt",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "media_type": "text/plain",
    }]
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "PASS"
    assert result["artifact_results"][0]["match"] is True
    assert result["safety"]["artifacts_executed"] is False


def test_artifact_hash_mismatch_fails(tmp_path):
    artifact = tmp_path / "evidence.txt"
    artifact.write_text("actual", encoding="utf-8")
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{"name": "evidence.txt", "sha256": "0" * 64, "media_type": "text/plain"}]
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert result["artifact_failures"][0]["reason"] == "sha256 mismatch"


def test_artifact_path_escape_is_rejected(tmp_path):
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{"name": "../secret.txt", "sha256": "0" * 64, "media_type": "text/plain"}]
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert "escapes" in result["artifact_failures"][0]["reason"]
