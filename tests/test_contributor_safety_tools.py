from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "contributor_safety_tools.py"
spec = importlib.util.spec_from_file_location("contributor_safety_tools", MODULE_PATH)
assert spec and spec.loader
tools = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tools
spec.loader.exec_module(tools)


def test_pr_plan_recommends_draft_when_checks_missing():
    result = tools.pr_plan({
        "title": "Improve docs",
        "summary": "Adds a beginner path.",
        "base": "main",
        "head": "docs/start",
        "checks": {"tests_run": True, "ci_expected": True, "secrets_reviewed": True, "scope_reviewed": True},
    })
    assert result["decision"].startswith("DRAFT_OR_BLOCKED")
    assert result["payload"]["draft_recommended"] is True
    assert "rollback_considered" in result["failed_checks"]
    assert all(v is False for v in result["execution"].values())


def test_pr_plan_ready_only_when_all_required_checks_true():
    checks = {key: True for key in ("tests_run", "ci_expected", "secrets_reviewed", "scope_reviewed", "rollback_considered")}
    result = tools.pr_plan({"title": "Safe change", "summary": "Bounded.", "base": "main", "head": "feat/x", "checks": checks})
    assert result["decision"] == "READY_FOR_HUMAN_OR_GOVERNED_PR_CREATE"
    assert result["failed_checks"] == []
    assert result["payload"]["draft_recommended"] is False


def test_pr_plan_rejects_same_head_and_base():
    with pytest.raises(tools.InputError):
        tools.pr_plan({"title": "x", "summary": "y", "base": "main", "head": "main", "checks": {}})


def test_onboarding_exposes_maintainer_gaps():
    result = tools.onboarding_plan({"project": "demo", "files": {"README.md": True, "LICENSE": True}})
    assert result["status"] == "ONBOARDING_PATH_HAS_GAPS"
    joined = " ".join(result["maintainer_gaps"])
    assert "START-HERE" in joined
    assert "CONTRIBUTING" in joined
    assert all(v is False for v in result["execution"].values())


def test_codeowners_proposal_validates_owner_tokens_and_does_not_write():
    result = tools.codeowners_proposal({"rules": [
        {"pattern": "*", "owners": ["@octocat"]},
        {"pattern": "/docs/", "owners": ["@org/docs-team"]},
        {"pattern": "/.github/CODEOWNERS", "owners": ["@octocat"]},
    ]})
    assert "/docs/ @org/docs-team" in result["proposed_content"]
    assert "includes ownership" in result["security_note"].lower()
    assert all(v is False for v in result["execution"].values())


def test_codeowners_proposal_rejects_malformed_owner_and_comment_pattern():
    with pytest.raises(tools.InputError):
        tools.codeowners_proposal({"rules": [{"pattern": "*", "owners": ["octocat"]}]})
    with pytest.raises(tools.InputError):
        tools.codeowners_proposal({"rules": [{"pattern": "#bad", "owners": ["@octocat"]}]})
