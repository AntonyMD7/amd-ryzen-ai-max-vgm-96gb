#!/usr/bin/env python3
"""Create, verify, and publish an exact-source GitHub release under strict guards.

The default mode is plan-only. Actual mutation requires --execute and a trusted
GitHub Actions push context on the explicitly allowed ref. The token is read only
from GH_TOKEN and is never printed. If draft verification fails after creation,
the draft is intentionally left unpublished for operator recovery.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from governed_release_manifest import ManifestError, load_and_validate

Run = Callable[[list[str]], subprocess.CompletedProcess[str]]


class PublishError(RuntimeError):
    pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, check=False, shell=False)


def require_trusted_context(env: dict[str, str], allowed_ref: str) -> dict[str, str]:
    required = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_REF": allowed_ref,
    }
    failures = [f"{key}={env.get(key, '')!r}" for key, expected in required.items() if env.get(key) != expected]
    if failures:
        raise PublishError("refusing write-capable release outside trusted push context: " + ", ".join(failures))
    repo = env.get("GITHUB_REPOSITORY", "")
    if repo.count("/") != 1 or any(ch.isspace() for ch in repo):
        raise PublishError("GITHUB_REPOSITORY is missing or malformed")
    if not env.get("GH_TOKEN"):
        raise PublishError("GH_TOKEN is required for --execute")
    return {"repository": repo, "event": env["GITHUB_EVENT_NAME"], "ref": env["GITHUB_REF"]}


def _require_ok(result: subprocess.CompletedProcess[str], label: str) -> str:
    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        raise PublishError(f"{label} failed with rc={result.returncode}: {stderr[:500]}")
    return (result.stdout or "").strip()


def _release_view(run: Run, repo: str, tag: str) -> dict[str, Any]:
    result = run([
        "gh", "release", "view", tag, "--repo", repo,
        "--json", "isDraft,tagName,name,targetCommitish,url,publishedAt",
    ])
    text = _require_ok(result, "release view")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PublishError("release view returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise PublishError("release view did not return an object")
    return data


def validate_release_view(data: dict[str, Any], manifest: dict[str, Any], *, expected_draft: bool) -> None:
    if data.get("isDraft") is not expected_draft:
        raise PublishError("release draft state differs from expected state")
    if data.get("tagName") != manifest["tag"]:
        raise PublishError("release tag differs from reviewed manifest")
    if data.get("name") != manifest["title"]:
        raise PublishError("release title differs from reviewed manifest")
    if expected_draft and data.get("targetCommitish") != manifest["source_commit"]:
        raise PublishError("draft targetCommitish differs from reviewed source commit")
    if not expected_draft and not data.get("publishedAt"):
        raise PublishError("published release has no publishedAt value")


def publish(
    manifest_path: Path,
    repo_root: Path,
    *,
    execute: bool,
    allowed_ref: str,
    evidence_path: Path,
    env: dict[str, str] | None = None,
    run: Run = _run,
) -> dict[str, Any]:
    manifest = load_and_validate(manifest_path, repo_root)
    evidence: dict[str, Any] = {
        "schema_version": "1.0",
        "tool": "governed_release_publish.py",
        "release_id": manifest["release_id"],
        "roadmap_ids": manifest["roadmap_ids"],
        "tag": manifest["tag"],
        "source_commit": manifest["source_commit"],
        "mode": "EXECUTE" if execute else "PLAN_ONLY",
        "status": "READY_FOR_TRUSTED_PUSH" if not execute else "STARTED",
        "draft_created": False,
        "draft_identity_verified": False,
        "published": False,
        "exact_tag_target_verified": False,
        "roadmap_completion_promoted": False,
    }
    if not execute:
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return evidence

    runtime_env = dict(os.environ if env is None else env)
    context = require_trusted_context(runtime_env, allowed_ref)
    repo = context["repository"]

    # The source must be a retained ancestor of the trusted release-control commit.
    _require_ok(run(["git", "cat-file", "-e", f"{manifest['source_commit']}^{{commit}}"]), "source commit lookup")
    ancestor = run(["git", "merge-base", "--is-ancestor", manifest["source_commit"], "HEAD"])
    if ancestor.returncode != 0:
        raise PublishError("reviewed source commit is not an ancestor of release-control HEAD")

    existing_release = run(["gh", "release", "view", manifest["tag"], "--repo", repo])
    if existing_release.returncode == 0:
        raise PublishError("release already exists; overwrite is forbidden")
    existing_tag = run([
        "git", "ls-remote", "--exit-code", "--tags", f"https://github.com/{repo}.git", f"refs/tags/{manifest['tag']}"
    ])
    if existing_tag.returncode == 0:
        raise PublishError("tag already exists; moving or overwriting tags is forbidden")

    make_latest = "true" if manifest["make_latest"] else "false"
    create = run([
        "gh", "release", "create", manifest["tag"], "--repo", repo,
        "--target", manifest["source_commit"], "--title", manifest["title"],
        "--notes-file", manifest["notes_file"], "--draft", "--latest=false",
    ])
    _require_ok(create, "draft release creation")
    evidence["draft_created"] = True
    evidence["status"] = "DRAFT_CREATED_RECOVERY_AVAILABLE"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    draft = _release_view(run, repo, manifest["tag"])
    validate_release_view(draft, manifest, expected_draft=True)
    evidence["draft_identity_verified"] = True

    edit_cmd = ["gh", "release", "edit", manifest["tag"], "--repo", repo, "--draft=false"]
    if make_latest == "true":
        edit_cmd.append("--latest")
    _require_ok(run(edit_cmd), "release publication")

    published = _release_view(run, repo, manifest["tag"])
    validate_release_view(published, manifest, expected_draft=False)
    evidence["published"] = True
    evidence["release_url"] = published.get("url", "")
    evidence["published_at"] = published.get("publishedAt", "")

    remote = _require_ok(run([
        "git", "ls-remote", "--tags", f"https://github.com/{repo}.git", f"refs/tags/{manifest['tag']}"
    ]), "post-publish tag lookup")
    resolved = remote.split()[0] if remote else ""
    if resolved != manifest["source_commit"]:
        raise PublishError("published tag does not resolve exactly to reviewed source commit")
    evidence["resolved_tag_commit"] = resolved
    evidence["exact_tag_target_verified"] = True
    evidence["status"] = "PUBLISHED_AND_EXACT_TAG_VERIFIED"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return evidence


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--allowed-ref", default="refs/heads/main")
    parser.add_argument("--evidence", type=Path, default=Path("governed-release-evidence.json"))
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = publish(
            args.manifest,
            args.repo_root.resolve(),
            execute=args.execute,
            allowed_ref=args.allowed_ref,
            evidence_path=args.evidence,
        )
    except (ManifestError, PublishError, OSError) as exc:
        failure = {
            "schema_version": "1.0",
            "tool": "governed_release_publish.py",
            "status": "BLOCKED_OR_RECOVERY_REQUIRED",
            "error": str(exc),
            "roadmap_completion_promoted": False,
        }
        try:
            args.evidence.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        except OSError:
            pass
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
