from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "community_maintenance_analysis.py"
spec = importlib.util.spec_from_file_location("community_maintenance_analysis", MODULE_PATH)
assert spec and spec.loader
analysis = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = analysis
spec.loader.exec_module(analysis)


def test_history_renders_known_edges_without_querying_git():
    result = analysis.history_explain({"commits": [
        {"sha": "a" * 40, "message": "root", "parents": []},
        {"sha": "b" * 40, "message": "feature", "parents": ["a" * 40]},
        {"sha": "c" * 40, "message": "merge", "parents": ["a" * 40, "b" * 40]},
    ]})
    assert "flowchart LR" in result["mermaid"]
    assert result["summary"]["known_edge_count"] == 3
    assert "cccccccc" in result["summary"]["merge_commits"]
    assert all(v is False for v in result["execution"].values())


def test_contributor_absence_matches_chaoss_over_half_rule():
    result = analysis.contributor_absence({"contributors": [
        {"label": "A", "contributions": 60},
        {"label": "B", "contributions": 25},
        {"label": "C", "contributions": 15},
    ]})
    assert result["metric"]["value"] == 1
    assert result["metric"]["decisive_contributors"] == ["A"]
    assert "not a judgment" in result["interpretation"]


def test_contributor_absence_requires_positive_total():
    with pytest.raises(analysis.InputError):
        analysis.contributor_absence({"contributors": [{"label": "A", "contributions": 0}]})


def test_issue_dedupe_surfaces_candidate_but_never_marks_duplicate():
    result = analysis.issue_dedupe({
        "target": {"number": 10, "title": "Bluetooth adapter missing after reboot", "body": "Windows cannot find bluetooth adapter"},
        "issues": [
            {"number": 1, "title": "Bluetooth adapter missing after reboot", "body": "Adapter missing on Windows after reboot"},
            {"number": 2, "title": "Improve README examples", "body": "Docs only"},
        ],
    })
    assert result["candidates"][0]["number"] == 1
    assert result["decision"] == "HUMAN_REVIEW_REQUIRED"
    assert result["automatic_duplicate_marking_allowed"] is False
    assert all(v is False for v in result["execution"].values())


def test_issue_dedupe_returns_no_strong_candidate_for_unrelated_titles():
    result = analysis.issue_dedupe({
        "target": {"number": 10, "title": "GPU driver crash", "body": "screen freezes"},
        "issues": [{"number": 1, "title": "README typo", "body": "spelling"}],
    })
    assert result["candidates"] == []
    assert result["decision"] == "NO_STRONG_LEXICAL_CANDIDATE"


def test_history_rejects_duplicate_sha():
    with pytest.raises(analysis.InputError):
        analysis.history_explain({"commits": [
            {"sha": "deadbee", "message": "one", "parents": []},
            {"sha": "deadbee", "message": "two", "parents": []},
        ]})
