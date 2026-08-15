from __future__ import annotations

import json
from pathlib import Path
import sys

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from accessible_report import render_html
from system_doctor import collect


def _schema() -> dict:
    return json.loads((ROOT / "schemas" / "system-doctor-report-v0.1.schema.json").read_text(encoding="utf-8"))


def test_live_readonly_report_validates_schema() -> None:
    report = collect()
    jsonschema.Draft202012Validator(_schema()).validate(report)


def test_schema_rejects_privacy_overclaim() -> None:
    report = collect()
    report["privacy"]["hostname_collected"] = True
    errors = list(jsonschema.Draft202012Validator(_schema()).iter_errors(report))
    assert errors


def test_schema_rejects_mutation_smuggling() -> None:
    report = collect()
    report["mutation"]["configuration_changed"] = True
    errors = list(jsonschema.Draft202012Validator(_schema()).iter_errors(report))
    assert errors


def test_schema_rejects_unreviewed_extra_fields() -> None:
    report = collect()
    report["system"]["hostname"] = "must-not-appear"
    errors = list(jsonschema.Draft202012Validator(_schema()).iter_errors(report))
    assert errors


def test_accessible_render_uses_same_validated_record() -> None:
    report = collect()
    jsonschema.Draft202012Validator(_schema()).validate(report)
    en = render_html(report, "en")
    es = render_html(report, "es")
    assert '<html lang="en">' in en
    assert '<html lang="es">' in es
    assert "Read only" in en
    assert "Solo lectura" in es
    assert "prefers-reduced-motion" in en
    assert "prefers-reduced-motion" in es


def test_html_renderer_does_not_turn_unknown_status_into_ok() -> None:
    report = collect()
    report["checks"]["storage_headroom"] = {
        "status": "UNKNOWN",
        "summary": "Synthetic unknown state for acceptance testing.",
    }
    jsonschema.Draft202012Validator(_schema()).validate(report)
    html = render_html(report, "en")
    assert "Unknown" in html
    assert "Synthetic unknown state" in html
