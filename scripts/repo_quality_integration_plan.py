#!/usr/bin/env python3
"""Plan adoption of mature repository-quality tools without executing them.

Roadmap scope: P-046/P-047/P-048/P-049. This planner detects only bounded
configuration/workflow signals in a local working tree. It never runs scanners,
reads .git history, prints secret values, installs packages, or edits workflows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
MAX_BYTES = 500_000

TOOLS: dict[str, dict[str, Any]] = {
    "security_health": {
        "roadmap_id": "P-046",
        "tool": "OpenSSF Scorecard",
        "authority": "https://github.com/ossf/scorecard",
        "signals": ["ossf/scorecard-action", "scorecard.yml", "scorecard.yaml"],
        "purpose": "broader open-source security-health checks",
    },
    "readme_lint": {
        "roadmap_id": "P-047",
        "tool": "markdownlint-cli2",
        "authority": "https://github.com/DavidAnson/markdownlint-cli2",
        "signals": ["markdownlint-cli2", ".markdownlint", ".markdownlint-cli2"],
        "purpose": "Markdown/README style and structural linting",
    },
    "broken_links": {
        "roadmap_id": "P-048",
        "tool": "lychee",
        "authority": "https://github.com/lycheeverse/lychee",
        "signals": ["lycheeverse/lychee-action", " lychee ", "lychee.toml", ".lychee"],
        "purpose": "live broken-link checking",
    },
    "secret_exposure": {
        "roadmap_id": "P-049",
        "tool": "Gitleaks",
        "authority": "https://github.com/gitleaks/gitleaks",
        "signals": ["gitleaks", ".gitleaks.toml"],
        "purpose": "hard-coded secret detection",
    },
}

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", "vendor"}
SCAN_SUFFIXES = {".yml", ".yaml", ".json", ".toml", ".md", ".txt"}


def iter_text(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.suffix.lower() not in SCAN_SUFFIXES and not path.name.startswith("."):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        yield rel.as_posix(), text


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("root must be a directory")

    corpus = list(iter_text(root))
    lower_files = [(name.lower(), text.lower()) for name, text in corpus]
    integrations = []
    for key, spec in TOOLS.items():
        matched = []
        for filename, text in lower_files:
            for signal in spec["signals"]:
                needle = signal.lower()
                if needle in filename or needle in text:
                    matched.append({"file": filename, "signal": signal})
                    break
        present = bool(matched)
        integrations.append({
            "integration": key,
            "roadmap_id": spec["roadmap_id"],
            "upstream_tool": spec["tool"],
            "authority": spec["authority"],
            "purpose": spec["purpose"],
            "detected": present,
            "detection_evidence": matched[:20],
            "recommended_action": (
                "VERIFY_EXISTING_INTEGRATION_AND_PINNING"
                if present
                else "ADOPT_UPSTREAM_TOOL_VIA_REVIEWED_PINNED_INTEGRATION"
            ),
            "required_gates": [
                "Review current upstream installation/action documentation at implementation time.",
                "Pin GitHub Actions by immutable commit SHA or otherwise use a verifiable version-lock strategy.",
                "Use least GITHUB_TOKEN permissions required by the integration.",
                "Do not expose raw secret findings or private values in public logs/artifacts.",
                "Retain a rollback path for any workflow/configuration mutation.",
                "Treat scanner output as a tool signal requiring context, not an automatic security verdict.",
            ],
        })

    return {
        "schema_version": "0.1",
        "tool": {"name": "repo_quality_integration_plan.py", "version": VERSION, "mode": "READ_ONLY_PLAN"},
        "repository": {"display_name": root.name, "text_files_scanned": len(corpus)},
        "integrations": integrations,
        "execution": {
            "upstream_tools_executed": False,
            "repository_code_executed": False,
            "packages_installed": False,
            "workflow_files_changed": False,
            "network_requests_performed": False,
            "git_history_read": False,
            "secret_values_collected": False,
        },
        "limitations": [
            "Detection is lexical and can produce false positives or miss dynamically composed workflow/config references.",
            "Detected configuration does not prove the upstream tool is enabled, current, secure, or passing.",
            "This planner does not replace Scorecard, markdownlint, lychee, Gitleaks, GitHub security settings, or human review.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan mature repository-quality tool adoption without executing scanners")
    parser.add_argument("root", type=Path, nargs="?", default=Path("."))
    args = parser.parse_args()
    try:
        result = inspect(args.root)
    except ValueError as exc:
        raise SystemExit(f"INPUT_ERROR: {exc}") from exc
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
