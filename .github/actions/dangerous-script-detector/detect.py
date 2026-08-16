#!/usr/bin/env python3
"""DAIS P-058 Dangerous-Script Detector v0.12.0.

Bounded, static, non-executing lexical risk detector for selected script and
GitHub Actions files. Findings are review evidence, never proof of malicious
intent or proof that an unflagged script is safe.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

VERSION = "0.12.0"
ROADMAP_ID = "P-058"
MAX_FILES = 5000
MAX_FILE_BYTES = 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
SKIP_DIRS = {".git", ".venv", "node_modules"}
SEVERITY_ORDER = {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
SUFFIX_LANGUAGE = {
    ".sh": "shell", ".bash": "shell", ".zsh": "shell", ".ksh": "shell",
    ".ps1": "powershell", ".psm1": "powershell",
    ".bat": "batch", ".cmd": "batch",
    ".yml": "yaml", ".yaml": "yaml",
}

class UnsafeInput(ValueError):
    pass

@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    category: str
    languages: frozenset[str]
    pattern: re.Pattern[str]
    rationale: str

def rule(rule_id: str, severity: str, category: str, languages: Iterable[str], pattern: str, rationale: str) -> Rule:
    return Rule(rule_id, severity, category, frozenset(languages), re.compile(pattern, re.IGNORECASE), rationale)

RULES = (
    rule("DS001", "CRITICAL", "remote-code-execution", {"shell", "yaml"}, r"\b(?:curl|wget)\b[^\n|]{0,500}\|\s*(?:sudo\s+)?(?:sh|bash|zsh|ksh)\b", "Remote content is piped directly into a shell."),
    rule("DS002", "CRITICAL", "remote-code-execution", {"powershell", "yaml"}, r"\b(?:invoke-webrequest|iwr|wget|curl|downloadstring)\b.{0,500}\b(?:invoke-expression|iex)\b", "Downloaded content is coupled to PowerShell expression execution."),
    rule("DS003", "CRITICAL", "obfuscated-execution", {"powershell", "batch", "yaml"}, r"\bpowershell(?:\.exe)?\b[^\n]{0,500}(?:-(?:enc|encodedcommand)\b|-e\s+[A-Za-z0-9+/=]{20,})", "Encoded PowerShell execution can obscure the command being run."),
    rule("DS010", "HIGH", "destructive-filesystem", {"shell", "yaml"}, r"(?:^|[;&|]\s*|\s)\brm\s+(?=[^\n]*-[A-Za-z]*r)(?=[^\n]*-[A-Za-z]*f)[^\n]{0,200}\s/(?:\s|$|\*|['\"])", "Recursive forced deletion targets a filesystem-root path."),
    rule("DS011", "HIGH", "destructive-storage", {"shell", "powershell", "batch", "yaml"}, r"\b(?:mkfs(?:\.[A-Za-z0-9_-]+)?|clear-disk|initialize-disk)\b|(?:^|\s)format(?:\.com)?\s+[A-Za-z]:", "The command can format or initialize storage."),
    rule("DS012", "HIGH", "raw-disk-write", {"shell", "yaml"}, r"\bdd\b[^\n]{0,500}\bof=/dev/(?:sd[a-z]\d*|nvme\d+n\d+(?:p\d+)?|vd[a-z]\d*|xvd[a-z]\d*)\b", "dd writes directly to a block device."),
    rule("DS013", "HIGH", "dynamic-execution", {"shell", "powershell", "yaml"}, r"(?:^|[;&|]\s*|\s)\beval\b\s+|\b(?:invoke-expression|iex)\b\s+", "Dynamic expression execution can turn data into code."),
    rule("DS014", "HIGH", "privileged-mutation", {"shell", "yaml"}, r"\b(?:sudo|doas)\b[^\n]{0,300}\b(?:rm|mkfs|dd|systemctl|service|apt(?:-get)?|dnf|yum|pacman|zypper)\b", "A privileged command performs mutation or package/service control."),
    rule("DS015", "HIGH", "service-mutation", {"shell", "yaml"}, r"\b(?:systemctl|service)\s+(?:stop|disable|mask|restart|start|enable)\b", "The command changes service state."),
    rule("DS016", "HIGH", "registry-mutation", {"powershell", "batch", "yaml"}, r"\breg(?:\.exe)?\s+(?:add|delete)\b|\b(?:remove-itemproperty|set-itemproperty)\b", "The command mutates the Windows registry."),
    rule("DS017", "HIGH", "firewall-weakening", {"shell", "powershell", "batch", "yaml"}, r"\bufw\s+(?:disable|reset)\b|\biptables\b[^\n]{0,300}\s-F\b|\bnft\b[^\n]{0,300}\bflush\b|\bset-netfirewallprofile\b[^\n]{0,300}-enabled\s+\$?false\b", "The command can disable or flush firewall policy."),
    rule("DS018", "HIGH", "permission-weakening", {"shell", "yaml"}, r"\bchmod\s+(?:-R\s+)?(?:0?777|a\+rwx)\b", "World-writable/executable permissions materially weaken access controls."),
    rule("DS019", "HIGH", "execution-policy-bypass", {"powershell", "batch", "yaml"}, r"\bpowershell(?:\.exe)?\b[^\n]{0,300}-(?:executionpolicy|ep)\s+bypass\b", "PowerShell execution-policy bypass reduces a defense-in-depth barrier."),
    rule("DS030", "MEDIUM", "destructive-git", {"shell", "powershell", "batch", "yaml"}, r"\bgit\s+(?:reset\s+--hard|clean\s+-[A-Za-z]*f[A-Za-z]*d[A-Za-z]*x?|push\b[^\n]{0,200}(?:--force|-f)\b|branch\s+-D)\b", "The Git command can discard local state or rewrite remote history."),
    rule("DS031", "MEDIUM", "package-mutation", {"shell", "yaml"}, r"\b(?:apt(?:-get)?|dnf|yum|pacman|zypper)\s+(?:install|remove|purge|upgrade|dist-upgrade|update)\b", "The command changes installed packages or package metadata."),
    rule("DS032", "MEDIUM", "forced-process-termination", {"shell", "powershell", "batch", "yaml"}, r"\bkill\s+-9\b|\btaskkill(?:\.exe)?\b[^\n]{0,300}\s/F\b|\bstop-process\b[^\n]{0,300}-force\b", "Forced process termination may cause data loss or service interruption."),
    rule("DS033", "MEDIUM", "recursive-delete", {"shell", "yaml"}, r"(?:^|[;&|]\s*|\s)\brm\s+(?=[^\n]*-[A-Za-z]*r)(?=[^\n]*-[A-Za-z]*f)\b", "Recursive forced deletion deserves explicit review even away from root."),
    rule("DS034", "MEDIUM", "scheduled-persistence", {"shell", "powershell", "batch", "yaml"}, r"\b(?:crontab|register-scheduledtask)\b|\bschtasks(?:\.exe)?\b[^\n]{0,300}/create\b", "The command creates or modifies scheduled execution."),
)

def h(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def contained_root(workspace: Path, requested: str) -> Path:
    if not requested or "\x00" in requested:
        raise UnsafeInput("root is empty or contains NUL")
    p = Path(requested)
    if p.is_absolute() or any(part == ".." for part in p.parts):
        raise UnsafeInput("root must be a contained relative path")
    workspace = workspace.resolve(strict=True)
    current = workspace
    for part in p.parts:
        if part in ("", "."):
            continue
        current = current / part
        if current.is_symlink():
            raise UnsafeInput("root path contains a symlink")
    resolved = current.resolve(strict=True)
    try:
        resolved.relative_to(workspace)
    except ValueError as exc:
        raise UnsafeInput("root escapes workspace") from exc
    if not resolved.is_dir():
        raise UnsafeInput("root must be a directory")
    return resolved

def language_for(path: Path, root: Path) -> str | None:
    language = SUFFIX_LANGUAGE.get(path.suffix.lower())
    if language != "yaml":
        return language
    rel = path.relative_to(root).as_posix().lower()
    if rel.startswith(".github/workflows/") or rel.endswith("/action.yml") or rel.endswith("/action.yaml") or rel in {"action.yml", "action.yaml"}:
        return "yaml"
    return None

def candidates(root: Path) -> list[tuple[Path, str]]:
    found: list[tuple[Path, str]] = []
    for directory, dirs, files in __import__("os").walk(root, followlinks=False):
        base = Path(directory)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not (base / d).is_symlink())
        for name in sorted(files):
            path = base / name
            language = language_for(path, root)
            if language is None:
                continue
            if path.is_symlink():
                raise UnsafeInput("supported candidate is a symlink")
            if not path.is_file():
                raise UnsafeInput("supported candidate is not a regular file")
            found.append((path, language))
            if len(found) > MAX_FILES:
                raise UnsafeInput("candidate file limit exceeded")
    return found

def scan(workspace: Path, requested_root: str = ".") -> dict:
    root = contained_root(workspace, requested_root)
    findings: list[dict] = []
    files_scanned = total_bytes = 0
    language_counts: dict[str, int] = {}
    severity_counts = {"MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    for path, language in candidates(root):
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise UnsafeInput("candidate exceeds per-file size limit")
        total_bytes += size
        if total_bytes > MAX_TOTAL_BYTES:
            raise UnsafeInput("aggregate byte limit exceeded")
        raw = path.read_bytes()
        if b"\x00" in raw:
            raise UnsafeInput("binary/NUL candidate refused")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnsafeInput("non-UTF-8 candidate refused") from exc
        files_scanned += 1
        language_counts[language] = language_counts.get(language, 0) + 1
        rel = path.relative_to(root).as_posix()
        for line_number, line in enumerate(text.splitlines(), 1):
            for r in RULES:
                if language in r.languages and r.pattern.search(line):
                    severity_counts[r.severity] += 1
                    findings.append({
                        "rule_id": r.rule_id, "severity": r.severity, "category": r.category,
                        "language": language, "line_number": line_number,
                        "path_sha256": h(rel), "line_sha256": h(line), "rationale": r.rationale,
                    })
    findings.sort(key=lambda x: (x["path_sha256"], x["line_number"], x["rule_id"]))
    highest = "NONE"
    for sev in ("CRITICAL", "HIGH", "MEDIUM"):
        if severity_counts[sev]:
            highest = sev
            break
    return {
        "schema_version": "1.0", "roadmap_id": ROADMAP_ID, "version": VERSION,
        "status": "PASS" if not findings else "REVIEW_REQUIRED",
        "highest_severity": highest, "files_scanned": files_scanned,
        "bytes_scanned": total_bytes, "language_counts": dict(sorted(language_counts.items())),
        "finding_count": len(findings), "severity_counts": severity_counts,
        "findings": findings,
        "privacy": {"source_text_retained": False, "absolute_paths_retained": False, "credential_values_retained": False},
        "claims": {"repository_safe": False, "script_safe_to_execute": False, "all_dangerous_behavior_detected": False, "semantic_static_analysis_complete": False},
        "mutation_performed": False, "repository_code_executed": False, "network_access_performed": False,
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", default=".")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    output = Path(args.output)
    try:
        report = scan(Path(args.workspace), args.root)
    except (UnsafeInput, OSError) as exc:
        report = {
            "schema_version": "1.0", "roadmap_id": ROADMAP_ID, "version": VERSION,
            "status": "ERROR", "error_type": type(exc).__name__, "error_sha256": h(str(exc)),
            "privacy": {"source_text_retained": False, "absolute_paths_retained": False, "credential_values_retained": False},
            "claims": {"repository_safe": False, "script_safe_to_execute": False, "all_dangerous_behavior_detected": False, "semantic_static_analysis_complete": False},
            "mutation_performed": False, "repository_code_executed": False, "network_access_performed": False,
        }
        output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        return 2
    output.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
