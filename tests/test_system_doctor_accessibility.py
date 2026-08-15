from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from accessible_report import render_html
from system_doctor import collect, render


def test_system_doctor_is_read_only_and_privacy_minimizing() -> None:
    report = collect()
    assert report["collector"]["mode"] == "READ_ONLY"
    assert all(value is False for value in report["mutation"].values())
    assert all(value is False for value in report["privacy"].values())


def test_three_audience_views_share_same_record() -> None:
    report = collect()
    beginner = render(report, "beginner")
    intermediate = render(report, "intermediate")
    engineer = render(report, "engineer")
    assert "No changes were made" in beginner
    assert "READ_ONLY" in intermediate
    assert '"collector"' in engineer


def test_accessible_html_has_semantic_navigation_and_focus_support() -> None:
    report = collect()
    html = render_html(report, "en")
    for required in [
        '<html lang="en">',
        'href="#report"',
        '<main id="report" tabindex="-1">',
        'aria-labelledby="safety-heading"',
        '<h1>',
        '<h2',
        '<details>',
        '<pre tabindex="0">',
        'prefers-reduced-motion',
    ]:
        assert required in html


def test_spanish_plain_language_path_exists() -> None:
    html = render_html(collect(), "es", include_engineer=False)
    assert '<html lang="es">' in html
    assert "Solo lectura" in html
    assert "Detalles de ingeniería" not in html


def test_renderer_escapes_machine_supplied_text() -> None:
    report = collect()
    report["limitations"] = ['<script>alert("x")</script>']
    html = render_html(report)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
