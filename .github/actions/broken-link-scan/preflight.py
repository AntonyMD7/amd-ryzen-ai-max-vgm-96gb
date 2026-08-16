#!/usr/bin/env python3
"""Fail-closed input and URL-safety preflight for P-048.

The preflight performs no network access. It bounds the local document set,
rejects symlink/path escapes, and refuses explicit non-public URL targets before
Lychee is allowed to run. DNS-level private-address exclusion is additionally
enforced by Lychee's --exclude-all-private flag at request time.
"""
from __future__ import annotations

import ipaddress
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit

SUPPORTED = {".md", ".markdown", ".mdx", ".html", ".htm", ".rst", ".txt"}
SKIP_DIRS = {".git", "node_modules", "vendor", ".venv", "venv", "dist", "build"}
MAX_FILES = 500
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 25 * 1024 * 1024
URL_RE = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*):\/\/[^\s<>\"')\]}]+")
PRIVATE_NAMES = ("localhost",)
PRIVATE_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".home.arpa")


class Refusal(ValueError):
    pass


def write_output(key: str, value: str | int) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as fh:
            fh.write(f"{key}={value}\n")


def safe_root(raw: str, workspace: Path) -> Path:
    if not raw or "\n" in raw or "\r" in raw:
        raise Refusal("root must be a non-empty single-line relative path")
    p = PurePosixPath(raw.replace("\\", "/"))
    if p.is_absolute() or any(part in {"", ".."} for part in p.parts):
        raise Refusal("root must stay within the checked-out repository")
    root = (workspace / Path(*p.parts)).resolve(strict=True)
    try:
        root.relative_to(workspace)
    except ValueError as exc:
        raise Refusal("root resolves outside GITHUB_WORKSPACE") from exc
    if root.is_symlink() or not root.is_dir():
        raise Refusal("root must be an existing non-symlink directory")
    return root


def inspect_url(raw: str) -> None:
    parsed = urlsplit(raw)
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise Refusal(f"unsupported absolute URL scheme: {scheme}")
    if parsed.username is not None or parsed.password is not None:
        raise Refusal("URLs containing embedded credentials are forbidden")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise Refusal("HTTP(S) URL is missing a hostname")
    if host in PRIVATE_NAMES or any(host.endswith(sfx) for sfx in PRIVATE_SUFFIXES):
        raise Refusal("explicit local/private hostname is forbidden")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        if "." not in host:
            raise Refusal("single-label HTTP(S) hostnames are forbidden")
        return
    if not ip.is_global:
        raise Refusal("non-global IP literal is forbidden")


def discover(root: Path, workspace: Path) -> tuple[list[Path], int]:
    files: list[Path] = []
    total = 0
    for current, dirs, names in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        kept_dirs: list[str] = []
        for name in sorted(dirs):
            candidate = current_path / name
            if name in SKIP_DIRS or candidate.is_symlink():
                continue
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(names):
            candidate = current_path / name
            if candidate.suffix.lower() not in SUPPORTED:
                continue
            if "\n" in name or "\r" in name or candidate.is_symlink() or not candidate.is_file():
                raise Refusal("unsupported/symlinked document path encountered")
            size = candidate.stat().st_size
            if size > MAX_FILE_BYTES:
                raise Refusal(f"document exceeds {MAX_FILE_BYTES} byte bound")
            total += size
            if total > MAX_TOTAL_BYTES:
                raise Refusal(f"document corpus exceeds {MAX_TOTAL_BYTES} byte bound")
            files.append(candidate)
            if len(files) > MAX_FILES:
                raise Refusal(f"document count exceeds {MAX_FILES} file bound")
    return files, total


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: preflight.py ROOT", file=sys.stderr)
        return 2
    workspace_raw = os.environ.get("GITHUB_WORKSPACE")
    runner_temp_raw = os.environ.get("RUNNER_TEMP")
    if not workspace_raw or not runner_temp_raw:
        print("GITHUB_WORKSPACE and RUNNER_TEMP are required", file=sys.stderr)
        return 2
    workspace = Path(workspace_raw).resolve(strict=True)
    try:
        root = safe_root(argv[1], workspace)
        files, total = discover(root, workspace)
        if not files:
            raise Refusal("no supported documentation files found in bounded scope")
        absolute_urls = 0
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            for match in URL_RE.finditer(text):
                inspect_url(match.group(0))
                absolute_urls += 1
        manifest = Path(runner_temp_raw) / "p048-inputs.txt"
        with manifest.open("w", encoding="utf-8", newline="\n") as fh:
            for path in files:
                rel = path.relative_to(workspace).as_posix()
                fh.write(rel + "\n")
        write_output("document_count", len(files))
        write_output("document_bytes", total)
        write_output("absolute_url_count", absolute_urls)
        write_output("manifest", str(manifest))
        write_output("root_abs", str(root))
        return 0
    except (OSError, Refusal) as exc:
        print(f"P-048 preflight refused input: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
