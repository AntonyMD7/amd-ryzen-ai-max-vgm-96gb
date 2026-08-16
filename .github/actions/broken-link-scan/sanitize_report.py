#!/usr/bin/env python3
"""Convert raw Lychee output into a privacy-minimized machine result.

Raw scanner output can contain full URLs, query strings, fragments, source lines,
or other repository text. This helper intentionally retains only counts supplied
by preflight, exit classification, and SHA-256 fingerprints of raw diagnostics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def classify(code: int) -> str:
    if code == 0:
        return "PASS"
    if code == 2:
        return "FAIL"
    return "ERROR"


def main(argv: list[str]) -> int:
    if len(argv) != 8:
        print("usage: sanitize_report.py RAW STDERR EXIT DOCS BYTES URLS OUT", file=sys.stderr)
        return 2
    raw, stderr = Path(argv[1]), Path(argv[2])
    code = int(argv[3])
    out = Path(argv[7])
    result = {
        "schema_version": "p048-broken-link-result-v0.5.0",
        "status": classify(code),
        "lychee_exit_code": code,
        "document_count": int(argv[4]),
        "document_bytes": int(argv[5]),
        "absolute_url_count_preflight": int(argv[6]),
        "raw_report_sha256": sha256(raw),
        "stderr_sha256": sha256(stderr),
        "raw_report_retained": False,
        "full_urls_retained": False,
        "network_scope": "PUBLIC_GITHUB_HOSTED_ONLY",
        "private_address_requests_allowed": False,
        "claims": {
            "link_health_for_scanned_scope": code == 0,
            "documentation_correctness": False,
            "destination_semantic_correctness": False,
            "security_safety_of_destinations": False,
            "whole_repository_quality": False,
        },
    }
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
