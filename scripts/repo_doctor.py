#!/usr/bin/env python3
"""Read-only repository structure/explainability doctor.

This is a bounded first-pass auditor, not a substitute for specialist tools such
as OpenSSF Scorecard, Gitleaks, markdownlint, or lychee. It reads a local working
tree, never invokes scripts from that tree, and does not inspect .git internals.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
MAX_TEXT_BYTES = 1_000_000
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", "vendor"}
TEXT_EXTENSIONS = {".md", ".txt", ".sh", ".ps1", ".py", ".js", ".ts", ".yml", ".yaml", ".json", ".toml"}
DANGEROUS_PATTERNS = {
    "recursive_force_delete": re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f|\brm\s+-[a-zA-Z]*f[a-zA-Z]*r", re.I),
    "pipe_to_shell": re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:sh|bash|zsh)\b", re.I),
    "powershell_execution_policy_bypass": re.compile(r"ExecutionPolicy\s+Bypass", re.I),
    "disk_format_or_partition": re.compile(r"\b(?:mkfs(?:\.[a-z0-9]+)?|diskpart|format\.com)\b", re.I),
}
MUTATION_PATTERNS = {
    "filesystem_write": re.compile(r"\b(?:rm|mv|cp|mkdir|touch|chmod|chown)\b|Set-Content|Remove-Item|Move-Item|Copy-Item", re.I),
    "package_change": re.compile(r"\b(?:apt|apt-get|dnf|yum|pacman|brew|pip|npm|pnpm|yarn)\s+(?:install|remove|uninstall|upgrade|update)\b", re.I),
    "service_change": re.compile(r"\b(?:systemctl|service)\s+(?:start|stop|restart|enable|disable)\b|Restart-Service|Start-Service|Stop-Service", re.I),
    "network_or_firewall_change": re.compile(r"\b(?:iptables|nft|ufw)\b|New-NetFirewallRule|Set-NetFirewallProfile", re.I),
}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield path, rel


def read_bounded(path: Path) -> str | None:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES or path.suffix.lower() not in TEXT_EXTENSIONS:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def headings(markdown: str) -> list[tuple[int, str]]:
    rows = []
    fenced = False
    for line in markdown.splitlines():
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            rows.append((len(match.group(1)), match.group(2).strip()))
    return rows


def markdown_accessibility_findings(text: str, rel: str) -> list[dict[str, Any]]:
    findings = []
    hs = headings(text)
    for previous, current in zip(hs, hs[1:]):
        if current[0] > previous[0] + 1:
            findings.append({"file": rel, "kind": "heading_level_skip", "detail": f"H{previous[0]} -> H{current[0]}"})
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in re.finditer(r"!\[([^\]]*)\]\([^\)]+\)", line):
            if not match.group(1).strip():
                findings.append({"file": rel, "line": line_no, "kind": "empty_image_alt_text", "detail": "Review whether the image is decorative; otherwise provide meaningful alt text."})
    return findings


def scan_script(text: str, rel: str) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    dangerous = []
    mutations = []
    for name, pattern in DANGEROUS_PATTERNS.items():
        if pattern.search(text):
            dangerous.append({"file": rel, "pattern": name, "classification": "REVIEW_REQUIRED"})
    for name, pattern in MUTATION_PATTERNS.items():
        if pattern.search(text):
            mutations.append({"file": rel, "pattern": name, "classification": "POTENTIALLY_MUTATING"})
    return dangerous, mutations


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("repository root must be a directory")

    files = list(iter_files(root))
    rels = {rel.as_posix() for _, rel in files}
    required_public = ["README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md", "START-HERE.md"]
    structure = {name: name in rels for name in required_public}
    structure.update({
        "has_tests": any(rel.parts and rel.parts[0].lower() in {"test", "tests"} for _, rel in files),
        "has_docs": any(rel.parts and rel.parts[0].lower() == "docs" for _, rel in files),
        "has_github_workflows": any(rel.as_posix().startswith(".github/workflows/") for _, rel in files),
        "has_issue_templates": any(rel.as_posix().startswith(".github/ISSUE_TEMPLATE/") for _, rel in files),
    })

    readme = ""
    readme_path = root / "README.md"
    if readme_path.exists():
        readme = read_bounded(readme_path) or ""
    readme_headings = [title for _, title in headings(readme)]

    accessibility = []
    dangerous = []
    mutations = []
    text_files_scanned = 0
    for path, rel in files:
        text = read_bounded(path)
        if text is None:
            continue
        text_files_scanned += 1
        if rel.suffix.lower() == ".md":
            accessibility.extend(markdown_accessibility_findings(text, rel.as_posix()))
        if rel.suffix.lower() in {".sh", ".ps1", ".py", ".js", ".ts", ".yml", ".yaml"}:
            d, m = scan_script(text, rel.as_posix())
            dangerous.extend(d)
            mutations.extend(m)

    missing = [name for name, present in structure.items() if name in required_public and not present]
    recommendations = []
    if missing:
        recommendations.append("Add/review missing public-project files: " + ", ".join(missing))
    if not structure["has_tests"]:
        recommendations.append("Add a reproducible test path appropriate to the project.")
    if not structure["has_github_workflows"]:
        recommendations.append("Consider CI for tests and policy checks.")
    if accessibility:
        recommendations.append("Review Markdown accessibility findings; automated checks do not establish WCAG conformance.")
    if dangerous:
        recommendations.append("Manually review flagged high-risk command patterns before execution or publication.")
    recommendations.extend([
        "Use OpenSSF Scorecard for broader open-source security-health signals instead of recreating its checks.",
        "Use Gitleaks for secret scanning; this doctor intentionally does not implement secret detection.",
        "Use markdownlint for comprehensive Markdown style rules.",
        "Use lychee or an equivalent mature checker for live broken-link validation.",
    ])

    return {
        "schema_version": "0.1",
        "tool": {"name": "repo_doctor.py", "version": VERSION, "mode": "READ_ONLY_STATIC"},
        "repository": {"display_name": root.name, "files_seen": len(files), "text_files_scanned": text_files_scanned},
        "explain": {
            "readme_title": readme_headings[0] if readme_headings else None,
            "readme_sections": readme_headings[:40],
            "languages_or_frameworks_not_inferred": True,
            "purpose_requires_human_or_readme_context": not bool(readme_headings),
        },
        "health": {"structure": structure, "missing_public_files": missing},
        "accessibility_findings": accessibility[:200],
        "dangerous_script_findings": dangerous[:200],
        "mutation_classification_findings": mutations[:300],
        "recommendations": recommendations,
        "safety": {
            "repository_scripts_executed": False,
            "network_requests_performed": False,
            "git_history_read": False,
            "secrets_scanned": False,
            "files_changed": False,
        },
        "limitations": [
            "Regex findings are review signals, not proof that a script is safe or dangerous.",
            "No dependency vulnerability, secret-history, live-link, license-compliance or supply-chain claim is made.",
            "Markdown heuristics do not establish accessibility conformance.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only public repository structure and safety preflight")
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    try:
        report = inspect(args.root)
    except ValueError as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
