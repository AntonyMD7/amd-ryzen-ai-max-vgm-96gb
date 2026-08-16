from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from p054_contributor_onboarding import (  # noqa: E402
    AuditError,
    audit_repository,
    render_guide,
    write_outputs,
)


def _write(root: Path, relative: str, text: str = "# Example\n") -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ready_repo(root: Path) -> None:
    for path in (
        "README.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        "LICENSE",
        "CODE_OF_CONDUCT.md",
        "SUPPORT.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        "START-HERE.md",
        ".github/ISSUE_TEMPLATE/bug.yml",
    ):
        _write(root, path)


def test_ready_repository_is_deterministic_and_non_mutating(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ready_repo(repo)
    before = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    first = audit_repository(repo, "en")
    second = audit_repository(repo, "en")
    after = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert first == second
    assert first["status"] == "ONBOARDING_BASELINE_READY"
    assert first["missing_required"] == []
    assert first["missing_recommended"] == []
    assert first["execution"] == {
        "network_request_performed": False,
        "repository_mutation_performed": False,
        "issue_or_comment_created": False,
        "collaborator_or_permission_changed": False,
        "repository_code_executed": False,
    }
    assert before == after


def test_missing_required_is_preserved_not_smoothed_over(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write(repo, "README.md")
    report = audit_repository(repo)
    assert report["status"] == "ONBOARDING_BASELINE_HAS_GAPS"
    assert report["missing_required"] == ["contributing", "security", "license"]
    assert report["claims"]["contributor_readiness_guaranteed"] is False
    assert report["claims"]["github_community_profile_verified"] is False


def test_spanish_guide_preserves_same_evidence(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ready_repo(repo)
    en = audit_repository(repo, "en")
    es = audit_repository(repo, "es")
    assert en["surfaces"] == es["surfaces"]
    guide = render_guide(es)
    assert "Guía de incorporación" in guide
    assert "No incluya credenciales" in guide
    assert "WCAG" not in guide


def test_candidate_symlink_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    external = tmp_path / "external.md"
    external.write_text("secret", encoding="utf-8")
    (repo / "README.md").symlink_to(external)
    with pytest.raises(AuditError, match="symlink"):
        audit_repository(repo)


def test_issue_template_symlink_fails_closed(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _write(repo, "README.md")
    folder = repo / ".github" / "ISSUE_TEMPLATE"
    folder.mkdir(parents=True)
    external = tmp_path / "outside.yml"
    external.write_text("name: outside", encoding="utf-8")
    (folder / "unsafe.yml").symlink_to(external)
    with pytest.raises(AuditError, match="symlink"):
        audit_repository(repo)


def test_output_inside_audited_repository_is_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ready_repo(repo)
    report = audit_repository(repo)
    with pytest.raises(AuditError, match="outside"):
        write_outputs(report, repo / "generated", repo)


def test_outputs_are_sanitized_and_outside_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ready_repo(repo)
    report = audit_repository(repo)
    report_path, guide_path = write_outputs(report, tmp_path / "out", repo)
    stored = json.loads(report_path.read_text(encoding="utf-8"))
    assert stored == report
    assert str(repo.resolve()) not in report_path.read_text(encoding="utf-8")
    assert "credentials" in guide_path.read_text(encoding="utf-8").lower()


def test_no_network_subprocess_or_mutation_executor_in_module() -> None:
    import p054_contributor_onboarding as module

    source = inspect.getsource(module)
    forbidden = (
        "import requests",
        "import urllib",
        "import socket",
        "import subprocess",
        "os.system(",
        "gh api",
        "git commit",
        "git push",
    )
    for needle in forbidden:
        assert needle not in source


def test_report_hash_changes_with_material_surface_change(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _ready_repo(repo)
    first = audit_repository(repo)
    _write(repo, "CONTRIBUTING.md", "# Changed contribution guidance\n")
    second = audit_repository(repo)
    assert first["report_sha256"] != second["report_sha256"]
    assert first["surfaces"]["contributing"]["sha256"] != second["surfaces"]["contributing"]["sha256"]


def test_unknown_language_refused(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(AuditError, match="unsupported language"):
        audit_repository(repo, "fr")
