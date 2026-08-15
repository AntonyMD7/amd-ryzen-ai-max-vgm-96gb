#!/usr/bin/env python3
"""Accessible AI v0.1 report renderer.

Turns a machine-readable diagnostic record into dependency-free semantic HTML.
This is a reference presentation layer, not a WCAG-conformance claim.
"""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from typing import Any

TEXT = {
    "en": {
        "title": "System check report",
        "skip": "Skip to report",
        "mode": "Safety mode",
        "readonly": "Read only — no repairs or configuration changes were made.",
        "checks": "Checks",
        "limitations": "Limitations",
        "details": "Engineering details",
        "ok": "Looks okay",
        "notice": "Worth reviewing",
        "review": "Needs review",
        "unknown": "Unknown",
    },
    "es": {
        "title": "Informe de revisión del sistema",
        "skip": "Ir al informe",
        "mode": "Modo de seguridad",
        "readonly": "Solo lectura — no se realizaron reparaciones ni cambios de configuración.",
        "checks": "Comprobaciones",
        "limitations": "Limitaciones",
        "details": "Detalles de ingeniería",
        "ok": "Parece correcto",
        "notice": "Conviene revisar",
        "review": "Necesita revisión",
        "unknown": "Desconocido",
    },
}

STATUS_LABEL = {"OK": "ok", "NOTICE": "notice", "REVIEW": "review", "UNKNOWN": "unknown"}


def localized_status(status: str, lang: str) -> str:
    key = STATUS_LABEL.get(status, "unknown")
    return TEXT[lang][key]


def render_html(report: dict[str, Any], lang: str = "en", include_engineer: bool = True) -> str:
    if lang not in TEXT:
        raise ValueError(f"unsupported language: {lang}")
    t = TEXT[lang]
    checks = report.get("checks", {})
    items: list[str] = []
    for name, check in sorted(checks.items()):
        status = str(check.get("status", "UNKNOWN"))
        summary = check.get("summary") or check.get("version") or ""
        items.append(
            '<li class="check">'
            f'<strong>{escape(name.replace("_", " ").title())}</strong>: '
            f'<span>{escape(localized_status(status, lang))}</span>'
            + (f'<p>{escape(str(summary))}</p>' if summary else "")
            + "</li>"
        )

    limitations = "".join(f"<li>{escape(str(item))}</li>" for item in report.get("limitations", []))
    engineering = ""
    if include_engineer:
        raw = escape(json.dumps(report, indent=2, sort_keys=True))
        engineering = f'<details><summary>{escape(t["details"])}</summary><pre tabindex="0">{raw}</pre></details>'

    return f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(t["title"])}</title>
<style>
:root {{ font-family: system-ui, sans-serif; font-size: 112.5%; line-height: 1.55; }}
body {{ max-width: 70rem; margin: 0 auto; padding: 1rem; }}
a:focus, button:focus, summary:focus, pre:focus {{ outline: 3px solid currentColor; outline-offset: 3px; }}
.skip {{ position: absolute; left: -10000px; }}
.skip:focus {{ position: static; display: inline-block; padding: .5rem; }}
.status {{ border: 2px solid currentColor; padding: 1rem; margin-block: 1rem; }}
.check {{ margin-block: .8rem; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; }}
@media (prefers-reduced-motion: reduce) {{ *, *::before, *::after {{ scroll-behavior: auto !important; transition: none !important; animation: none !important; }} }}
</style>
</head>
<body>
<a class="skip" href="#report">{escape(t["skip"])}</a>
<header><h1>{escape(t["title"])}</h1></header>
<main id="report" tabindex="-1">
<section aria-labelledby="safety-heading" class="status">
<h2 id="safety-heading">{escape(t["mode"])}</h2>
<p><strong>{escape(t["readonly"])}</strong></p>
</section>
<section aria-labelledby="checks-heading">
<h2 id="checks-heading">{escape(t["checks"])}</h2>
<ul>{''.join(items)}</ul>
</section>
<section aria-labelledby="limits-heading">
<h2 id="limits-heading">{escape(t["limitations"])}</h2>
<ul>{limitations}</ul>
</section>
{engineering}
</main>
</body>
</html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a diagnostic JSON record as accessible semantic HTML")
    parser.add_argument("report", type=Path)
    parser.add_argument("--lang", choices=sorted(TEXT), default="en")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-engineer", action="store_true")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    args.output.write_text(render_html(report, args.lang, not args.no_engineer), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
