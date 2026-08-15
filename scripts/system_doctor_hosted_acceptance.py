#!/usr/bin/env python3
"""Run privacy-safe hosted acceptance for Universal System Doctor.

This harness is deliberately read-only. It validates the System Doctor report,
renders the same sanitized truth in English and Spanish, and emits digest-bound
acceptance evidence for the exact hosted operating-system environment.

A PASS means the bounded collector/report contract worked on that hosted image.
It does not prove hardware diagnosis, vendor-driver coverage, production safety,
or real-user accessibility acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "system-doctor-report-v0.1.schema.json"

sys.path.insert(0, str(ROOT / "scripts"))
from accessible_report import render_html  # noqa: E402
from system_doctor import collect  # noqa: E402


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_acceptance(output_dir: Path, environment_class: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    report = collect()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(report)

    if report["collector"]["mode"] != "READ_ONLY":
        raise AssertionError("collector mode must remain READ_ONLY")
    if not all(value is False for value in report["privacy"].values()):
        raise AssertionError("privacy minimization contract failed")
    if not all(value is False for value in report["mutation"].values()):
        raise AssertionError("mutation contract failed")

    report_text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    rendered: dict[str, str] = {}
    for lang in ("en", "es"):
        html = render_html(report, lang)
        if f'<html lang="{lang}">' not in html:
            raise AssertionError(f"missing document language for {lang}")
        if 'href="#report"' not in html:
            raise AssertionError("skip-link contract missing")
        if "prefers-reduced-motion" not in html:
            raise AssertionError("reduced-motion contract missing")
        if '<main id="report" tabindex="-1">' not in html:
            raise AssertionError("main landmark/focus target contract missing")
        rendered[lang] = html

    (output_dir / "system-doctor-report.json").write_text(report_text, encoding="utf-8")
    (output_dir / "system-doctor-en.html").write_text(rendered["en"], encoding="utf-8")
    (output_dir / "system-doctor-es.html").write_text(rendered["es"], encoding="utf-8")

    acceptance = {
        "schema_version": "0.2",
        "evidence_type": "system-doctor-github-hosted-cross-platform-acceptance",
        "environment_class": environment_class,
        "observed_platform": {
            "os": report["system"]["os"],
            "release": report["system"]["release"],
            "architecture": report["system"]["architecture"],
            "python": report["system"]["python"],
        },
        "digests": {
            "report_sha256": sha256_text(report_text),
            "english_html_sha256": sha256_text(rendered["en"]),
            "spanish_html_sha256": sha256_text(rendered["es"]),
        },
        "checks": {
            "schema_validation": "PASS",
            "privacy_contract": "PASS",
            "read_only_contract": "PASS",
            "semantic_html_static_checks": "PASS",
        },
        "claims": {
            "hosted_os_contract_exercised": True,
            "physical_hardware_validated": False,
            "vendor_driver_diagnostics_validated": False,
            "hardware_failure_diagnosis_validated": False,
            "wcag_conformance": False,
            "real_user_assistive_technology_acceptance": False,
            "production_ready": False,
        },
    }
    (output_dir / "acceptance.json").write_text(
        json.dumps(acceptance, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return acceptance


def main() -> int:
    parser = argparse.ArgumentParser(description="Run hosted System Doctor acceptance")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--environment-class", required=True)
    args = parser.parse_args()
    acceptance = run_acceptance(args.output_dir, args.environment_class)
    print(f"SYSTEM_DOCTOR_HOSTED_ACCEPTANCE=PASS environment={acceptance['environment_class']}")
    print(f"OBSERVED_OS={acceptance['observed_platform']['os']}")
    print("PHYSICAL_HARDWARE_VALIDATED=FALSE")
    print("PRODUCTION_READY=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
