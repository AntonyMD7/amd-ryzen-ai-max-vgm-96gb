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


def artifact_record(tmp_path: Path, *, name: str = "evidence.txt", payload: bytes = b"bounded evidence\n"):
    artifact = tmp_path / name
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_bytes(payload)
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{
        "name": name,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "media_type": "text/plain",
    }]
    return artifact, record


def test_existing_sanitized_example_passes_schema_validation():
    result = validator.validate_record(EXAMPLE, SCHEMA)
    assert result["status"] == "PASS"
    assert result["schema_errors"] == []
    assert result["validator"]["version"] == "0.2.0"
    assert len(result["record_sha256"]) == 64
    assert len(result["schema_sha256"]) == 64
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
    assert result["counts"]["schema_errors"] == len(result["schema_errors"])


def test_artifact_hash_matches_without_execution(tmp_path):
    artifact, record = artifact_record(tmp_path)
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "PASS"
    assert result["artifact_results"][0]["match"] is True
    assert result["artifact_results"][0]["size_bytes"] == artifact.stat().st_size
    assert result["counts"]["verified_artifacts"] == 1
    assert result["safety"]["artifacts_executed"] is False


def test_artifact_hash_mismatch_fails(tmp_path):
    artifact, record = artifact_record(tmp_path)
    record["artifacts"][0]["sha256"] = "0" * 64
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert result["artifact_failures"][0]["reason"] == "sha256 mismatch"
    assert artifact.read_bytes() == b"bounded evidence\n"


def test_artifact_path_escape_is_rejected(tmp_path):
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{"name": "../secret.txt", "sha256": "0" * 64, "media_type": "text/plain"}]
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert "escapes" in result["artifact_failures"][0]["reason"]


def test_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / "outside-evidence.txt"
    outside.write_text("outside", encoding="utf-8")
    link = tmp_path / "linked.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        return
    record = copy.deepcopy(EXAMPLE)
    record["artifacts"] = [{
        "name": "linked.txt",
        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
        "media_type": "text/plain",
    }]
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert "escapes" in result["artifact_failures"][0]["reason"]


def test_duplicate_artifact_names_fail_closed(tmp_path):
    _, record = artifact_record(tmp_path)
    record["artifacts"].append(copy.deepcopy(record["artifacts"][0]))
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert result["status"] == "FAIL"
    assert result["counts"]["artifact_failures"] == 1
    assert "duplicate" in result["artifact_failures"][0]["reason"]


def test_artifact_count_bound_fails_closed_without_hashing(tmp_path):
    _, record = artifact_record(tmp_path)
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path, max_artifacts=0)
    assert result["status"] == "FAIL"
    assert result["artifact_results"] == []
    assert "exceeds" in result["artifact_failures"][0]["reason"]


def test_artifact_size_bound_fails_closed(tmp_path):
    _, record = artifact_record(tmp_path, payload=b"12345")
    result = validator.validate_record(record, SCHEMA, artifact_root=tmp_path, max_artifact_bytes=4)
    assert result["status"] == "FAIL"
    assert result["artifact_results"] == []
    assert "size" in result["artifact_failures"][0]["reason"]


def test_validation_is_input_immutable(tmp_path):
    _, record = artifact_record(tmp_path)
    before = copy.deepcopy(record)
    validator.validate_record(record, SCHEMA, artifact_root=tmp_path)
    assert record == before


def test_atomic_result_file_round_trip(tmp_path):
    output = tmp_path / "nested" / "report.json"
    result = validator.validate_record(EXAMPLE, SCHEMA)
    validator.write_json_atomic(output, result)
    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded == result
    assert not list(output.parent.glob(f".{output.name}.*"))
