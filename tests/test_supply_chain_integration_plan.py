from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "supply_chain_integration_plan.py"
spec = importlib.util.spec_from_file_location("supply_chain_integration_plan", MODULE_PATH)
assert spec and spec.loader
planner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = planner
spec.loader.exec_module(planner)


def write(root: Path, rel: str, text: str):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_planner_detects_license_spdx_and_manifests_without_scanning(tmp_path):
    write(tmp_path, "LICENSE", "MIT License")
    write(tmp_path, "src/x.py", "# SPDX-License-Identifier: MIT\n")
    write(tmp_path, "pyproject.toml", "[project]\nname='x'\n")
    result = planner.inspect(tmp_path)
    assert result["license_compliance"]["observed"]["license_files"] == ["LICENSE"]
    assert result["license_compliance"]["observed"]["spdx_marker_count"] == 1
    assert result["dependency_risk"]["observed"]["manifests"] == [{"file": "pyproject.toml", "ecosystem": "python"}]
    assert all(v is False for v in result["execution"].values())


def test_planner_detects_upstream_integration_signals(tmp_path):
    write(tmp_path, ".github/workflows/dependency-review.yml", "uses: actions/dependency-review-action@abc\n")
    write(tmp_path, ".github/workflows/osv.yml", "run: osv-scanner scan source .\n")
    write(tmp_path, ".reuse/dep5", "reuse lint\n")
    result = planner.inspect(tmp_path)
    assert result["license_compliance"]["observed"]["reuse_signals"]
    assert result["dependency_risk"]["observed"]["github_dependency_review_signals"]
    assert result["dependency_risk"]["observed"]["osv_scanner_signals"]


def test_git_and_vendor_are_skipped(tmp_path):
    write(tmp_path, ".git/config", "SPDX-License-Identifier: Secret\n")
    write(tmp_path, "vendor/package.json", "{}")
    result = planner.inspect(tmp_path)
    assert result["repository"]["file_count"] == 0
    assert result["license_compliance"]["observed"]["spdx_marker_count"] == 0
    assert result["dependency_risk"]["observed"]["manifests"] == []


def test_adoption_authorities_and_no_overclaim_are_present(tmp_path):
    result = planner.inspect(tmp_path)
    license_names = {x["name"] for x in result["license_compliance"]["authorities"]}
    dependency_names = {x["name"] for x in result["dependency_risk"]["authorities"]}
    assert {"SPDX", "REUSE", "GitHub Licensee/Licenses API"} <= license_names
    assert {"GitHub Dependency Review", "OSV-Scanner"} <= dependency_names
    joined = " ".join(result["dependency_risk"]["required_gates"]).lower()
    assert "no findings" in joined
    assert "source diffs" in joined
