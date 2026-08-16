#!/usr/bin/env python3
"""Bound and stage a working-tree-only secret scan without executing repo code."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

MAX_FILES = 5000
MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 100 * 1024 * 1024
MAX_RELATIVE_PATH_CHARS = 512
SKIP_DIR_NAMES = {".git"}


class PreflightError(ValueError):
    pass


def _inside(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def _safe_relative_root(root: str) -> Path:
    if not root or "\x00" in root:
        raise PreflightError("root must be a non-empty relative directory")
    p = Path(root)
    if p.is_absolute():
        raise PreflightError("absolute roots are not allowed")
    if any(part == ".." for part in p.parts):
        raise PreflightError("parent traversal is not allowed")
    return p


def stage_scope(workspace: Path, root: str, staging: Path) -> dict:
    workspace = workspace.resolve(strict=True)
    rel_root = _safe_relative_root(root)
    unresolved = workspace / rel_root
    if unresolved.is_symlink():
        raise PreflightError("root symlinks are not allowed")
    candidate = unresolved.resolve(strict=True)
    if not _inside(candidate, workspace) or not candidate.is_dir():
        raise PreflightError("root must resolve to a directory inside the workspace")

    # Refuse symlinked path components in the selected root.
    cursor = workspace
    for part in rel_root.parts:
        if part in ("", "."):
            continue
        cursor = cursor / part
        if cursor.is_symlink():
            raise PreflightError("symlinked root components are not allowed")

    staging.mkdir(parents=True, exist_ok=False)
    manifest = hashlib.sha256()
    file_count = 0
    total_bytes = 0

    for dirpath, dirnames, filenames in os.walk(candidate, topdown=True, followlinks=False):
        current = Path(dirpath)
        kept_dirs = []
        for name in sorted(dirnames):
            path = current / name
            if name in SKIP_DIR_NAMES:
                continue
            if path.is_symlink():
                raise PreflightError("directory symlinks are not allowed in scan scope")
            kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in sorted(filenames):
            src = current / name
            if src.is_symlink():
                raise PreflightError("file symlinks are not allowed in scan scope")
            info = src.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise PreflightError("only regular files are supported in scan scope")
            relative = src.relative_to(candidate)
            rel_text = relative.as_posix()
            if len(rel_text) > MAX_RELATIVE_PATH_CHARS:
                raise PreflightError("relative path exceeds the supported bound")
            size = info.st_size
            if size > MAX_FILE_BYTES:
                raise PreflightError("a file exceeds the 10 MiB scan bound")
            file_count += 1
            total_bytes += size
            if file_count > MAX_FILES:
                raise PreflightError("scan scope exceeds 5000 files")
            if total_bytes > MAX_TOTAL_BYTES:
                raise PreflightError("scan scope exceeds 100 MiB")

            dst = staging / relative
            dst.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with src.open("rb") as r, dst.open("wb") as w:
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    w.write(chunk)
            os.chmod(dst, 0o600)
            manifest.update(rel_text.encode("utf-8"))
            manifest.update(b"\0")
            manifest.update(digest.digest())
            manifest.update(b"\0")

    if file_count == 0:
        raise PreflightError("scan scope contains no regular files")

    return {
        "schema_version": "1.0",
        "file_count": file_count,
        "total_bytes": total_bytes,
        "scope_sha256": manifest.hexdigest(),
        "git_history_scanned": False,
        "repository_code_executed": False,
        "symlinks_followed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--staging", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        result = stage_scope(Path(args.workspace), args.root, Path(args.staging))
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"P049_PREFLIGHT_FILES={result['file_count']}")
        print(f"P049_PREFLIGHT_BYTES={result['total_bytes']}")
        print("P049_GIT_HISTORY_SCANNED=FALSE")
        print("P049_REPOSITORY_CODE_EXECUTED=FALSE")
        return 0
    except (OSError, PreflightError) as exc:
        print(f"P049_PREFLIGHT_REFUSED={type(exc).__name__}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
