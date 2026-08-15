#!/usr/bin/env python3
"""Read-only supply-chain integration planner for licensing and dependencies.

Roadmap scope: P-056 License Compliance Checker and P-060 Dependency Risk
Summarizer. This tool intentionally does not implement a license engine or
vulnerability database. It inventories bounded local signals and recommends
mature upstream integrations (SPDX/REUSE/Licensee, GitHub Dependency Review,
OSV-Scanner) with explicit verification gates.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
MAX_BYTES = 1_000_000
SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "dist", "build", ".next", "vendor"}
MANIFESTS = {
    "package.json": "npm/node",
    "package-lock.json": "npm/node",
    "pnpm-lock.yaml": "pnpm/node",
    "yarn.lock": "yarn/node",
    "requirements.txt": "python",
    "pyproject.toml": "python",
    "poetry.lock": "python",
    "uv.lock": "python",
    "Cargo.toml": "rust",
    "Cargo.lock": "rust",
    "go.mod": "go",
    "go.sum": "go",
    "pom.xml": "maven/java",
    "build.gradle": "gradle/java",
    "build.gradle.kts": "gradle/java",
}
SPDX_RE = re.compile(r"SPDX-License-Identifier:\s*([^\s*]+(?:\s+(?:AND|OR|WITH)\s+[^\s*]+)*)", re.I)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        yield path, rel.as_posix()


def inspect(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("root must be a directory")
    files = list(iter_files(root))
    names = {rel for _, rel in files}
    basenames = {Path(rel).name for _, rel in files}
    license_files = sorted([rel for _, rel in files if Path(rel).name.upper().startswith(("LICENSE", "COPYING"))])
    manifests = sorted(
        [{"file": rel, "ecosystem": MANIFESTS[Path(rel).name]} for _, rel in files if Path(rel).name in MANIFESTS],
        key=lambda x: x["file"],
    )

    spdx_hits = []
    reuse_signals = []
    dependency_review_signals = []
    osv_signals = []
    for path, rel in files:
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for match in SPDX_RE.finditer(text):
            spdx_hits.append({"file": rel, "expression": match.group(1)[:200]})
        lower = text.lower()
        filename = rel.lower()
        if "reuse lint" in lower or ".reuse/" in filename or "reuse.software" in lower:
            reuse_signals.append(rel)
        if "actions/dependency-review-action" in lower or "dependency-review" in filename:
            dependency_review_signals.append(rel)
        if "osv-scanner" in lower or "osv-scanner" in filename:
            osv_signals.append(rel)

    license_plan = {
        "roadmap_id": "P-056",
        "state": "INTEGRATION_PLANNING",
        "observed": {
            "license_files": license_files,
            "spdx_marker_count": len(spdx_hits),
            "spdx_samples": spdx_hits[:30],
            "reuse_signals": sorted(set(reuse_signals)),
        },
        "authorities": [
            {"name": "SPDX", "purpose": "standard license identifiers/expressions and SBOM/licensing metadata", "url": "https://spdx.dev/"},
            {"name": "REUSE", "purpose": "machine-readable per-file copyright/license practice and linting", "url": "https://reuse.software/"},
            {"name": "GitHub Licensee/Licenses API", "purpose": "repository-level license recognition", "url": "https://docs.github.com/en/rest/licenses/licenses"},
        ],
        "recommendation": "ADOPT_REUSE_AND_SPDX_WITH_GITHUB_LICENSE_RECOGNITION",
        "required_gates": [
            "Do not infer legal permission from a filename alone; validate license text/metadata with mature tooling.",
            "Use SPDX expressions for multi-license cases rather than flattening them into one label.",
            "Review vendored/third-party material separately and preserve upstream notices.",
            "Treat policy compatibility decisions as organization/legal policy, not a generic scanner verdict.",
        ],
    }

    dependency_plan = {
        "roadmap_id": "P-060",
        "state": "INTEGRATION_PLANNING",
        "observed": {
            "manifests": manifests,
            "github_dependency_review_signals": sorted(set(dependency_review_signals)),
            "osv_scanner_signals": sorted(set(osv_signals)),
        },
        "authorities": [
            {"name": "GitHub Dependency Review", "purpose": "PR dependency-change/vulnerability/license policy checks", "url": "https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review"},
            {"name": "OSV-Scanner", "purpose": "open-source dependency vulnerability scanning/remediation guidance", "url": "https://github.com/google/osv-scanner"},
        ],
        "recommendation": "ADOPT_DEPENDENCY_REVIEW_FOR_PR_DIFFS_AND_OSV_SCANNER_FOR_BROADER_SCANS",
        "required_gates": [
            "Pin reviewed GitHub Actions/release artifacts to immutable/verifiable revisions.",
            "Retain manifest/lockfile provenance and scanner/database version in evidence.",
            "Do not equate 'no findings' with no dependency risk; unsupported manifests or stale databases must be explicit.",
            "Review source diffs as well as dependency metadata because scanners may not parse every dependency source.",
        ],
    }

    return {
        "schema_version": "0.1",
        "tool": {"name": "supply_chain_integration_plan.py", "version": VERSION, "mode": "READ_ONLY_PLAN"},
        "repository": {"display_name": root.name, "file_count": len(files)},
        "license_compliance": license_plan,
        "dependency_risk": dependency_plan,
        "execution": {
            "license_tool_executed": False,
            "vulnerability_scanner_executed": False,
            "network_request_performed": False,
            "git_history_read": False,
            "dependency_installed": False,
            "repository_changed": False,
        },
        "limitations": [
            "SPDX markers are reported lexically; this planner does not validate full SPDX expression grammar or legal compatibility.",
            "Manifest discovery does not resolve a dependency graph or determine whether dependencies are reachable/exploitable.",
            "No legal, vulnerability-free, or supply-chain-safe conclusion is produced by this planner.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan mature license/dependency tooling without executing scanners")
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
