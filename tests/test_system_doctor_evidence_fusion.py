from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "system_doctor_evidence_fusion.py"
SCHEMA = ROOT / "schemas" / "system-doctor-observation-case-v0.1.schema.json"
EXAMPLE = ROOT / "examples" / "system-doctor-evidence-fusion-synthetic-v0.1.json"

spec = importlib.util.spec_from_file_location("system_doctor_evidence_fusion", SCRIPT)
assert spec and spec.loader
fusion = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fusion)


def load_example() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_matches_schema_and_fails_honestly() -> None:
    case = load_example()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(case, schema)

    result = fusion.fuse_case(case)
    assert result["overall_state"] == "CONFLICT_REQUIRES_REVIEW"
    assert result["claims"] == {
        "root_cause_proven": False,
        "hardware_health_proven": False,
        "repair_authorized": False,
        "production_safe_to_infer": False,
        "roadmap_complete": False,
    }
    assert all(value is False for value in result["mutation"].values())
    assert len(result["result_sha256"]) == 64


def test_conflicting_sources_are_preserved_not_majority_voted() -> None:
    result = fusion.fuse_case(load_example())
    driver = next(item for item in result["domains"] if item["domain"] == "DRIVER")
    assert driver["state"] == "CONFLICT_REQUIRES_REVIEW"
    assert driver["conflict_preserved"] is True
    assert driver["observation_ids"] == ["obs-driver-01", "obs-driver-02"]
    assert "VERIFY_WITH_VENDOR_DIAGNOSTIC" in driver["verification_keys"]


def test_unknown_is_never_promoted_to_ok() -> None:
    case = load_example()
    case["observations"] = [case["observations"][-1]]
    result = fusion.fuse_case(case)
    assert result["overall_state"] == "INCOMPLETE_EVIDENCE"
    assert result["domains"][0]["state"] == "UNKNOWN"


def test_ok_plus_unknown_is_partial_unknown_not_ok() -> None:
    case = load_example()
    ok = copy.deepcopy(case["observations"][1])
    ok["domain"] = "CPU"
    ok["observation_id"] = "obs-cpu-ok"
    unknown = copy.deepcopy(case["observations"][-1])
    unknown["domain"] = "CPU"
    unknown["observation_id"] = "obs-cpu-unknown"
    case["observations"] = [ok, unknown]
    result = fusion.fuse_case(case)
    assert result["domains"][0]["state"] == "PARTIAL_UNKNOWN"
    assert result["overall_state"] == "INCOMPLETE_EVIDENCE"


def test_duplicate_observation_id_fails_closed() -> None:
    case = load_example()
    case["observations"][1]["observation_id"] = case["observations"][0]["observation_id"]
    with pytest.raises(fusion.FusionError, match="duplicate"):
        fusion.fuse_case(case)


def test_unprovenanced_digest_fails_closed() -> None:
    case = load_example()
    case["observations"][0]["source"]["evidence_sha256"] = "not-a-digest"
    with pytest.raises(fusion.FusionError, match="SHA-256"):
        fusion.fuse_case(case)


@pytest.mark.parametrize(
    "sensitive",
    [
        "person@example.com",
        "192.168.1.100",
        "C:/Users/Alice/private",
        "/home/alice/private",
        "https://alice:secret@example.com/tool",
        "github_pat_1234567890abcdef",
    ],
)
def test_sensitive_literals_are_refused(sensitive: str) -> None:
    case = load_example()
    case["observations"][0]["source"]["tool"] = sensitive
    with pytest.raises(fusion.FusionError, match="sensitive"):
        fusion.fuse_case(case)


def test_extra_fields_fail_closed() -> None:
    case = load_example()
    case["observations"][0]["raw_log"] = "not allowed"
    with pytest.raises(fusion.FusionError, match="unsupported keys"):
        fusion.fuse_case(case)


def test_engine_has_no_execution_or_network_primitives() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "subprocess",
        "os.system",
        "Popen(",
        "requests.",
        "urllib.request",
        "socket.",
        "shutil.which",
    )
    assert not any(token in source for token in forbidden)


def test_result_is_deterministic_for_identical_input() -> None:
    case = load_example()
    first = fusion.fuse_case(case)
    second = fusion.fuse_case(copy.deepcopy(case))
    assert first == second
