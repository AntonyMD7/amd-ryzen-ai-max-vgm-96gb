from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "repo_quality_integration_plan.py"
spec = importlib.util.spec_from_file_location("repo_quality_integration_plan", MODULE_PATH)
assert spec and spec.loader
planner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = planner
spec.loader.exec_module(planner)


def write(root: Path, rel: str, text: str):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def test_empty_repo_recommends_upstream_adoption(tmp_path):
    result = planner.inspect(tmp_path)
    assert {x["roadmap_id"] for x in result["integrations"]} == {"P-046", "P-047", "P-048", "P-049"}
    assert all(x["detected"] is False for x in result["integrations"])
    assert all(x["recommended_action"].startswith("ADOPT_UPSTREAM") for x in result["integrations"])
    assert all(v is False for v in result["execution"].values())


def test_known_configuration_signals_are_detected_without_execution(tmp_path):
    write(tmp_path, ".github/workflows/scorecard.yml", "uses: ossf/scorecard-action@deadbeef\n")
    write(tmp_path, ".markdownlint-cli2.yaml", "globs: ['README.md']\n")
    write(tmp_path, ".github/workflows/links.yml", "uses: lycheeverse/lychee-action@deadbeef\n")
    write(tmp_path, ".gitleaks.toml", "title = 'example'\n")
    result = planner.inspect(tmp_path)
    by_id = {x["roadmap_id"]: x for x in result["integrations"]}
    assert all(by_id[x]["detected"] for x in ("P-046", "P-047", "P-048", "P-049"))
    assert all(by_id[x]["recommended_action"] == "VERIFY_EXISTING_INTEGRATION_AND_PINNING" for x in by_id)
    assert result["execution"]["upstream_tools_executed"] is False


def test_git_and_dependency_dirs_are_not_scanned(tmp_path):
    write(tmp_path, ".git/config", "gitleaks")
    write(tmp_path, "node_modules/pkg/x.md", "ossf/scorecard-action")
    result = planner.inspect(tmp_path)
    assert result["repository"]["text_files_scanned"] == 0
    assert all(x["detected"] is False for x in result["integrations"])


def test_each_integration_requires_immutable_or_verifiable_pinning(tmp_path):
    result = planner.inspect(tmp_path)
    for item in result["integrations"]:
        text = " ".join(item["required_gates"]).lower()
        assert "immutable commit sha" in text
        assert "least github_token permissions" in text
        assert "raw secret findings" in text
