#!/usr/bin/env python3
"""P-054 Contributor Onboarding Assistant.

A bounded, read-only audit of repository community-health/onboarding surfaces.
It intentionally does not call the GitHub API, execute repository code, add labels,
post comments, invite collaborators, or mutate the audited repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

VERSION = "0.9.1"
MAX_FILE_BYTES = 1024 * 1024
SUPPORTED_LANGUAGES = {"en", "es"}

CANDIDATES: dict[str, tuple[str, ...]] = {
    "readme": ("README.md",),
    "contributing": ("CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md"),
    "security": ("SECURITY.md", ".github/SECURITY.md", "docs/SECURITY.md"),
    "license": ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"),
    "code_of_conduct": ("CODE_OF_CONDUCT.md", ".github/CODE_OF_CONDUCT.md", "docs/CODE_OF_CONDUCT.md"),
    "support": ("SUPPORT.md", ".github/SUPPORT.md", "docs/SUPPORT.md"),
    "pull_request_template": (
        "PULL_REQUEST_TEMPLATE.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "docs/PULL_REQUEST_TEMPLATE.md",
    ),
    "start_here": ("START-HERE.md", "docs/START-HERE.md"),
}

REQUIRED = ("readme", "contributing", "security", "license")
RECOMMENDED = ("code_of_conduct", "support", "pull_request_template", "issue_template", "start_here")

TEXT = {
    "en": {
        "title": "Contributor onboarding guide",
        "ready": "Core onboarding baseline is present.",
        "gaps": "Core onboarding baseline has gaps.",
        "before": "Before contributing",
        "maintainer": "Maintainer follow-up",
        "privacy": "Do not include credentials, private repository content, personal/medical data, private network details, or other sensitive information in public issues or pull requests.",
        "issue": "Use the repository's issue templates for scoped questions or bug reports when available.",
        "contrib": "Read the contribution guidelines before opening a non-trivial pull request.",
        "security": "Use the security policy instead of a public issue for suspected vulnerabilities.",
        "license": "Review the project license before reusing or contributing code.",
    },
    "es": {
        "title": "Guía de incorporación para colaboradores",
        "ready": "La base principal de incorporación está presente.",
        "gaps": "La base principal de incorporación tiene elementos pendientes.",
        "before": "Antes de contribuir",
        "maintainer": "Seguimiento para mantenedores",
        "privacy": "No incluya credenciales, contenido de repositorios privados, datos personales o médicos, detalles de redes privadas ni otra información sensible en issues o pull requests públicos.",
        "issue": "Use las plantillas de issues del repositorio para preguntas acotadas o reportes de errores cuando estén disponibles.",
        "contrib": "Lea las pautas de contribución antes de abrir un pull request no trivial.",
        "security": "Use la política de seguridad, no un issue público, para vulnerabilidades sospechadas.",
        "license": "Revise la licencia del proyecto antes de reutilizar o contribuir código.",
    },
}


class AuditError(ValueError):
    pass


def _safe_root(root: Path) -> Path:
    if root.is_symlink():
        raise AuditError("repository root must not be a symlink")
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise AuditError("repository root must be a directory")
    return resolved


def _safe_candidate(root: Path, relative: str) -> Path | None:
    candidate = root / relative
    if not candidate.exists() and not candidate.is_symlink():
        return None
    if candidate.is_symlink():
        raise AuditError(f"onboarding surface must not be a symlink: {relative}")
    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AuditError(f"onboarding surface escapes repository root: {relative}") from exc
    if not resolved.is_file():
        return None
    size = resolved.stat().st_size
    if size <= 0:
        return None
    if size > MAX_FILE_BYTES:
        raise AuditError(f"onboarding surface exceeds {MAX_FILE_BYTES} bytes: {relative}")
    return resolved


def _fingerprint(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_one(root: Path, names: tuple[str, ...]) -> dict[str, Any]:
    for relative in names:
        path = _safe_candidate(root, relative)
        if path is not None:
            return {
                "present": True,
                "path": relative,
                "sha256": _fingerprint(path),
                "size_bytes": path.stat().st_size,
            }
    return {"present": False, "path": None, "sha256": None, "size_bytes": None}


def _issue_templates(root: Path) -> dict[str, Any]:
    folder = root / ".github" / "ISSUE_TEMPLATE"
    if not folder.exists() and not folder.is_symlink():
        return {"present": False, "count": 0, "paths": []}
    if folder.is_symlink():
        raise AuditError(".github/ISSUE_TEMPLATE must not be a symlink")
    resolved = folder.resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise AuditError(".github/ISSUE_TEMPLATE escapes repository root") from exc
    if not resolved.is_dir():
        return {"present": False, "count": 0, "paths": []}
    paths: list[str] = []
    for item in sorted(resolved.iterdir(), key=lambda p: p.name.lower()):
        if item.is_symlink():
            raise AuditError(f"issue template must not be a symlink: {item.name}")
        if not item.is_file() or item.suffix.lower() not in {".md", ".yml", ".yaml"}:
            continue
        if item.stat().st_size <= 0:
            continue
        if item.stat().st_size > MAX_FILE_BYTES:
            raise AuditError(f"issue template exceeds {MAX_FILE_BYTES} bytes: {item.name}")
        paths.append(f".github/ISSUE_TEMPLATE/{item.name}")
    return {"present": bool(paths), "count": len(paths), "paths": paths}


def audit_repository(root: Path, language: str = "en") -> dict[str, Any]:
    if language not in SUPPORTED_LANGUAGES:
        raise AuditError(f"unsupported language: {language}")
    safe_root = _safe_root(root)
    surfaces = {name: _find_one(safe_root, paths) for name, paths in CANDIDATES.items()}
    surfaces["issue_template"] = _issue_templates(safe_root)
    missing_required = [name for name in REQUIRED if not surfaces[name]["present"]]
    missing_recommended = [name for name in RECOMMENDED if not surfaces[name]["present"]]
    status = "ONBOARDING_BASELINE_READY" if not missing_required else "ONBOARDING_BASELINE_HAS_GAPS"
    report = {
        "schema_version": "1.0",
        "roadmap_id": "P-054",
        "product": "DAIS Contributor Onboarding Assistant",
        "version": VERSION,
        "language": language,
        "status": status,
        "required": list(REQUIRED),
        "recommended": list(RECOMMENDED),
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "surfaces": surfaces,
        "claims": {
            "github_community_profile_verified": False,
            "repository_policy_correctness_verified": False,
            "good_first_issue_availability_verified": False,
            "contributor_readiness_guaranteed": False,
            "accessibility_conformance_claimed": False,
        },
        "execution": {
            "network_request_performed": False,
            "repository_mutation_performed": False,
            "issue_or_comment_created": False,
            "collaborator_or_permission_changed": False,
            "repository_code_executed": False,
        },
    }
    report["report_sha256"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return report


def render_guide(report: dict[str, Any]) -> str:
    t = TEXT[report["language"]]
    present = report["surfaces"]
    lines = [f"# {t['title']}", "", t["ready"] if not report["missing_required"] else t["gaps"], ""]
    lines += [f"## {t['before']}", "", f"- {t['contrib']}", f"- {t['issue']}", f"- {t['security']}", f"- {t['license']}", f"- {t['privacy']}", ""]
    lines += ["## Evidence", ""]
    for key in (*REQUIRED, *RECOMMENDED):
        entry = present[key]
        if key == "issue_template":
            detail = f"{entry['count']} template(s)" if entry["present"] else "missing"
        else:
            detail = entry["path"] if entry["present"] else "missing"
        lines.append(f"- `{key}`: {detail}")
    lines += ["", f"## {t['maintainer']}", ""]
    if report["missing_required"]:
        lines.append("- Required gaps: " + ", ".join(f"`{x}`" for x in report["missing_required"]))
    else:
        lines.append("- No required baseline gaps detected.")
    if report["missing_recommended"]:
        lines.append("- Recommended gaps: " + ", ".join(f"`{x}`" for x in report["missing_recommended"]))
    else:
        lines.append("- No recommended gaps detected.")
    lines += [
        "",
        "> This is a local bounded audit, not GitHub's Community Standards API, policy approval, contributor guarantee, or accessibility-conformance result.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(report: dict[str, Any], out_dir: Path, root: Path) -> tuple[Path, Path]:
    safe_root = _safe_root(root)
    raw_out = out_dir.expanduser()
    if raw_out.exists() and raw_out.is_symlink():
        raise AuditError("output directory must not be a symlink")
    resolved_out = raw_out.resolve()
    try:
        resolved_out.relative_to(safe_root)
    except ValueError:
        pass
    else:
        raise AuditError("output directory must be outside the audited repository")
    raw_out.mkdir(parents=True, exist_ok=True)
    if raw_out.is_symlink():
        raise AuditError("output directory must not be a symlink")
    out_dir = raw_out.resolve(strict=True)
    if out_dir != resolved_out or not out_dir.is_dir():
        raise AuditError("output directory identity changed during validation")
    report_path = out_dir / "p054-onboarding-report.json"
    guide_path = out_dir / "p054-onboarding-guide.md"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    guide_path.write_text(render_guide(report), encoding="utf-8")
    return report_path, guide_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit contributor onboarding surfaces without repository/network mutation")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--language", choices=sorted(SUPPORTED_LANGUAGES), default="en")
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()
    try:
        report = audit_repository(args.root, args.language)
        if args.out_dir:
            report_path, guide_path = write_outputs(report, args.out_dir, args.root)
            print(json.dumps({
                "status": report["status"],
                "report_sha256": report["report_sha256"],
                "missing_required_count": len(report["missing_required"]),
                "report_path": str(report_path),
                "guide_path": str(guide_path),
            }, sort_keys=True))
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
    except (OSError, AuditError) as exc:
        raise SystemExit(f"AUDIT_REFUSED: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
