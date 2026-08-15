from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "github_agentic_safety_plans.py"
spec = importlib.util.spec_from_file_location("github_agentic_safety_plans", MODULE_PATH)
assert spec and spec.loader
plans = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = plans
spec.loader.exec_module(plans)


def test_security_issue_is_routed_without_public_write():
    result = plans.issue_triage({"number": 7, "title": "Possible credential leak", "body": "token leak in logs"})
    assert result["category"] == "POTENTIAL_SECURITY_REPORT"
    assert result["automatic_write_allowed"] is False
    assert "do not post" in result["handling"].lower()
    assert all(v is False for v in result["execution"].values())


def test_docs_and_bug_prefilters_are_transparent():
    docs = plans.issue_triage({"number": 1, "title": "README typo", "body": "documentation spelling"})
    bug = plans.issue_triage({"number": 2, "title": "App crashes on start", "body": "regression after update"})
    assert docs["category"] == "DOCUMENTATION"
    assert bug["category"] == "BUG_CANDIDATE"
    assert docs["limitations"]


def test_pr_review_flags_workflows_dependencies_and_large_change():
    result = plans.pr_review({
        "number": 9,
        "ci_status": "success",
        "files": [
            {"path": ".github/workflows/release.yml", "additions": 30, "deletions": 2},
            {"path": "package-lock.json", "additions": 900, "deletions": 100},
        ],
    })
    kinds = {x["kind"] for x in result["risk_findings"]}
    assert "workflow_or_action" in kinds
    assert "dependency_lockfile" in kinds
    assert "large_change_set" in kinds
    assert result["decision"] == "HUMAN_REVIEW_REQUIRED"
    assert all(v is False for v in result["execution"].values())


def test_failed_ci_is_explicit_blocker():
    result = plans.pr_review({"number": 9, "ci_status": "failure", "files": []})
    assert any("failure" in item.lower() for item in result["blockers_or_review_focus"])


def test_docs_repair_proposes_pr_but_changes_nothing(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    before = (tmp_path / "README.md").read_bytes()
    result = plans.docs_repair(tmp_path)
    assert result["decision"] == "PATCH_PR_RECOMMENDED"
    assert any(x["path"] == "START-HERE.md" for x in result["proposed_repairs"])
    assert all(v is False for v in result["execution"].values())
    assert (tmp_path / "README.md").read_bytes() == before


def test_docs_repair_can_report_no_deterministic_gap(tmp_path):
    for name in plans.PUBLIC_DOCS:
        (tmp_path / name).write_text("# X\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("# Demo\nSTART-HERE CONTRIBUTING SECURITY LICENSE\n", encoding="utf-8")
    result = plans.docs_repair(tmp_path)
    assert result["decision"] == "NO_DETERMINISTIC_REPAIR_NEEDED"
