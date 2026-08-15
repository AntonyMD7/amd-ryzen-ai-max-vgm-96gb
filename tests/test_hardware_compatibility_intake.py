from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from hardware_compatibility_intake import IntakeError, validate_public_report


def _fixture() -> dict:
    return json.loads((ROOT / "examples" / "hardware-compatibility-synthetic-v0.2.json").read_text(encoding="utf-8"))


def test_synthetic_conformance_fixture_is_public_review_eligible_not_verified() -> None:
    result = validate_public_report(_fixture())
    assert result["status"] == "ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED"
    assert result["schema_validation"] == "PASS"
    assert result["privacy_prefilter"] == "PASS"
    assert result["compatibility_verified_by_intake"] is False
    assert result["human_review_completed_by_intake"] is False
    assert result["safe_to_auto_apply"] is False
    assert len(result["report_sha256"]) == 64


def test_schema_refuses_raw_log_or_unreviewed_fields() -> None:
    report = _fixture()
    report["raw_logs"] = "this field should never become a public dump surface"
    with pytest.raises(IntakeError, match="schema"):
        validate_public_report(report)


def test_secret_and_identity_patterns_fail_closed() -> None:
    cases = [
        "token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
        "contact person@example.com",
        "adapter 00:11:22:33:44:55",
        "tailnet 100.65.97.31",
        "lan 192.168.1.44",
        "/home/alice/private/file.txt",
        r"C:\Users\Alice\Desktop\report.txt",
    ]
    for index, text in enumerate(cases):
        report = _fixture()
        report["report_id"] = f"HCC-SYNTHETIC-{index:04d}"
        report["observation"]["summary"] = text
        with pytest.raises(IntakeError, match="sensitive"):
            validate_public_report(report)


def test_unique_identifier_configuration_keys_are_rejected() -> None:
    for key in ["hostname", "device_id", "serial_number", "mac_address", "ip_address"]:
        report = _fixture()
        report["configuration"] = [{"key": key, "value": "redacted-looking-value"}]
        with pytest.raises(IntakeError, match="unique-or-network-identifier"):
            validate_public_report(report)


def _verified_report() -> dict:
    report = _fixture()
    report["report_id"] = "HCC-VERIFIED-0001"
    report["observation"] = {
        "status": "VERIFIED_WORKING",
        "observed_at_utc": "2026-08-15T00:00:00Z",
        "summary": "The bounded test completed with the expected result on this exact software and hardware record.",
        "reproduction_runs": 2,
    }
    report["evidence"] = {
        "method": "REPRODUCIBLE_TEST",
        "source_commit": "0123456789abcdef0123456789abcdef01234567",
        "artifact_hashes": ["a" * 64],
        "source_urls": ["https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb"],
        "reproduction_steps": ["Run the bounded public test twice and compare the expected result."],
    }
    report["provenance"] = {
        "reporter_class": "OWNER_TEST",
        "submitted_at_utc": "2026-08-15T00:00:00Z",
        "review_status": "HUMAN_REVIEWED",
    }
    report["limitations"] = ["The result applies only to the exact recorded versions and configuration."]
    return report


def test_verified_status_requires_reproducible_hashed_evidence() -> None:
    report = _verified_report()
    report["evidence"]["artifact_hashes"] = []
    report["observation"]["reproduction_runs"] = 0
    with pytest.raises(IntakeError, match="verified-status"):
        validate_public_report(report)


def test_vendor_documentation_or_community_report_alone_cannot_be_verified_outcome() -> None:
    for method in ["VENDOR_DOCUMENTATION", "COMMUNITY_REPORT"]:
        report = _verified_report()
        report["evidence"]["method"] = method
        with pytest.raises(IntakeError):
            validate_public_report(report)


def test_valid_verified_shaped_report_still_not_verified_by_intake_itself() -> None:
    result = validate_public_report(_verified_report())
    assert result["status"] == "ELIGIBLE_FOR_PUBLIC_REVIEW_NOT_VERIFIED"
    assert result["compatibility_verified_by_intake"] is False
    assert result["human_review_completed_by_intake"] is False


def test_ci_synthetic_report_cannot_claim_real_hardware_outcome() -> None:
    report = _verified_report()
    report["provenance"]["reporter_class"] = "CI_SYNTHETIC"
    with pytest.raises(IntakeError, match="ci-synthetic"):
        validate_public_report(report)


def test_privacy_booleans_cannot_be_downgraded() -> None:
    for field in _fixture()["privacy"]:
        report = _fixture()
        report["privacy"][field] = False
        with pytest.raises(IntakeError, match="schema"):
            validate_public_report(report)


def test_intake_contains_no_uploader_or_mutation_executor() -> None:
    source = (ROOT / "scripts" / "hardware_compatibility_intake.py").read_text(encoding="utf-8")
    for forbidden in ["import requests", "urllib", "subprocess", "os.system(", "shell=True", "git push", "fwupdmgr update"]:
        assert forbidden not in source
