#!/usr/bin/env python3
"""P-056 License Compliance Checker.

A bounded wrapper around the established REUSE CLI. It runs exactly `reuse lint
--json`, preserves the raw upstream report only in caller-selected temporary
storage, and emits a deterministic privacy-minimized evidence record plus
English/Spanish guidance.

The product verifies only what the pinned REUSE tool reports for the exact
snapshot. It never turns license metadata into legal advice, redistribution
permission, dependency-license compatibility, or a repository-safety claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
from typing import Any

ROADMAP_ID = "P-056"
VERSION = "0.11.0"
EXPECTED_REUSE_VERSION = "6.2.0"
EXPECTED_REUSE_SPEC = "3.3"
MAX_RAW_REPORT_BYTES = 32 * 1024 * 1024
TIMEOUT_SECONDS = 180
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REV_RE = re.compile(r"^[0-9a-f]{40}$")


class ComplianceError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _inside(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _safe_root(value: Path) -> Path:
    if value.is_symlink():
        raise ComplianceError("repository root must not be a symlink")
    root = value.resolve(strict=True)
    if not root.is_dir():
        raise ComplianceError("repository root must be an existing directory")
    return root


def _safe_out(root: Path, value: Path) -> Path:
    if value.is_symlink():
        raise ComplianceError("output directory must not be a symlink")
    out = value.resolve(strict=False)
    if _inside(root, out):
        raise ComplianceError("output directory must be outside the audited repository root")
    out.mkdir(parents=True, exist_ok=True)
    out = out.resolve(strict=True)
    if _inside(root, out):
        raise ComplianceError("output directory resolved inside the audited repository root")
    for name in ("p056-license-report.json", "p056-license-guide.md", "p056-reuse-raw.json"):
        candidate = out / name
        if candidate.is_symlink():
            raise ComplianceError(f"refusing symlink output target: {name}")
    return out


def _safe_reuse_bin(value: Path) -> Path:
    if value.is_symlink():
        # A caller can use a venv entry script, but the executable itself must be
        # a concrete file rather than a caller-controlled redirect.
        raise ComplianceError("reuse executable must not be a symlink")
    binary = value.resolve(strict=True)
    if not binary.is_file():
        raise ComplianceError("reuse executable must be a regular file")
    if binary.name not in {"reuse", "reuse.exe"}:
        raise ComplianceError("reuse executable basename must be reuse or reuse.exe")
    if os.name != "nt" and not os.access(binary, os.X_OK):
        raise ComplianceError("reuse executable is not executable")
    return binary


def _fixed_env() -> dict[str, str]:
    # Preserve PATH because REUSE may use the local VCS, but suppress locale and
    # interactive variability. No repository-provided environment is interpreted
    # as a command or argument by this wrapper.
    env = dict(os.environ)
    env.update({
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
        "PYTHONUTF8": "1",
        "NO_COLOR": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    })
    return env


def _run(command: list[str], *, cwd: Path, timeout: int = TIMEOUT_SECONDS) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            env=_fixed_env(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ComplianceError(f"pinned REUSE command exceeded {timeout} seconds") from exc


def _tool_version(reuse_bin: Path, root: Path, expected_version: str) -> str:
    result = _run([str(reuse_bin), "--version"], cwd=root, timeout=30)
    combined = (result.stdout + "\n" + result.stderr).strip()
    if result.returncode != 0:
        raise ComplianceError("pinned REUSE version check failed")
    match = re.search(r"(?<![0-9])([0-9]+\.[0-9]+\.[0-9]+)(?![0-9])", combined)
    if not match:
        raise ComplianceError("could not parse REUSE tool version")
    actual = match.group(1)
    if actual != expected_version:
        raise ComplianceError(f"REUSE version mismatch: expected {expected_version}, got {actual}")
    return actual


def _count_list(value: Any, field: str) -> int:
    if not isinstance(value, list):
        raise ComplianceError(f"unexpected REUSE JSON field type for {field}")
    return len(value)


def _validate_sha256(value: str, field: str) -> str:
    if not _SHA256_RE.fullmatch(value):
        raise ComplianceError(f"{field} must be a lowercase SHA-256 digest")
    return value


def _validate_revision(value: str) -> str:
    if value == "unknown":
        return value
    if not _REV_RE.fullmatch(value):
        raise ComplianceError("source revision must be a 40-character lowercase Git commit or unknown")
    return value


def audit(
    root_value: Path,
    reuse_bin_value: Path,
    *,
    expected_version: str = EXPECTED_REUSE_VERSION,
    source_revision: str = "unknown",
    dependency_lock_sha256: str,
) -> tuple[dict[str, Any], bytes]:
    root = _safe_root(root_value)
    reuse_bin = _safe_reuse_bin(reuse_bin_value)
    source_revision = _validate_revision(source_revision)
    dependency_lock_sha256 = _validate_sha256(dependency_lock_sha256, "dependency lock SHA-256")
    actual_version = _tool_version(reuse_bin, root, expected_version)

    result = _run([str(reuse_bin), "lint", "--json"], cwd=root)
    raw = result.stdout.encode("utf-8")
    if len(raw) > MAX_RAW_REPORT_BYTES:
        raise ComplianceError("REUSE JSON report exceeds bounded output limit")
    try:
        upstream = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ComplianceError("REUSE lint did not return parseable JSON") from exc
    if not isinstance(upstream, dict):
        raise ComplianceError("REUSE lint JSON root must be an object")

    tool_version = upstream.get("reuse_tool_version")
    spec_version = upstream.get("reuse_spec_version")
    if tool_version != actual_version:
        raise ComplianceError("REUSE JSON tool version disagrees with executable version")
    if spec_version != EXPECTED_REUSE_SPEC:
        raise ComplianceError(
            f"unexpected REUSE Specification version: expected {EXPECTED_REUSE_SPEC}, got {spec_version}"
        )
    summary = upstream.get("summary")
    non_compliant = upstream.get("non_compliant")
    if not isinstance(summary, dict) or not isinstance(non_compliant, dict):
        raise ComplianceError("REUSE JSON is missing summary/non_compliant objects")
    compliant = summary.get("compliant")
    if not isinstance(compliant, bool):
        raise ComplianceError("REUSE JSON summary.compliant must be boolean")

    # A successful JSON contract is authoritative for compliance state. The
    # return code is retained as evidence, not used to smooth over contradictory
    # or malformed output.
    category_fields = (
        "bad_licenses",
        "deprecated_licenses",
        "licenses_without_extension",
        "missing_licenses",
        "unused_licenses",
        "read_errors",
        "missing_copyright_info",
        "missing_licensing_info",
    )
    category_counts = {name: _count_list(non_compliant.get(name), name) for name in category_fields}

    files_total = summary.get("files_total")
    files_copyright = summary.get("files_with_copyright_info")
    files_licensing = summary.get("files_with_licensing_info")
    used_licenses = summary.get("used_licenses")
    if not all(isinstance(v, int) and v >= 0 for v in (files_total, files_copyright, files_licensing)):
        raise ComplianceError("REUSE JSON file counters must be non-negative integers")
    if not isinstance(used_licenses, list) or not all(isinstance(v, str) for v in used_licenses):
        raise ComplianceError("REUSE JSON used_licenses must be a string list")
    license_ids = sorted(set(used_licenses))
    license_set_digest = _sha256("\n".join(license_ids).encode("utf-8"))

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "roadmap_id": ROADMAP_ID,
        "product": {"name": "DAIS License Compliance Checker", "version": VERSION},
        "status": "REUSE_COMPLIANT" if compliant else "REUSE_NONCOMPLIANT",
        "source": {
            "revision": source_revision,
            "raw_reuse_report_sha256": _sha256(raw),
        },
        "authority": {
            "tool": "reuse",
            "tool_version": tool_version,
            "reuse_spec_version": spec_version,
            "lint_version": upstream.get("lint_version"),
            "exact_command": ["reuse", "lint", "--json"],
            "dependency_environment_sha256": dependency_lock_sha256,
        },
        "summary": {
            "compliant": compliant,
            "files_total": files_total,
            "files_with_copyright_info": files_copyright,
            "files_with_licensing_info": files_licensing,
            "used_license_count": len(license_ids),
            "used_license_set_sha256": license_set_digest,
            "non_compliant_category_counts": category_counts,
            "recommendation_count": _count_list(upstream.get("recommendations"), "recommendations"),
        },
        "execution": {
            "audit_network_request_performed": False,
            "repository_mutation_performed": False,
            "repository_code_executed": False,
            "shell_execution_used": False,
            "fixed_upstream_command_only": True,
        },
        "acquisition": {
            "action_policy": "exact reuse package version with resolved-environment digest",
            "network_may_be_required_to_acquire_tool": True,
            "full_transitive_dependency_hash_lock_claimed": False,
        },
        "claims": {
            "reuse_spec_compliance_reported_by_pinned_tool": compliant,
            "legal_permission_established": False,
            "license_compatibility_established": False,
            "dependency_license_safety_established": False,
            "third_party_notice_completeness_established": False,
            "distribution_legally_approved": False,
            "repository_security_guaranteed": False,
        },
        "limitations": [
            "REUSE compliance is metadata/specification evidence, not legal advice or redistribution permission.",
            "The raw REUSE report may contain repository-relative paths and stays runner-temporary unless the caller explicitly handles it.",
            "The action pins reuse==6.2.0 and records the resolved environment digest, but does not claim a fully hashed transitive dependency lock.",
            "Dependency-license compatibility and vendored/third-party legal review remain separate concerns.",
        ],
        "upstream_return_code": result.returncode,
    }
    return report, raw


def _guide(report: dict[str, Any], language: str) -> str:
    s = report["summary"]
    authority = report["authority"]
    if language == "es":
        lines = [
            "# Guía de cumplimiento de licencias",
            "",
            f"**Estado:** `{report['status']}`",
            f"**REUSE:** `{authority['tool_version']}` / especificación `{authority['reuse_spec_version']}`",
            f"**Archivos evaluados:** {s['files_total']}",
            "",
            "## Qué significa",
            "",
            ("La herramienta REUSE fijada informa que esta instantánea cumple la especificación REUSE."
             if s["compliant"] else
             "La herramienta REUSE fijada informa que esta instantánea NO cumple todavía la especificación REUSE."),
            "",
            "Esto es evidencia técnica de metadatos, no asesoría legal ni permiso para redistribuir software.",
            "",
            "## Próximos pasos",
            "",
            "1. Revise el informe bruto temporal de REUSE localmente para ver rutas y recomendaciones específicas.",
            "2. Corrija metadatos SPDX/REUSE en una rama revisada y vuelva a ejecutar el chequeo.",
            "3. Revise por separado dependencias, material de terceros, avisos y compatibilidad de políticas/licencias.",
            "4. Solicite revisión jurídica cuando una decisión de distribución o compatibilidad lo requiera.",
        ]
    else:
        lines = [
            "# License compliance guide",
            "",
            f"**Status:** `{report['status']}`",
            f"**REUSE:** `{authority['tool_version']}` / specification `{authority['reuse_spec_version']}`",
            f"**Files evaluated:** {s['files_total']}",
            "",
            "## What this means",
            "",
            ("The pinned REUSE tool reports this snapshot compliant with the REUSE Specification."
             if s["compliant"] else
             "The pinned REUSE tool reports this snapshot is NOT yet compliant with the REUSE Specification."),
            "",
            "This is technical metadata evidence, not legal advice or permission to redistribute software.",
            "",
            "## Next steps",
            "",
            "1. Review the runner-temporary raw REUSE report locally for specific paths and recommendations.",
            "2. Correct SPDX/REUSE metadata on a reviewed branch and run the check again.",
            "3. Separately review dependencies, third-party material, notices, and policy/license compatibility.",
            "4. Obtain qualified legal review when a distribution or compatibility decision requires it.",
        ]
    return "\n".join(lines) + "\n"


def run(
    root: Path,
    reuse_bin: Path,
    out_dir: Path,
    *,
    language: str,
    source_revision: str,
    dependency_lock_sha256: str,
    expected_version: str = EXPECTED_REUSE_VERSION,
) -> dict[str, Any]:
    if language not in {"en", "es"}:
        raise ComplianceError("language must be en or es")
    resolved_root = _safe_root(root)
    out = _safe_out(resolved_root, out_dir)
    report, raw = audit(
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
    guide_path.write_text(_guide(report, language), encoding="utf-8")
    raw_path.write_bytes(raw)
    return {
        "status": report["status"],
        "compliant": str(report["summary"]["compliant"]).lower(),
        "reuse_tool_version": report["authority"]["tool_version"],
        "reuse_spec_version": report["authority"]["reuse_spec_version"],
        "report_sha256": _sha256(report_bytes),
        "report_path": str(report_path),
        "guide_path": str(guide_path),
        "raw_report_path": str(raw_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded REUSE-based license-compliance evidence wrapper")
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
