from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "hardware_external_observation_adapter.py"
LINUXHW = ROOT / "examples" / "hardware-external-linuxhw-normalized-v0.1.json"
LVFS = ROOT / "examples" / "hardware-external-lvfs-reference-only-v0.1.json"

spec = importlib.util.spec_from_file_location("hardware_external_observation_adapter", SCRIPT)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_reviewed_linuxhw_derived_fact_is_only_public_review_candidate() -> None:
    report, intake = adapter.adapt_external_observation(load(LINUXHW))
    assert report["observation"]["status"] == "COMMUNITY_REPORTED"
    assert report["observation"]["reproduction_runs"] == 0
    assert report["evidence"]["method"] == "COMMUNITY_REPORT"
    assert report["provenance"]["reporter_class"] == "COMMUNITY"
    assert report["provenance"]["review_status"] == "AUTOMATED_CHECKED"
    assert all(value is True for value in report["privacy"].values())
    assert all(value is False for value in report["claims"].values())
    assert intake["status"] == "ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED"
    assert intake["compatibility_verified_by_intake"] is False
    assert intake["safe_to_auto_apply"] is False


def test_external_failing_status_is_never_promoted_to_verified_failure() -> None:
    payload = load(LINUXHW)
    payload["observation"]["source_status"] = "COMMUNITY_FAILING"
    report, intake = adapter.adapt_external_observation(payload)
    assert report["observation"]["status"] == "COMMUNITY_REPORTED"
    assert report["observation"]["reproduction_runs"] == 0
    assert report["evidence"]["method"] == "COMMUNITY_REPORT"
    assert intake["compatibility_verified_by_intake"] is False
    assert intake["human_review_completed_by_intake"] is False


def test_external_unknown_remains_unknown() -> None:
    payload = load(LINUXHW)
    payload["observation"]["source_status"] = "UNKNOWN"
    report, _ = adapter.adapt_external_observation(payload)
    assert report["observation"]["status"] == "UNKNOWN"


def test_linuxhw_reference_only_rights_are_blocked() -> None:
    payload = load(LINUXHW)
    payload["source"]["rights_status"] = "REFERENCE_ONLY"
    with pytest.raises(adapter.ExternalSourceBlocked, match="rights are reviewed"):
        adapter.adapt_external_observation(payload)


def test_linuxhw_unreviewed_privacy_is_blocked() -> None:
    payload = load(LINUXHW)
    payload["source"]["privacy_status"] = "NOT_REVIEWED"
    with pytest.raises(adapter.ExternalSourceBlocked, match="identifiers are removed"):
        adapter.adapt_external_observation(payload)


def test_linuxhw_wrong_license_is_rejected() -> None:
    payload = load(LINUXHW)
    payload["source"]["license_expression"] = "UNRESOLVED_REFERENCE_ONLY"
    with pytest.raises(adapter.ExternalSourceError):
        adapter.adapt_external_observation(payload)


def test_linuxhw_noncanonical_url_is_rejected() -> None:
    payload = load(LINUXHW)
    payload["source"]["dataset_url"] = "https://example.com/linuxhw/HWInfo"
    with pytest.raises(adapter.ExternalSourceError, match="canonical"):
        adapter.adapt_external_observation(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("configuration", [{"key": "device.serial", "value": "ABC123"}]),
        ("configuration", [{"key": "network.mode", "value": "192.168.1.25"}]),
        ("configuration", [{"key": "contact.note", "value": "person@example.com"}]),
        ("configuration", [{"key": "path.note", "value": "/home/alice/private/file"}]),
    ],
)
def test_sensitive_or_unique_identifiers_are_rejected(field: str, value: object) -> None:
    payload = load(LINUXHW)
    payload[field] = value
    with pytest.raises(adapter.ExternalSourceError, match="privacy prefilter"):
        adapter.adapt_external_observation(payload)


def test_lvfs_reference_remains_blocked_until_rights_and_field_review() -> None:
    with pytest.raises(adapter.ExternalSourceBlocked, match="reference-only"):
        adapter.adapt_external_observation(load(LVFS))


def test_lvfs_cannot_self_declare_import_rights_in_v01() -> None:
    payload = load(LVFS)
    payload["source"]["license_expression"] = "CC-BY-4.0"
    payload["source"]["rights_status"] = "DERIVED_FACTS_PUBLICATION_REVIEWED"
    payload["source"]["privacy_status"] = "NORMALIZED_IDENTIFIERS_REMOVED"
    with pytest.raises(adapter.ExternalSourceError):
        adapter.adapt_external_observation(payload)


def test_output_is_deterministic_for_identical_normalized_input() -> None:
    payload = load(LINUXHW)
    first, first_intake = adapter.adapt_external_observation(payload)
    second, second_intake = adapter.adapt_external_observation(copy.deepcopy(payload))
    assert first == second
    assert first_intake == second_intake


def test_adapter_has_no_network_or_execution_primitives() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "urllib.request",
        "urlopen(",
        "requests.",
        "httpx.",
        "subprocess",
        "os.system",
        "Popen(",
    )
    assert not any(token in source for token in forbidden)
