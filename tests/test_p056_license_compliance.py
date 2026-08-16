from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p056_license_compliance import ComplianceError, audit, run  # noqa: E402


LOCK_SHA = "a" * 64
REV = "1" * 40


def fake_reuse(tmp_path: Path, payload: dict, *, version: str = "6.2.0", returncode: int = 0, raw: str | None = None) -> Path:
    binary = tmp_path / "reuse"
    if raw is None:
        raw = json.dumps(payload)
    script = f'''#!/usr/bin/env python3
import sys
if sys.argv[1:] == ["--version"]:
    print("reuse {version}")
    raise SystemExit(0)
if sys.argv[1:] == ["lint", "--json"]:
    print({raw!r})
    raise SystemExit({returncode})
print("unexpected arguments", file=sys.stderr)
raise SystemExit(91)
'''
    binary.write_text(script, encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def payload(*, compliant: bool = True) -> dict:
    return {
        "lint_version": "1.0",
        "reuse_spec_version": "3.3",
        "reuse_tool_version": "6.2.0",
        "non_compliant": {
            "bad_licenses": [],
            "deprecated_licenses": [],
            "licenses_without_extension": [],
            "missing_licenses": [] if compliant else ["MIT"],
            "unused_licenses": [],
            "read_errors": [],
            "missing_copyright_info": [] if compliant else ["private/name.py"],
            "missing_licensing_info": [] if compliant else ["private/name.py"],
        },
        "files": [{"path": "private/name.py", "copyright": "Person Name"}],
        "summary": {
            "used_licenses": ["MIT"],
            "files_total": 2,
            "files_with_copyright_info": 2 if compliant else 1,
            "files_with_licensing_info": 2 if compliant else 1,
            "compliant": compliant,
        },
        "recommendations": [] if compliant else ["fix private/name.py"],
    }


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    return root


def test_compliant_upstream_result_maps_to_scoped_truth(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    report, raw = audit(root, fake_reuse(tmp_path, payload()), source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    assert report["status"] == "REUSE_COMPLIANT"
    assert report["summary"]["compliant"] is True
    assert report["authority"]["tool_version"] == "6.2.0"
    assert report["authority"]["reuse_spec_version"] == "3.3"
    assert report["claims"]["reuse_spec_compliance_reported_by_pinned_tool"] is True
    assert report["claims"]["legal_permission_established"] is False
    assert report["claims"]["license_compatibility_established"] is False
    assert report["execution"]["repository_mutation_performed"] is False
    assert report["source"]["raw_reuse_report_sha256"] == hashlib.sha256(raw).hexdigest()


def test_noncompliance_is_preserved_without_path_or_identity_leak(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    report, _ = audit(root, fake_reuse(tmp_path, payload(compliant=False), returncode=1), source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    assert report["status"] == "REUSE_NONCOMPLIANT"
    assert report["summary"]["compliant"] is False
    counts = report["summary"]["non_compliant_category_counts"]
    assert counts["missing_licenses"] == 1
    assert counts["missing_copyright_info"] == 1
    encoded = json.dumps(report)
    assert "private/name.py" not in encoded
    assert "Person Name" not in encoded
    assert "fix private/name.py" not in encoded
    assert report["claims"]["distribution_legally_approved"] is False


def test_used_license_ids_are_digest_only_in_sanitized_evidence(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    p = payload()
    p["summary"]["used_licenses"] = ["MIT", "Apache-2.0"]
    report, _ = audit(root, fake_reuse(tmp_path, p), source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    encoded = json.dumps(report)
    assert '"MIT"' not in encoded
    assert '"Apache-2.0"' not in encoded
    assert report["summary"]["used_license_count"] == 2
    assert len(report["summary"]["used_license_set_sha256"]) == 64


def test_wrong_tool_version_fails_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    with pytest.raises(ComplianceError, match="version mismatch"):
        audit(root, fake_reuse(tmp_path, payload(), version="6.1.0"), source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_wrong_spec_version_fails_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    p = payload()
    p["reuse_spec_version"] = "3.2"
    with pytest.raises(ComplianceError, match="Specification version"):
        audit(root, fake_reuse(tmp_path, p), source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_malformed_json_fails_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    with pytest.raises(ComplianceError, match="parseable JSON"):
        audit(root, fake_reuse(tmp_path, payload(), raw="not-json"), source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_invalid_structured_fields_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    p = payload()
    p["non_compliant"]["missing_licenses"] = "MIT"
    with pytest.raises(ComplianceError, match="field type"):
        audit(root, fake_reuse(tmp_path, p), source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_invalid_revision_and_dependency_digest_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    binary = fake_reuse(tmp_path, payload())
    with pytest.raises(ComplianceError, match="source revision"):
        audit(root, binary, source_revision="main", dependency_lock_sha256=LOCK_SHA)
    with pytest.raises(ComplianceError, match="SHA-256"):
        audit(root, binary, source_revision=REV, dependency_lock_sha256="abc")


def test_reuse_executable_basename_and_symlink_fail_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    bad = tmp_path / "arbitrary-command"
    bad.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    bad.chmod(bad.stat().st_mode | stat.S_IXUSR)
    with pytest.raises(ComplianceError, match="basename"):
        audit(root, bad, source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    link = tmp_path / "reuse"
    link.symlink_to(bad)
    with pytest.raises(ComplianceError, match="symlink"):
        audit(root, link, source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_output_directory_must_be_outside_repository(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    binary = fake_reuse(tmp_path, payload())
    with pytest.raises(ComplianceError, match="outside"):
        run(root, binary, root / "evidence", language="en", source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_root_symlink_fails_closed(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    root_link = tmp_path / "repo-link"
    root_link.symlink_to(root, target_is_directory=True)
    binary = fake_reuse(tmp_path, payload())
    with pytest.raises(ComplianceError, match="root must not be a symlink"):
        audit(root_link, binary, source_revision=REV, dependency_lock_sha256=LOCK_SHA)


def test_en_es_share_exact_technical_report_but_different_guides(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    binary = fake_reuse(tmp_path, payload(compliant=False), returncode=1)
    en = run(root, binary, tmp_path / "out-en", language="en", source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    es = run(root, binary, tmp_path / "out-es", language="es", source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    en2 = run(root, binary, tmp_path / "out-en2", language="en", source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    assert en["status"] == es["status"] == en2["status"] == "REUSE_NONCOMPLIANT"
    assert en["report_sha256"] == es["report_sha256"] == en2["report_sha256"]
    assert Path(en["guide_path"]).read_text(encoding="utf-8") != Path(es["guide_path"]).read_text(encoding="utf-8")
    assert Path(en["raw_report_path"]).read_text(encoding="utf-8") == Path(es["raw_report_path"]).read_text(encoding="utf-8")


def test_raw_report_is_separated_from_sanitized_report(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    binary = fake_reuse(tmp_path, payload(compliant=False), returncode=1)
    result = run(root, binary, tmp_path / "out", language="en", source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    sanitized = Path(result["report_path"]).read_text(encoding="utf-8")
    raw = Path(result["raw_report_path"]).read_text(encoding="utf-8")
    assert "private/name.py" not in sanitized
    assert "private/name.py" in raw
    assert str(root) not in sanitized


def test_audit_does_not_mutate_repository(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    binary = fake_reuse(tmp_path, payload())
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    audit(root, binary, source_revision=REV, dependency_lock_sha256=LOCK_SHA)
    after = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    assert before == after


def test_source_uses_fixed_shell_false_subprocess_and_no_network_client() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts" / "p056_license_compliance.py").read_text(encoding="utf-8")
    assert "shell=False" in source
    assert '[str(reuse_bin), "lint", "--json"]' in source
    forbidden = ["shell=True", "os.system(", "import requests", "urllib.request", "http.client", "socket."]
    for token in forbidden:
        assert token not in source
