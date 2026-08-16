#!/usr/bin/env python3
"""P-056 v0.11.1 deterministic evidence profile.

This patch keeps the bounded REUSE 6.2.0 audit semantics from v0.11.0 while
separating two different identities that v0.11.0 accidentally conflated:

* the exact raw upstream JSON bytes observed in one execution; and
* the deterministic, privacy-minimized DAIS semantic evidence record.

REUSE may serialize semantically equivalent findings in a different order across
independent executions.  Therefore an exact hash of raw upstream bytes is useful
run evidence, but it must not be embedded inside a record whose digest is claimed
to be deterministic across equivalent runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import p056_license_compliance as base

ROADMAP_ID = "P-056"
VERSION = "0.11.1"
EXPECTED_REUSE_VERSION = base.EXPECTED_REUSE_VERSION

ComplianceError = base.ComplianceError


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def audit(
    root_value: Path,
    reuse_bin_value: Path,
    *,
    expected_version: str = EXPECTED_REUSE_VERSION,
    source_revision: str = "unknown",
    dependency_lock_sha256: str,
) -> tuple[dict, bytes, str]:
    """Return deterministic semantic evidence plus exact raw-run identity.

    The raw SHA-256 is deliberately returned out-of-band.  The deterministic
    report contains only normalized facts derived by the existing bounded
    validator, so equivalent REUSE findings under the same declared dependency
    environment produce byte-identical DAIS evidence even if upstream JSON byte
    ordering differs.
    """
    report, raw = base.audit(
        root_value,
        reuse_bin_value,
        expected_version=expected_version,
        source_revision=source_revision,
        dependency_lock_sha256=dependency_lock_sha256,
    )
    raw_sha256 = _sha256(raw)
    source = report.get("source")
    if not isinstance(source, dict):
        raise ComplianceError("base P-056 report is missing source object")
    observed = source.pop("raw_reuse_report_sha256", None)
    if observed != raw_sha256:
        raise ComplianceError("base P-056 raw report digest disagrees with observed bytes")

    report["product"]["version"] = VERSION
    source["raw_reuse_report_sha256_in_deterministic_record"] = False
    report["authority"]["evidence_identity_profile"] = "semantic-v1"
    report["limitations"] = list(report["limitations"]) + [
        "Exact raw REUSE bytes have a separate per-run SHA-256 because upstream JSON serialization order is not a stable semantic identity.",
    ]
    return report, raw, raw_sha256


def run(
    root: Path,
    reuse_bin: Path,
    out_dir: Path,
    *,
    language: str,
    source_revision: str,
    dependency_lock_sha256: str,
    expected_version: str = EXPECTED_REUSE_VERSION,
) -> dict:
    if language not in {"en", "es"}:
        raise ComplianceError("language must be en or es")
    resolved_root = base._safe_root(root)
    out = base._safe_out(resolved_root, out_dir)
    report, raw, raw_sha256 = audit(
        resolved_root,
        reuse_bin,
        expected_version=expected_version,
        source_revision=source_revision,
        dependency_lock_sha256=dependency_lock_sha256,
    )
    report_bytes = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    report_path = out / "p056-license-report.json"
    guide_path = out / "p056-license-guide.md"
    raw_path = out / "p056-reuse-raw.json"
    report_path.write_bytes(report_bytes)
    guide_path.write_text(base._guide(report, language), encoding="utf-8")
    raw_path.write_bytes(raw)
    return {
        "status": report["status"],
        "compliant": str(report["summary"]["compliant"]).lower(),
        "reuse_tool_version": report["authority"]["tool_version"],
        "reuse_spec_version": report["authority"]["reuse_spec_version"],
        "report_sha256": _sha256(report_bytes),
        "raw_report_sha256": raw_sha256,
        "report_path": str(report_path),
        "guide_path": str(guide_path),
        "raw_report_path": str(raw_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="P-056 v0.11.1 deterministic REUSE evidence wrapper")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--reuse-bin", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--language", choices=("en", "es"), default="en")
    parser.add_argument("--source-revision", default="unknown")
    parser.add_argument("--dependency-lock-sha256", required=True)
    parser.add_argument("--expected-reuse-version", default=EXPECTED_REUSE_VERSION)
    args = parser.parse_args()
    try:
        result = run(
            args.root,
            args.reuse_bin,
            args.out_dir,
            language=args.language,
            source_revision=args.source_revision,
            dependency_lock_sha256=args.dependency_lock_sha256,
            expected_version=args.expected_reuse_version,
        )
    except (ComplianceError, OSError, UnicodeError) as exc:
        raise SystemExit(f"P056_INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
