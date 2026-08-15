from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from system_doctor_hosted_acceptance import run_acceptance


def test_hosted_acceptance_emits_digest_bound_read_only_evidence(tmp_path):
    result = run_acceptance(tmp_path, "UNIT_TEST_HOST")

    assert result["environment_class"] == "UNIT_TEST_HOST"
    assert result["checks"] == {
        "schema_validation": "PASS",
        "privacy_contract": "PASS",
        "read_only_contract": "PASS",
        "semantic_html_static_checks": "PASS",
    }
    assert result["claims"]["hosted_os_contract_exercised"] is True
    assert result["claims"]["physical_hardware_validated"] is False
    assert result["claims"]["vendor_driver_diagnostics_validated"] is False
    assert result["claims"]["hardware_failure_diagnosis_validated"] is False
    assert result["claims"]["wcag_conformance"] is False
    assert result["claims"]["real_user_assistive_technology_acceptance"] is False
    assert result["claims"]["production_ready"] is False

    for name in (
        "system-doctor-report.json",
        "system-doctor-en.html",
        "system-doctor-es.html",
        "acceptance.json",
    ):
        assert (tmp_path / name).is_file()

    public_report = json.loads((tmp_path / "system-doctor-report.json").read_text(encoding="utf-8"))
    assert public_report["collector"]["mode"] == "READ_ONLY"
    assert all(value is False for value in public_report["privacy"].values())
    assert all(value is False for value in public_report["mutation"].values())


def test_hosted_acceptance_preserves_observed_platform_without_identity(tmp_path):
    result = run_acceptance(tmp_path, "UNIT_TEST_HOST")
    observed = result["observed_platform"]
    assert observed["os"]
    assert observed["architecture"]

    serialized = (tmp_path / "acceptance.json").read_text(encoding="utf-8").lower()
    assert "username" not in serialized
    assert "hostname" not in serialized
    assert "network_addresses" not in serialized
    assert "credentials" not in serialized
