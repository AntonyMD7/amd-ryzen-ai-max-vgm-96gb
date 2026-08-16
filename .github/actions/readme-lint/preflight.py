#!/usr/bin/env python3
"""Fail-closed scope preflight for the DAIS README Lint Action (P-047)."""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

MAX_READMES = 250
MAX_FILE_BYTES = 2_000_000
MAX_TOTAL_BYTES = 10_000_000
SKIP_PARTS = {'.git', 'node_modules', 'vendor', '.venv', 'venv', 'dist', 'build'}
SAFE_ROOT = re.compile(r'^[A-Za-z0-9._/-]+$')


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def inspect(root_text: str, workspace: Path | None = None) -> list[Path]:
    workspace = (workspace or Path.cwd()).resolve()
    if not root_text or '\n' in root_text or '\r' in root_text or '\\' in root_text:
        raise ValueError('root must be one non-empty POSIX-style relative path')
    if not SAFE_ROOT.fullmatch(root_text):
        raise ValueError('root contains unsupported characters or glob syntax')
    candidate = Path(root_text)
    if candidate.is_absolute() or '..' in candidate.parts:
        raise ValueError('root must stay inside the checked-out workspace')
    raw_root = workspace / candidate
    if raw_root.is_symlink():
        raise ValueError('root symlinks are refused')
    root = raw_root.resolve()
    if not _within(root, workspace) or not root.is_dir():
        raise ValueError('root must resolve to an existing workspace directory')

    readmes: list[Path] = []
    total = 0
    for path in sorted(root.rglob('README.md')):
        rel = path.relative_to(root)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if path.is_symlink():
            raise ValueError(f'README symlink refused: {rel.as_posix()}')
        resolved = path.resolve()
        if not _within(resolved, root) or not resolved.is_file():
            raise ValueError(f'README escapes selected root: {rel.as_posix()}')
        size = resolved.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f'README exceeds {MAX_FILE_BYTES} byte limit: {rel.as_posix()}')
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError(f'combined README size exceeds {MAX_TOTAL_BYTES} byte limit')
        readmes.append(resolved)
        if len(readmes) > MAX_READMES:
            raise ValueError(f'README count exceeds {MAX_READMES} file limit')

    if not readmes:
        raise ValueError('no bounded README.md files found under root')
    return readmes


def main(argv: list[str]) -> int:
    root_text = argv[1] if len(argv) == 2 else ''
    try:
        readmes = inspect(root_text)
    except ValueError as exc:
        print(f'P047_PREFLIGHT=REFUSED: {exc}', file=sys.stderr)
        return 2
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a', encoding='utf-8') as handle:
            handle.write(f'readme_count={len(readmes)}\n')
    print('P047_PREFLIGHT=PASS')
    print(f'README_COUNT={len(readmes)}')
    print('INPUT_MUTATION_PERFORMED=NO')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
