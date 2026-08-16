#!/usr/bin/env python3
"""Validate a reusable DAIS governed-release manifest.

This module is deliberately read-only. It validates release intent, exact source
identity, repository-relative inputs, and the truth boundary that publication
must not automatically imply roadmap completion.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
SEMVER = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
ROADMAP_ID = re.compile(r"^(?:P-\d{3}|F-\d{2})$")
SAFE_PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
EXPECTED_KEYS = {
    "schema_version",
    "release_id",
    "roadmap_ids",
    "tag",
    "title",
    "source_commit",
    "notes_file",
    "required_files",
    "publication_mode",
    "post_publish_exact_tag_verification_required",
    "roadmap_completion_on_publish",
    "make_latest",
}


class ManifestError(ValueError):
    pass


def safe_relpath(value: Any, *, field: str) -> str:
    if not isinstance(value, str) or not value or not SAFE_PATH.fullmatch(value):
        raise ManifestError(f"{field} must be a safe repository-relative path")
    parts = value.split("/")
    if value.startswith(".") or any(part in {"", ".", ".."} for part in parts):
        raise ManifestError(f"{field} contains forbidden traversal or dot segments")
    return value


def validate_manifest(data: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ManifestError("manifest root must be an object")
    if set(data) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(data))
        extra = sorted(set(data) - EXPECTED_KEYS)
        raise ManifestError(f"manifest key mismatch missing={missing} extra={extra}")
    if data["schema_version"] != SCHEMA_VERSION:
        raise ManifestError("unsupported manifest schema_version")

    release_id = data["release_id"]
    if not isinstance(release_id, str) or not re.fullmatch(r"[A-Z0-9][A-Z0-9_.-]{2,79}", release_id):
        raise ManifestError("release_id must be a bounded uppercase identifier")

    roadmap_ids = data["roadmap_ids"]
    if not isinstance(roadmap_ids, list) or not roadmap_ids or len(roadmap_ids) > 16:
        raise ManifestError("roadmap_ids must contain 1-16 entries")
    if any(not isinstance(item, str) or not ROADMAP_ID.fullmatch(item) for item in roadmap_ids):
        raise ManifestError("roadmap_ids contains an invalid DAIS roadmap ID")
    if len(set(roadmap_ids)) != len(roadmap_ids):
        raise ManifestError("roadmap_ids must be unique")

    tag = data["tag"]
    if not isinstance(tag, str) or not SEMVER.fullmatch(tag):
        raise ManifestError("tag must be a v-prefixed semantic version")
    source_commit = data["source_commit"]
    if not isinstance(source_commit, str) or not SHA40.fullmatch(source_commit):
        raise ManifestError("source_commit must be an exact lowercase 40-character commit SHA")

    title = data["title"]
    if not isinstance(title, str) or not (3 <= len(title) <= 160) or any(c in title for c in "\r\n"):
        raise ManifestError("title must be a single line between 3 and 160 characters")

    notes_file = safe_relpath(data["notes_file"], field="notes_file")
    if not notes_file.lower().endswith(".md"):
        raise ManifestError("notes_file must be Markdown")

    required_files = data["required_files"]
    if not isinstance(required_files, list) or not required_files or len(required_files) > 128:
        raise ManifestError("required_files must contain 1-128 repository-relative paths")
    normalized: list[str] = []
    for item in required_files:
        normalized.append(safe_relpath(item, field="required_files[]"))
    if len(set(normalized)) != len(normalized):
        raise ManifestError("required_files must be unique")
    if notes_file not in normalized:
        raise ManifestError("notes_file must also appear in required_files")

    if data["publication_mode"] != "DRAFT_THEN_PUBLISH":
        raise ManifestError("publication_mode must be DRAFT_THEN_PUBLISH")
    if data["post_publish_exact_tag_verification_required"] is not True:
        raise ManifestError("post-publish exact tag verification must be required")
    if data["roadmap_completion_on_publish"] is not False:
        raise ManifestError("release publication must never automatically imply roadmap completion")
    if not isinstance(data["make_latest"], bool):
        raise ManifestError("make_latest must be a boolean")

    missing_files = [path for path in normalized if not (repo_root / path).is_file()]
    if missing_files:
        raise ManifestError(f"required reviewed files are missing: {missing_files}")

    return {
        "schema_version": SCHEMA_VERSION,
        "decision": "MANIFEST_VALID",
        "release_id": release_id,
        "roadmap_ids": roadmap_ids,
        "tag": tag,
        "title": title,
        "source_commit": source_commit,
        "notes_file": notes_file,
        "required_files": normalized,
        "publication_mode": "DRAFT_THEN_PUBLISH",
        "make_latest": data["make_latest"],
        "release_publication_performed": False,
        "roadmap_completion_promoted": False,
    }


def load_and_validate(path: Path, repo_root: Path) -> dict[str, Any]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(str(exc)) from exc
    return validate_manifest(raw, repo_root.resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        result = load_and_validate(args.manifest, args.repo_root)
    except ManifestError as exc:
        result = {"schema_version": SCHEMA_VERSION, "decision": "BLOCKED", "error": str(exc)}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("decision") == "MANIFEST_VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
