#!/usr/bin/env python3
"""Browser-based supporting accessibility probe for generated Accessible AI HTML.

This is automated supporting evidence only. It exercises a narrow keyboard path,
a 320-CSS-pixel reflow proxy, reduced-motion emulation, and document-language
semantics in a real browser. It cannot establish WCAG conformance, screen-reader
usability, disability-inclusive acceptance, or production readiness.

Requires Selenium in the execution environment; Selenium is intentionally not a
runtime dependency of the report renderer itself.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_probe(url: str, artifact: Path, output: Path, language: str, chromedriver: str) -> dict[str, Any]:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.keys import Keys
    except ImportError as exc:  # pragma: no cover - hosted workflow contract
        raise RuntimeError("selenium is required for browser supporting acceptance") from exc

    if language not in {"en", "es"}:
        raise ValueError("language must be en or es")
    if not url.startswith("http://127.0.0.1:"):
        raise ValueError("acceptance URL must be loopback-only")
    if not artifact.is_file():
        raise ValueError("artifact must exist")

    options = Options()
    for arg in ("--headless=new", "--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"):
        options.add_argument(arg)

    driver = webdriver.Chrome(service=Service(chromedriver), options=options)
    try:
        # WAI explains 320 CSS px as the horizontal geometry corresponding to
        # a 1280 CSS-pixel viewport at 400% zoom. This is a reflow proxy; it is
        # not relabeled as a manual 400%-zoom conformance test.
        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {"width": 320, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        driver.execute_cdp_cmd(
            "Emulation.setEmulatedMedia",
            {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
        )
        driver.get(url)

        metrics = driver.execute_script(
            """
            return {
              innerWidth: window.innerWidth,
              clientWidth: document.documentElement.clientWidth,
              documentScrollWidth: document.documentElement.scrollWidth,
              bodyScrollWidth: document.body.scrollWidth,
              lang: document.documentElement.lang,
              reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
            };
            """
        )
        reflow_pass = (
            metrics["innerWidth"] == 320
            and metrics["documentScrollWidth"] <= metrics["clientWidth"] + 1
            and metrics["bodyScrollWidth"] <= metrics["clientWidth"] + 1
        )
        if not reflow_pass:
            raise RuntimeError(f"320-CSS-pixel reflow proxy failed: {metrics}")
        if metrics["lang"] != language:
            raise RuntimeError(f"document language mismatch: {metrics['lang']!r} != {language!r}")
        if metrics["reducedMotion"] is not True:
            raise RuntimeError("prefers-reduced-motion emulation was not observed by the page")

        body = driver.find_element("tag name", "body")
        body.send_keys(Keys.TAB)
        first = driver.switch_to.active_element
        first_snapshot = driver.execute_script(
            """
            const el = document.activeElement;
            const r = el.getBoundingClientRect();
            return {tag: el.tagName, cls: el.className, text: el.textContent.trim(), x:r.x, y:r.y, width:r.width, height:r.height};
            """
        )
        if first_snapshot["tag"] != "A" or "skip" not in str(first_snapshot["cls"]).split():
            raise RuntimeError(f"first Tab did not reach skip link: {first_snapshot}")
        if first_snapshot["width"] <= 0 or first_snapshot["height"] <= 0 or first_snapshot["x"] < 0:
            raise RuntimeError(f"focused skip link is not visibly exposed: {first_snapshot}")

        first.send_keys(Keys.TAB)
        second = driver.switch_to.active_element
        second_tag = second.tag_name.upper()
        if second_tag != "SUMMARY":
            raise RuntimeError(f"second Tab did not reach engineering details summary: {second_tag}")

        second.send_keys(Keys.ENTER)
        details_open = driver.execute_script("return document.activeElement.closest('details').open")
        if details_open is not True:
            raise RuntimeError("Enter did not open the details element")

        second.send_keys(Keys.TAB)
        third = driver.switch_to.active_element
        if third.tag_name.upper() != "PRE":
            raise RuntimeError(f"Tab after opening details did not reach engineering evidence block: {third.tag_name}")

        browser_version = driver.capabilities.get("browserVersion", "unknown")
        record = {
            "schema_version": "0.1",
            "evidence_type": "accessible-ai-supporting-acceptance",
            "evidence_class": "AUTOMATED_TOOL",
            "subject": {
                "artifact_kind": "HTML",
                "artifact_ref": str(artifact).replace("\\", "/")[:240],
                "sha256": _sha256(artifact),
            },
            "standard_target": "WCAG_2_2_AA",
            "environment": {
                "os_family": "GitHub-hosted Ubuntu 24.04",
                "browser_family": f"Google Chrome {browser_version}"[:80],
                "assistive_technology": "not run",
                "tool_name": "Selenium WebDriver + Chrome DevTools emulation",
                "tool_version": "selenium-4.35.0",
            },
            "checks": {
                "keyboard_only": {
                    "status": "PASS",
                    "evidence_ref": str(output).replace("\\", "/")[:240],
                    "notes": "Automated browser path: Tab exposes skip link, next Tab reaches summary, Enter opens details, next Tab reaches focusable engineering block. Supporting evidence only; no human keyboard-usability claim.",
                },
                "screen_reader": {
                    "status": "NOT_RUN",
                    "evidence_ref": "",
                    "notes": "No screen reader or assistive-technology user session was run.",
                },
                "zoom_reflow_400": {
                    "status": "PASS",
                    "evidence_ref": str(output).replace("\\", "/")[:240],
                    "notes": "Automated 320-CSS-pixel horizontal reflow proxy passed with no document/body horizontal overflow. This geometry supports WAI reflow evaluation but is not relabeled as manual 400-percent user-agent zoom acceptance.",
                },
                "reduced_motion": {
                    "status": "PASS",
                    "evidence_ref": str(output).replace("\\", "/")[:240],
                    "notes": "Browser emulation confirmed prefers-reduced-motion: reduce is visible to the page; this does not prove every future animated component respects it.",
                },
                "language_semantics": {
                    "status": "PASS",
                    "evidence_ref": str(output).replace("\\", "/")[:240],
                    "notes": f"Browser observed html[lang]={language} on the exact generated artifact.",
                },
                "automated_rules": {
                    "status": "NOT_RUN",
                    "evidence_ref": "",
                    "notes": "axe rules are exercised by the separate pinned Accessible AI automated supporting acceptance workflow.",
                },
            },
            "privacy": {
                "participant_identity_stored": False,
                "participant_contact_stored": False,
                "credential_values_stored": False,
                "private_content_stored": False,
                "consent_recorded_when_people_involved": False,
            },
            "claims": {
                "wcag_conformance": False,
                "all_accessibility_issues_found": False,
                "real_user_acceptance": False,
                "production_ready": False,
            },
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return record
    finally:
        driver.quit()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lang", choices=["en", "es"], required=True)
    parser.add_argument(
        "--chromedriver",
        default=str(Path(os.environ.get("CHROMEWEBDRIVER", "")) / "chromedriver"),
    )
    args = parser.parse_args()
    run_probe(args.url, args.artifact, args.output, args.lang, args.chromedriver)
    print("BROWSER_ACCESSIBILITY_SUPPORTING_PROBE=PASS")
    print("WCAG_CONFORMANCE_CLAIMED=FALSE")
    print("REAL_USER_ACCEPTANCE_CLAIMED=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
