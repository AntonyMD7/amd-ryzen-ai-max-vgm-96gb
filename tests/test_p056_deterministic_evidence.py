from __future__ import annotations

import json
from pathlib import Path
import stat
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p056_license_compliance_v0111 import audit, run  # noqa: E402

LOCK_SHA = "a" * 64
REV = "1" * 40


def payload() -> dict:
    return {
        "lint_version": "1.0",
        "reuse_spec_version": "3.3",
        "reuse_tool_version": "6.2.0",
        "non_compliant": {
            "bad_licenses": [],
            "deprecated_licenses": [],
            "licenses_without_extension": [],
            "missing_licenses": ["MIT"],
            "unused_licenses": [],
            "read_errors": [],
            "missing_copyright_info": ["private/a.py", "private/b.py"],
            "missing_licensing_info": ["private/a.py", "private/b.py"],
        },
        "files": [
            {"path": "private/a.py", "copyright": "Private Person A"},
            {"path": "private/b.py", "copyright": "Private Person B"},
        ],
        "summary": {
            "used_licenses": ["MIT", "Apache-2.0"],
            "files_total": 2,
            "files_with_copyright_info": 0,
            "files_with_licensing_info": 0,
            "compliant": False,
        },
        "recommendations": ["fix private/a.py", "fix private/b.py"],
    }


def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    (root / "README.md").write_text("hello\n", encoding="utf-8")
    return root


def fake_reuse(tmp_path: Path, name: str, raw_json: str) -> Path:
    directory = tmp_path / name
    directory.mkdir()
    binary = directory / "reuse"
    script = f'''#!/usr/bin/env python3
import sys
if sys.argv[1:] == ["--version"]:
    print("reuse 6.2.0")
    raise SystemExit(0)
if sys.argv[1:] == ["lint", "--json"]:
    print({raw_json!r})
    raise SystemExit(1)
raise SystemExit(91)
'''
    binary.write_text(script, encoding="utf-8")
    binary.chmod(binary.stat().st_mode | stat.S_IXUSR)
    return binary


def test_semantically_equivalent_upstream_serializations_have_one_dais_identity(tmp_path: Path) -> None:
    root = repo(tmp_path)
    p = payload()
    raw_a = json.dumps(p, sort_keys=False, separators=(",", ":"))
    # Change object serialization order and privacy-sensitive list order without
    # changing the bounded semantic counts/state that DAIS is allowed to retain.
    p2 = dict(reversed(list(p.items())))
    p2["non_compliant"] = dict(reversed(list(p["non_compliant"].items())))
    p2["non_compliant"]["missing_copyright_info"] = list(reversed(p["non_compliant"]["missing_copyright_info"]))
    p2["non_compliant"]["missing_licensing_info"] = list(reversed(p["non_compliant"]["missing_licensing_info"]))
    p2["files"] = list(reversed(p["files"]))
    p2["summary"] = dict(reversed(list(p["summary"].items())))
    p2["summary"]["used_licenses"] = list(reversed(p["summary"]["used_licenses"]))
    p2["recommendations"] = list(reversed(p["recommendations"]))
    raw_b = json.dumps(p2, indent=4, sort_keys=False)

    report_a, raw_bytes_a, raw_sha_a = audit(
        root, fake_reuse(tmp_path, "a", raw_a), source_revision=REV, dependency_lock_sha256=LOCK_SHA
    )
    report_b, raw_bytes_b, raw_sha_b = audit(
        root, fake_reuse(tmp_path, "b", raw_b), source_revision=REV, dependency_lock_sha256=LOCK_SHA
    )

    assert raw_bytes_a != raw_bytes_b
    assert raw_sha_a != raw_sha_b
    assert report_a == report_b
    assert report_a["product"]["version"] == "0.11.1"
    assert report_a["authority"]["evidence_identity_profile"] == "semantic-v1"
    assert report_a["source"]["raw_reuse_report_sha256_in_deterministic_record"] is False
    assert "raw_reuse_report_sha256" not in report_a["source"]
    encoded = json.dumps(report_a)
    assert "private/a.py" not in encoded
    assert "Private Person A" not in encoded
    assert '"MIT"' not in encoded
    assert '"Apache-2.0"' not in encoded


def test_repeated_runs_emit_same_report_digest_but_distinct_raw_digest_when_bytes_differ(tmp_path: Path) -> None:
    root = repo(tmp_path)
    p = payload()
    raw_a = json.dumps(p, separators=(",", ":"))
    raw_b = json.dumps(p, indent=2)
    a = run(
        root,
        fake_reuse(tmp_path, "run-a", raw_a),
        tmp_path / "out-a",
        language="en",
        source_revision=REV,
        dependency_lock_sha256=LOCK_SHA,
    )
    b = run(
        root,
        fake_reuse(tmp_path, "run-b", raw_b),
        tmp_path / "out-b",
        language="es",
        source_revision=REV,
        dependency_lock_sha256=LOCK_SHA,
    )
    assert a["report_sha256"] == b["report_sha256"]
    assert a["raw_report_sha256"] != b["raw_report_sha256"]
    assert Path(a["report_path"]).read_bytes() == Path(b["report_path"]).read_bytes()
    assert Path(a["guide_path"]).read_text() != Path(b["guide_path"]).read_text()


def test_action_uses_patch_profile_and_exposes_separate_raw_identity() -> None:
    action = (Path(__file__).resolve().parents[1] / ".github" / "actions" / "license-compliance" / "action.yml").read_text()
    assert "p056_license_compliance_v0111.py" in action
    assert "raw-report-sha256" in action
    assert "deterministic privacy-minimized DAIS semantic evidence" in action
