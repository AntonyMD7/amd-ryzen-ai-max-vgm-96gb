from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / '.github/actions/readme-lint/preflight.py'
ACTION = ROOT / '.github/actions/readme-lint/action.yml'
CONFIG = ROOT / '.github/actions/readme-lint/.markdownlint-cli2.yaml'


def load_preflight():
    spec = importlib.util.spec_from_file_location('p047_preflight', PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_preflight_accepts_bounded_readme(tmp_path: Path):
    mod = load_preflight()
    (tmp_path / 'README.md').write_text('# Example\n\nSafe text.\n', encoding='utf-8')
    selected = mod.inspect('.', tmp_path)
    assert len(selected) == 1
    assert selected[0].name == 'README.md'


def test_preflight_rejects_empty_scope_and_traversal(tmp_path: Path):
    mod = load_preflight()
    with pytest.raises(ValueError, match='no bounded README'):
        mod.inspect('.', tmp_path)
    with pytest.raises(ValueError, match='inside the checked-out workspace'):
        mod.inspect('../outside', tmp_path)
    with pytest.raises(ValueError, match='glob syntax'):
        mod.inspect('docs/**', tmp_path)


def test_preflight_excludes_dependency_trees(tmp_path: Path):
    mod = load_preflight()
    dep = tmp_path / 'node_modules' / 'x'
    dep.mkdir(parents=True)
    (dep / 'README.md').write_text('# Dependency\n', encoding='utf-8')
    (tmp_path / 'README.md').write_text('# Product\n', encoding='utf-8')
    selected = mod.inspect('.', tmp_path)
    assert [p.relative_to(tmp_path).as_posix() for p in selected] == ['README.md']


def test_preflight_rejects_oversized_readme(tmp_path: Path):
    mod = load_preflight()
    (tmp_path / 'README.md').write_bytes(b'x' * (mod.MAX_FILE_BYTES + 1))
    with pytest.raises(ValueError, match='exceeds'):
        mod.inspect('.', tmp_path)


def test_preflight_rejects_readme_symlink(tmp_path: Path):
    mod = load_preflight()
    target = tmp_path / 'real.md'
    target.write_text('# Real\n', encoding='utf-8')
    link = tmp_path / 'README.md'
    try:
        link.symlink_to(target.name)
    except (OSError, NotImplementedError):
        pytest.skip('symlinks unavailable')
    with pytest.raises(ValueError, match='symlink refused'):
        mod.inspect('.', tmp_path)


def test_action_is_immutable_non_mutating_and_no_plugin_surface():
    text = ACTION.read_text(encoding='utf-8')
    assert 'DavidAnson/markdownlint-cli2-action@21c1be1b93ad9ed58fa840aacc3f279cde2a72ff' in text
    assert "fix: 'false'" in text
    assert 'pull_request_target' not in text
    assert 'customRules' not in text
    assert 'markdownItPlugins' not in text
    assert 'outputFormatters' not in text
    assert 'readme-count:' in text
    assert 'upstream-commit:' in text


def test_fixed_config_disallows_executable_extension_points():
    text = CONFIG.read_text(encoding='utf-8')
    assert 'customRules' not in text
    assert 'markdownItPlugins' not in text
    assert 'outputFormatters' not in text
    assert 'fix:' not in text
