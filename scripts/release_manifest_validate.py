#!/usr/bin/env python3
"""Validate a static governed public-release manifest.

This tool is read-only. It validates the reviewed release intent and exact
source identity before a separately permissioned GitHub Actions job may create
a draft release.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SEMVER = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
PATH = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
EXPECTED_KEYS = {
    "schema_version",
    "release_id",
    "roadmap_id",
    "tag",
    "title",
    "source_commit",
    "completion_record",
    "notes_file",
    "expected_readiness_decision",
    "publication_mode",
    "post_publish_exact_tag_verification_required",
    "roadmap_completion_on_publish",
}


class ManifestError(ValueError):
    pass


def _safe_relpath(value: Any, *, suffix: str | None = None) -> str:
    if not isinstance(value, str) or not PATH.fullmatch(value):
        raise ManifestError("release manifest contains an unsafe repository-relative path")
    if value.startswith(".") or ".." in value.split("/"):
        raise ManifestError("release manifest path traversal is forbidden")
    if suffix and not value.endswith(suffix):
        raise ManifestError(f"release manifest path must end with {suffix}")
    return value


def validate_manifest(data: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    if set(data) != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - set(data))
        extra = sorted(set(data) - EXPECTED_KEYS)
        raise ManifestError(f"manifest key mismatch missing={missing} extra={extra}")
    if data["schema_version"] != "1.0":
        raise ManifestError("unsupported release manifest schema")
    if data["roadmap_id"] != "P-025" or data["release_id"] != "P025-V0.1.0":
        raise ManifestError("this release lane is scoped only to P-025 v0.1.0")
    tag = data["tag"]
    if not isinstance(tag, str) or not SEMVER.fullmatch(tag) or tag != "v0.1.0":
        raise ManifestError("expected exact governed tag v0.1.0")
    source = data["source_commit"]
    if not isinstance(source, str) or not SHA40.fullmatch(source):
        raise ManifestError("source_commit must be an exact lowercase 40-character commit")
    if source != "704f7bab429b1f67896b32bf90b99d3d0d9cd39c":
        raise ManifestError("P-025 v0.1.0 source commit is not the exact attested candidate")
    title = data["title"]
    if not isinstance(title, str) or title != "AMD Ryzen AI Max 96 GB VGM Community Toolkit v0.1.0":
        raise ManifestError("release title differs from reviewed P-025 v0.1.0 intent")
    completion = _safe_relpath(data["completion_record"], suffix=".json")
    notes = _safe_relpath(data["notes_file"], suffix=".md")
    if completion != "examples/public-build-completion-p025-in-progress.json":
        raise ManifestError("completion record is outside the reviewed P-025 record")
    if notes != "RELEASE-NOTES-v0.1.0.md":
        raise ManifestError("release notes path differs from reviewed P-025 v0.1.0 notes")
    if data["expected_readiness_decision"] != "READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW":
        raise ManifestError("unexpected release-readiness decision")
    if data["publication_mode"] != "DRAFT_THEN_PUBLISH":
        raise ManifestError("release must use draft-then-publish mode")
    if data["post_publish_exact_tag_verification_required"] is not True:
        raise ManifestError("exact post-publish tag verification must be required")
    if data["roadmap_completion_on_publish"] is not False:
        raise ManifestError("release publication must not automatically mark roadmap completion")
    for rel in (completion, notes):
        if not (repo_root / rel).is_file():
            raise ManifestError(f"required reviewed release file is missing: {rel}")
    return {
        "schema_version": "1.0",
        "decision": "MANIFEST_VALID",
        "roadmap_id": data["roadmap_id"],
        "tag": tag,
        "source_commit": source,
        "completion_record": completion,
        "notes_file": notes,
        "publication_mode": data["publication_mode"],
        "release_publication_performed": False,
        "roadmap_completion_promoted": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ManifestError("manifest root must be an object")
        result = validate_manifest(data, args.repo_root.resolve())
    except (OSError, json.JSONDecodeError, ManifestError) as exc:
        result = {"schema_version": "1.0", "decision": "BLOCKED", "error": str(exc)}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if result.get("decision") == "MANIFEST_VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
