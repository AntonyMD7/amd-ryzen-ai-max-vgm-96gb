import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from governed_release_manifest import ManifestError, validate_manifest
from governed_release_publish import PublishError, publish, require_trusted_context


SOURCE = "a" * 40


def _manifest(root: Path) -> dict:
    (root / "README.md").write_text("readme\n", encoding="utf-8")
    (root / "RELEASE.md").write_text("notes\n", encoding="utf-8")
    return {
        "schema_version": "1.0",
        "release_id": "DAIS-RELEASE-TOOLKIT-V0.2.0",
        "roadmap_ids": ["P-051", "P-057"],
        "tag": "v0.2.0",
        "title": "DAIS Governed Release Toolkit v0.2.0",
        "source_commit": SOURCE,
        "notes_file": "RELEASE.md",
        "required_files": ["README.md", "RELEASE.md"],
        "publication_mode": "DRAFT_THEN_PUBLISH",
        "post_publish_exact_tag_verification_required": True,
        "roadmap_completion_on_publish": False,
        "make_latest": True,
    }


def _write_manifest(root: Path, data: dict) -> Path:
    path = root / "manifest.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_manifest_accepts_exact_bounded_release_intent(tmp_path: Path):
    result = validate_manifest(_manifest(tmp_path), tmp_path)
    assert result["decision"] == "MANIFEST_VALID"
    assert result["roadmap_ids"] == ["P-051", "P-057"]
    assert result["roadmap_completion_promoted"] is False


def test_manifest_refuses_path_traversal(tmp_path: Path):
    data = _manifest(tmp_path)
    data["notes_file"] = "../secret.md"
    data["required_files"] = ["README.md", "../secret.md"]
    with pytest.raises(ManifestError, match="forbidden traversal"):
        validate_manifest(data, tmp_path)


def test_manifest_refuses_duplicate_or_invalid_roadmap_ids(tmp_path: Path):
    data = _manifest(tmp_path)
    data["roadmap_ids"] = ["P-051", "P-051"]
    with pytest.raises(ManifestError, match="unique"):
        validate_manifest(data, tmp_path)
    data = _manifest(tmp_path)
    data["roadmap_ids"] = ["X-999"]
    with pytest.raises(ManifestError, match="invalid DAIS roadmap ID"):
        validate_manifest(data, tmp_path)


def test_manifest_refuses_completion_on_publication(tmp_path: Path):
    data = _manifest(tmp_path)
    data["roadmap_completion_on_publish"] = True
    with pytest.raises(ManifestError, match="must never automatically imply"):
        validate_manifest(data, tmp_path)


def test_manifest_refuses_missing_reviewed_files(tmp_path: Path):
    data = _manifest(tmp_path)
    data["required_files"].append("missing.txt")
    with pytest.raises(ManifestError, match="missing"):
        validate_manifest(data, tmp_path)


def test_write_context_refuses_pull_request_and_missing_token():
    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "pull_request",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "owner/repo",
        "GH_TOKEN": "not-printed",
    }
    with pytest.raises(PublishError, match="trusted push context"):
        require_trusted_context(env, "refs/heads/main")
    env["GITHUB_EVENT_NAME"] = "push"
    env.pop("GH_TOKEN")
    with pytest.raises(PublishError, match="GH_TOKEN"):
        require_trusted_context(env, "refs/heads/main")


def test_plan_mode_performs_no_external_commands(tmp_path: Path):
    data = _manifest(tmp_path)
    manifest = _write_manifest(tmp_path, data)
    evidence = tmp_path / "evidence.json"
    commands = []

    def forbidden(cmd):
        commands.append(cmd)
        raise AssertionError("plan mode must not execute external commands")

    result = publish(
        manifest,
        tmp_path,
        execute=False,
        allowed_ref="refs/heads/main",
        evidence_path=evidence,
        run=forbidden,
    )
    assert result["status"] == "READY_FOR_TRUSTED_PUSH"
    assert commands == []
    assert json.loads(evidence.read_text())["roadmap_completion_promoted"] is False


def test_execute_draft_verify_publish_and_exact_tag_verification(tmp_path: Path):
    data = _manifest(tmp_path)
    manifest = _write_manifest(tmp_path, data)
    evidence = tmp_path / "evidence.json"
    seen = []

    def cp(cmd, rc=0, stdout="", stderr=""):
        seen.append(cmd)
        return subprocess.CompletedProcess(cmd, rc, stdout=stdout, stderr=stderr)

    def fake_run(cmd):
        if cmd[:3] == ["git", "cat-file", "-e"]:
            return cp(cmd)
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            return cp(cmd)
        if cmd[:3] == ["gh", "release", "view"] and "--json" not in cmd:
            return cp(cmd, rc=1, stderr="not found")
        if cmd[:3] == ["git", "ls-remote", "--exit-code"]:
            return cp(cmd, rc=2, stderr="not found")
        if cmd[:3] == ["gh", "release", "create"]:
            return cp(cmd, stdout="https://github.com/owner/repo/releases/tag/v0.2.0\n")
        if cmd[:3] == ["gh", "release", "view"] and "--json" in cmd:
            published = sum(1 for item in seen if item[:3] == ["gh", "release", "edit"]) > 0
            payload = {
                "isDraft": not published,
                "tagName": "v0.2.0",
                "name": "DAIS Governed Release Toolkit v0.2.0",
                "targetCommitish": SOURCE,
                "url": "https://github.com/owner/repo/releases/tag/v0.2.0",
                "publishedAt": "2026-08-16T00:00:00Z" if published else None,
            }
            return cp(cmd, stdout=json.dumps(payload))
        if cmd[:3] == ["gh", "release", "edit"]:
            return cp(cmd)
        if cmd[:2] == ["git", "ls-remote"]:
            return cp(cmd, stdout=f"{SOURCE}\trefs/tags/v0.2.0\n")
        raise AssertionError(f"unexpected command: {cmd}")

    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "owner/repo",
        "GH_TOKEN": "super-secret-token",
    }
    result = publish(
        manifest,
        tmp_path,
        execute=True,
        allowed_ref="refs/heads/main",
        evidence_path=evidence,
        env=env,
        run=fake_run,
    )
    assert result["status"] == "PUBLISHED_AND_EXACT_TAG_VERIFIED"
    assert result["draft_created"] is True
    assert result["draft_identity_verified"] is True
    assert result["published"] is True
    assert result["exact_tag_target_verified"] is True
    evidence_text = evidence.read_text(encoding="utf-8")
    assert "super-secret-token" not in evidence_text
    assert result["roadmap_completion_promoted"] is False


def test_draft_identity_failure_stops_before_publication(tmp_path: Path):
    data = _manifest(tmp_path)
    manifest = _write_manifest(tmp_path, data)
    evidence = tmp_path / "evidence.json"

    def fake_run(cmd):
        if cmd[:3] == ["git", "cat-file", "-e"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:3] == ["git", "merge-base", "--is-ancestor"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        if cmd[:3] == ["gh", "release", "view"] and "--json" not in cmd:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not found")
        if cmd[:3] == ["git", "ls-remote", "--exit-code"]:
            return subprocess.CompletedProcess(cmd, 2, stdout="", stderr="not found")
        if cmd[:3] == ["gh", "release", "create"]:
            return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")
        if cmd[:3] == ["gh", "release", "view"] and "--json" in cmd:
            payload = {
                "isDraft": True,
                "tagName": "v0.2.0",
                "name": "TAMPERED TITLE",
                "targetCommitish": SOURCE,
                "url": "",
                "publishedAt": None,
            }
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(payload), stderr="")
        if cmd[:3] == ["gh", "release", "edit"]:
            raise AssertionError("publication must not happen after draft identity failure")
        raise AssertionError(f"unexpected command: {cmd}")

    env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": "refs/heads/main",
        "GITHUB_REPOSITORY": "owner/repo",
        "GH_TOKEN": "token",
    }
    with pytest.raises(PublishError, match="title"):
        publish(
            manifest,
            tmp_path,
            execute=True,
            allowed_ref="refs/heads/main",
            evidence_path=evidence,
            env=env,
            run=fake_run,
        )
    snapshot = json.loads(evidence.read_text())
    assert snapshot["draft_created"] is True
    assert snapshot["published"] is False
    assert snapshot["status"] == "DRAFT_CREATED_RECOVERY_AVAILABLE"
