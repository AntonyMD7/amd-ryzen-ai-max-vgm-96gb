#!/usr/bin/env python3
"""P-055 CODEOWNERS Assistant: bounded, read-only local audit and guidance.

This tool intentionally does not replace GitHub's CODEOWNERS parser or server-side
owner/access validation. It identifies the effective local CODEOWNERS location by
GitHub's documented precedence, performs conservative local structural checks,
and emits privacy-minimized evidence plus beginner guidance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROADMAP_ID = "P-055"
VERSION = "0.10.0"
MAX_FILE_BYTES = 1024 * 1024
CANDIDATES = (".github/CODEOWNERS", "CODEOWNERS", "docs/CODEOWNERS")
AT_OWNER = re.compile(r"^@[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})(?:/[A-Za-z0-9_.-]+)?$")
EMAIL_OWNER = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class AuditError(ValueError):
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
    root = value.resolve(strict=True)
    if not root.is_dir():
        raise AuditError("root must be an existing directory")
    return root


def _candidate(root: Path, relative: str) -> tuple[Path, bool]:
    raw = root / relative
    if raw.is_symlink():
        raise AuditError(f"refusing symlink CODEOWNERS candidate: {relative}")
    if not raw.exists():
        return raw, False
    resolved = raw.resolve(strict=True)
    if not _inside(root, resolved):
        raise AuditError(f"CODEOWNERS candidate escapes root: {relative}")
    if not resolved.is_file():
        raise AuditError(f"CODEOWNERS candidate is not a regular file: {relative}")
    size = resolved.stat().st_size
    if size > MAX_FILE_BYTES:
        raise AuditError(f"CODEOWNERS candidate exceeds {MAX_FILE_BYTES} bytes: {relative}")
    return resolved, True


def _owner_kind(token: str) -> str | None:
    if AT_OWNER.fullmatch(token):
        return "team" if "/" in token else "user"
    if EMAIL_OWNER.fullmatch(token):
        return "email"
    return None


def _explicit_self_protection(pattern: str, effective_path: str) -> bool:
    """Conservative subset only; false means 'not proven', never 'unprotected'."""
    p = pattern.lstrip("/")
    effective = effective_path.lstrip("/")
    if p in {"*", "**", "**/*"}:
        return True
    if p == effective:
        return True
    parent = effective.rsplit("/", 1)[0] + "/" if "/" in effective else ""
    if parent and p in {parent, parent + "*", parent + "**", parent + "**/*"}:
        return True
    return False


def _finding(severity: str, code: str, line: int | None, message: str) -> dict[str, Any]:
    return {"severity": severity, "code": code, "line": line, "message": message}


def audit(root_value: Path) -> dict[str, Any]:
    root = _safe_root(root_value)
    present: list[tuple[str, Path]] = []
    for relative in CANDIDATES:
        path, exists = _candidate(root, relative)
        if exists:
            present.append((relative, path))

    execution = {
        "network_request_performed": False,
        "repository_mutation_performed": False,
        "repository_code_executed": False,
        "subprocess_executed": False,
    }
    claims = {
        "github_server_syntax_verified": False,
        "owner_identity_or_write_access_verified": False,
        "branch_protection_verified": False,
        "code_owner_review_requirement_verified": False,
        "comprehensive_repository_coverage_proven": False,
        "repository_security_guaranteed": False,
    }

    if not present:
        report = {
            "schema_version": "1.0",
            "roadmap_id": ROADMAP_ID,
            "product": {"name": "DAIS CODEOWNERS Assistant", "version": VERSION},
            "status": "CODEOWNERS_MISSING",
            "source": {"effective_path": None, "ignored_lower_precedence_paths": [], "file_sha256": None},
            "metrics": {"rules": 0, "comments": 0, "invalid_lines": 0, "warnings": 1, "owner_tokens": 0, "user_tokens": 0, "team_tokens": 0, "email_tokens": 0},
            "security": {"explicit_codeowners_self_protection_found": False},
            "findings": [_finding("WARNING", "CODEOWNERS_MISSING", None, "No local CODEOWNERS file was found in GitHub's documented search locations.")],
            "claims": claims,
            "execution": execution,
        }
        return report

    effective_rel, effective = present[0]
    ignored = [rel for rel, _ in present[1:]]
    data = effective.read_bytes()
    text = data.decode("utf-8", errors="strict")
    findings: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    comments = 0
    owner_counts = {"user": 0, "team": 0, "email": 0}
    last_rule_for_pattern: dict[str, int] = {}
    self_protection = False

    if ignored:
        findings.append(_finding("INFO", "LOWER_PRECEDENCE_FILES_IGNORED", None, "Additional local CODEOWNERS files exist but GitHub precedence selects the higher-priority file."))

    for lineno, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            comments += 1
            continue
        if stripped.startswith(r"\#"):
            findings.append(_finding("ERROR", "UNSUPPORTED_ESCAPED_HASH", lineno, "GitHub CODEOWNERS does not support escaping a leading # with a backslash."))
            continue
        parts = stripped.split()
        pattern = parts[0]
        owners = parts[1:]
        invalid = False
        if pattern.startswith("!"):
            findings.append(_finding("ERROR", "UNSUPPORTED_NEGATION", lineno, "CODEOWNERS does not support gitignore-style negation patterns."))
            invalid = True
        if "[" in pattern or "]" in pattern:
            findings.append(_finding("ERROR", "UNSUPPORTED_CHARACTER_RANGE", lineno, "CODEOWNERS does not support gitignore-style character ranges."))
            invalid = True
        if not owners:
            findings.append(_finding("ERROR", "MISSING_OWNER", lineno, "A CODEOWNERS rule must include at least one owner token."))
            invalid = True
        valid_owner_kinds: list[str] = []
        for owner in owners:
            kind = _owner_kind(owner)
            if kind is None:
                findings.append(_finding("ERROR", "INVALID_OWNER_TOKEN_LOCAL", lineno, "An owner token is not a locally recognizable @user, @org/team, or email form."))
                invalid = True
            else:
                valid_owner_kinds.append(kind)
                owner_counts[kind] += 1
        if pattern in last_rule_for_pattern:
            findings.append(_finding("WARNING", "DUPLICATE_EXACT_PATTERN", lineno, "This exact pattern appeared earlier; GitHub rule order makes the later matching rule significant."))
        last_rule_for_pattern[pattern] = lineno
        self_protection = self_protection or _explicit_self_protection(pattern, effective_rel)
        rules.append({
            "line": lineno,
            "pattern_sha256": _sha256(pattern.encode("utf-8")),
            "owner_count": len(owners),
            "owner_kinds": sorted(valid_owner_kinds),
            "locally_invalid": invalid,
        })

    if not rules:
        findings.append(_finding("ERROR", "NO_RULES", None, "The effective CODEOWNERS file contains no ownership rules."))
    if not self_protection:
        findings.append(_finding("WARNING", "SELF_PROTECTION_NOT_PROVEN", None, "No explicit rule in the conservative local subset proves ownership of the effective CODEOWNERS file or its containing directory."))

    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warnings = sum(1 for f in findings if f["severity"] == "WARNING")
    if errors:
        status = "CODEOWNERS_LOCAL_ERRORS"
    elif warnings:
        status = "CODEOWNERS_NEEDS_REVIEW"
    else:
        status = "CODEOWNERS_LOCAL_BASELINE_READY"

    return {
        "schema_version": "1.0",
        "roadmap_id": ROADMAP_ID,
        "product": {"name": "DAIS CODEOWNERS Assistant", "version": VERSION},
        "status": status,
        "source": {
            "effective_path": effective_rel,
            "ignored_lower_precedence_paths": ignored,
            "file_sha256": _sha256(data),
        },
        "metrics": {
            "rules": len(rules),
            "comments": comments,
            "invalid_lines": errors,
            "warnings": warnings,
            "owner_tokens": sum(owner_counts.values()),
            "user_tokens": owner_counts["user"],
            "team_tokens": owner_counts["team"],
            "email_tokens": owner_counts["email"],
        },
        "security": {"explicit_codeowners_self_protection_found": self_protection},
        "rules": rules,
        "findings": findings,
        "claims": claims,
        "execution": execution,
    }


def _guide(report: dict[str, Any], language: str) -> str:
    status = report["status"]
    n = len(report["findings"])
    if language == "es":
        title = "# Guía de CODEOWNERS"
        lines = [title, "", f"**Estado local:** `{status}`", f"**Hallazgos:** {n}", "", "## Qué significa", "", "Este resultado revisa solamente el archivo local y reglas conservadoras. GitHub sigue siendo la autoridad para sintaxis, identidad/permisos de propietarios y protección de ramas.", "", "## Próximos pasos", "", "1. Revise cada hallazgo por número de línea.", "2. Verifique propietarios y permisos en GitHub.", "3. Use la interfaz o API de errores de CODEOWNERS de GitHub para validación autoritativa.", "4. Considere proteger el propio archivo CODEOWNERS y exigir revisión de propietarios mediante reglas de rama/rulesets.", "", "No publique credenciales, secretos ni datos privados en CODEOWNERS o reportes de soporte."]
    else:
        title = "# CODEOWNERS guide"
        lines = [title, "", f"**Local status:** `{status}`", f"**Findings:** {n}", "", "## What this means", "", "This result checks only the local file and a conservative rule subset. GitHub remains authoritative for syntax, owner identity/write access, and branch/ruleset enforcement.", "", "## Next steps", "", "1. Review each finding by line number.", "2. Verify owners and repository access in GitHub.", "3. Use GitHub's CODEOWNERS errors UI/API for authoritative server-side syntax feedback.", "4. Consider protecting CODEOWNERS itself and requiring code-owner review through branch protection or rulesets.", "", "Do not publish credentials, secrets, or private data in CODEOWNERS or support reports."]
    return "\n".join(lines) + "\n"


def run(root: Path, language: str, out_dir: Path) -> dict[str, Any]:
    if language not in {"en", "es"}:
        raise AuditError("language must be en or es")
    resolved_root = _safe_root(root)
    out = out_dir.resolve()
    if _inside(resolved_root, out):
        raise AuditError("output directory must be outside the audited repository root")
    out.mkdir(parents=True, exist_ok=True)
    report = audit(resolved_root)
    raw = json.dumps(report, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    report_path = out / "p055-codeowners-report.json"
    guide_path = out / "p055-codeowners-guide.md"
    report_path.write_bytes(raw)
    guide_path.write_text(_guide(report, language), encoding="utf-8")
    return {
        "status": report["status"],
        "finding_count": len(report["findings"]),
        "report_sha256": _sha256(raw),
        "report_path": str(report_path),
        "guide_path": str(guide_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only DAIS CODEOWNERS audit and guidance")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--language", choices=("en", "es"), default="en")
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run(args.root, args.language, args.out_dir)
    except (AuditError, OSError, UnicodeError) as exc:
        raise SystemExit(f"P055_INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
