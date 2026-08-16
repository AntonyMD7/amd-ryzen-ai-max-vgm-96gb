#!/usr/bin/env python3
"""Bounded, fail-closed wrapper around the upstream lychee link checker.

P-048 deliberately does not implement another link checker.  It supplies a
small DAIS policy boundary around a pinned upstream lychee binary:

* repository-contained, tracked-file-only input scope;
* no shell/eval or arbitrary upstream argument injection;
* bounded file count and input bytes;
* private/link-local/loopback network targets excluded when online;
* optional fully offline local-link checking;
* machine-readable result identity without silently converting failures.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SUPPORTED_SUFFIXES = {
    ".md",
    ".markdown",
    ".mdx",
    ".qmd",
    ".rmd",
    ".mkd",
    ".mkdn",
    ".mdwn",
    ".mdown",
    ".mkdown",
    ".html",
    ".htm",
    ".css",
    ".txt",
    ".xml",
    ".rst",
}


class ScanError(RuntimeError):
    """Expected fail-closed scanner error."""


@dataclass(frozen=True)
class Scope:
    workspace: Path
    repository_root: Path
    scan_root: Path
    scan_root_relative: str
    files: tuple[Path, ...]
    total_input_bytes: int


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _git_repository_root(workspace: Path) -> Path:
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(workspace), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ScanError("workspace is not inside a readable Git repository") from exc
    root = Path(raw).resolve(strict=True)
    if not _is_within(root, workspace):
        # The Git checkout itself may not escape the GitHub workspace.
        raise ScanError("Git repository root escapes the declared workspace")
    return root


def resolve_scope(
    *,
    workspace: Path,
    requested_root: str,
    max_files: int,
    max_input_bytes: int,
) -> Scope:
    if max_files < 1 or max_files > 100_000:
        raise ScanError("max_files must be between 1 and 100000")
    if max_input_bytes < 1 or max_input_bytes > 10 * 1024**3:
        raise ScanError("max_input_bytes must be between 1 byte and 10 GiB")
    if not requested_root or "\x00" in requested_root or "\n" in requested_root or "\r" in requested_root:
        raise ScanError("scan root is empty or contains a control character")

    workspace = workspace.resolve(strict=True)
    raw_root = Path(requested_root)
    if raw_root.is_absolute():
        raise ScanError("scan root must be workspace-relative")
    if any(part == ".." for part in raw_root.parts):
        raise ScanError("scan root may not contain parent traversal")

    candidate = (workspace / raw_root).resolve(strict=True)
    if not _is_within(candidate, workspace):
        raise ScanError("scan root escapes the workspace")
    if not candidate.is_dir():
        raise ScanError("scan root must be an existing directory")

    repository_root = _git_repository_root(workspace)
    if not _is_within(candidate, repository_root):
        raise ScanError("scan root escapes the Git repository")

    root_rel = candidate.relative_to(repository_root).as_posix() or "."
    pathspec = "." if root_rel == "." else root_rel
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(repository_root), "ls-files", "-z", "--cached", "--", pathspec],
            stderr=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ScanError("unable to enumerate tracked Git inputs") from exc

    selected: list[Path] = []
    total = 0
    for encoded in raw.split(b"\0"):
        if not encoded:
            continue
        try:
            rel = encoded.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ScanError("tracked input path is not valid UTF-8") from exc
        if any(ch in rel for ch in ("\n", "\r", "\x00")):
            raise ScanError("tracked input path contains an unsupported control character")
        path = repository_root / rel
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        if path.is_symlink():
            raise ScanError(f"refusing symlink input: {rel}")
        resolved = path.resolve(strict=True)
        if not _is_within(resolved, candidate):
            continue
        if not resolved.is_file():
            continue
        size = resolved.stat().st_size
        total += size
        if total > max_input_bytes:
            raise ScanError("tracked link-scan inputs exceed max_input_bytes")
        selected.append(resolved)
        if len(selected) > max_files:
            raise ScanError("tracked link-scan inputs exceed max_files")

    return Scope(
        workspace=workspace,
        repository_root=repository_root,
        scan_root=candidate,
        scan_root_relative=root_rel,
        files=tuple(selected),
        total_input_bytes=total,
    )


def build_command(
    *,
    lychee: Path,
    repository_root: Path,
    files_from: Path,
    report: Path,
    offline: bool,
    timeout_seconds: int,
    max_retries: int,
) -> list[str]:
    if timeout_seconds < 1 or timeout_seconds > 300:
        raise ScanError("timeout_seconds must be between 1 and 300")
    if max_retries < 0 or max_retries > 10:
        raise ScanError("max_retries must be between 0 and 10")
    command = [
        str(lychee),
        "--no-progress",
        "--format",
        "json",
        "--output",
        str(report),
        "--max-retries",
        str(max_retries),
        "--timeout",
        str(timeout_seconds),
        "--exclude-private",
        "--exclude-loopback",
        "--exclude-link-local",
        "--include-mail=false",
        "--root-dir",
        str(repository_root),
        "--files-from",
        str(files_from),
    ]
    if offline:
        command.append("--offline")
    return command


def _sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(path.name + f".tmp-{os.getpid()}")
    with tmp.open("w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _lychee_version(lychee: Path) -> str:
    try:
        out = subprocess.check_output([str(lychee), "--version"], text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ScanError("unable to execute the pinned lychee binary") from exc
    return out


def run_scan(args: argparse.Namespace) -> tuple[dict, int]:
    workspace = Path(args.workspace)
    summary_path = Path(args.summary)
    report_path = Path(args.report)
    lychee = Path(args.lychee)

    base = {
        "schema_version": "1.0",
        "roadmap_id": "P-048",
        "scanner": "lychee",
        "network_policy": "OFFLINE" if args.offline else "PUBLIC_ONLY",
        "private_ranges_excluded": True,
        "loopback_excluded": True,
        "link_local_excluded": True,
        "mail_checking_enabled": False,
        "arbitrary_command_execution_enabled": False,
        "arbitrary_upstream_args_enabled": False,
        "tracked_files_only": True,
        "input_mutation_performed": False,
        "roadmap_completion_claimed": False,
    }

    try:
        if not lychee.is_file() or lychee.is_symlink():
            raise ScanError("pinned lychee executable is missing or is a symlink")
        scope = resolve_scope(
            workspace=workspace,
            requested_root=args.root,
            max_files=args.max_files,
            max_input_bytes=args.max_input_bytes,
        )
        base.update(
            {
                "scan_root": scope.scan_root_relative,
                "input_file_count": len(scope.files),
                "input_bytes": scope.total_input_bytes,
                "lychee_version": _lychee_version(lychee),
            }
        )
        if not scope.files:
            result = {**base, "status": "NO_INPUT_FILES", "exit_code": 10, "report_sha256": None}
            _atomic_json(summary_path, result)
            return result, 10

        report_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="dais-p048-") as tmpdir:
            files_from = Path(tmpdir) / "inputs.txt"
            files_from.write_text("".join(f"{path}\n" for path in scope.files), encoding="utf-8")
            command = build_command(
                lychee=lychee,
                repository_root=scope.repository_root,
                files_from=files_from,
                report=report_path,
                offline=args.offline,
                timeout_seconds=args.timeout_seconds,
                max_retries=args.max_retries,
            )
            completed = subprocess.run(command, cwd=scope.repository_root, check=False)

        status = {
            0: "PASS",
            1: "ENGINE_ERROR",
            2: "BROKEN_LINKS",
            3: "CONFIG_ERROR",
        }.get(completed.returncode, "ENGINE_ERROR")
        result = {
            **base,
            "status": status,
            "exit_code": completed.returncode,
            "report_sha256": _sha256(report_path),
        }
        _atomic_json(summary_path, result)
        return result, completed.returncode if completed.returncode in {0, 1, 2, 3} else 12
    except (ScanError, FileNotFoundError) as exc:
        result = {**base, "status": "SCOPE_OR_RUNTIME_REJECTED", "exit_code": 12, "reason": str(exc), "report_sha256": None}
        _atomic_json(summary_path, result)
        return result, 12


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded DAIS P-048 link-scan policy wrapper")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--root", default=".")
    parser.add_argument("--lychee", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--max-files", type=int, default=5000)
    parser.add_argument("--max-input-bytes", type=int, default=104857600)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    result, rc = run_scan(args)
    print(json.dumps(result, sort_keys=True))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
