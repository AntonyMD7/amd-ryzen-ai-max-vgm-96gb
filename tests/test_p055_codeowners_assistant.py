from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from p055_codeowners_assistant import AuditError, audit, run  # noqa: E402


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_is_honest_not_success(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    report = audit(root)
    assert report["status"] == "CODEOWNERS_MISSING"
    assert report["source"]["effective_path"] is None
    assert report["claims"]["comprehensive_repository_coverage_proven"] is False
    assert report["execution"]["repository_mutation_performed"] is False


def test_github_precedence_and_lower_files_are_reported(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, "CODEOWNERS", "* @root-owner\n")
    write(root, "docs/CODEOWNERS", "* @docs-owner\n")
    write(root, ".github/CODEOWNERS", "* @global-owner\n/.github/ @security-owner\n")
    report = audit(root)
    assert report["source"]["effective_path"] == ".github/CODEOWNERS"
    assert report["source"]["ignored_lower_precedence_paths"] == ["CODEOWNERS", "docs/CODEOWNERS"]
    assert report["security"]["explicit_codeowners_self_protection_found"] is True
    assert any(f["code"] == "LOWER_PRECEDENCE_FILES_IGNORED" for f in report["findings"])


def test_supported_local_baseline_and_privacy_minimized_rules(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, ".github/CODEOWNERS", "# owners\n* @global-owner\n/.github/ @org/security\n/docs/ person@example.com\n")
    report = audit(root)
    assert report["status"] == "CODEOWNERS_LOCAL_BASELINE_READY"
    assert report["metrics"]["rules"] == 3
    assert report["metrics"]["user_tokens"] == 1
    assert report["metrics"]["team_tokens"] == 1
    assert report["metrics"]["email_tokens"] == 1
    serialized = json.dumps(report)
    assert "global-owner" not in serialized
    assert "org/security" not in serialized
    assert "person@example.com" not in serialized
    assert all(set(r) == {"line", "pattern_sha256", "owner_count", "owner_kinds", "locally_invalid"} for r in report["rules"])


def test_unsupported_github_syntax_and_bad_owner_fail_local_baseline(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(
        root,
        ".github/CODEOWNERS",
        "!secret/ @owner\n"
        "src/[ab].py @owner\n"
        r"\#literal @owner" + "\n"
        "docs/ not-an-owner\n",
    )
    report = audit(root)
    assert report["status"] == "CODEOWNERS_LOCAL_ERRORS"
    codes = {f["code"] for f in report["findings"]}
    assert {"UNSUPPORTED_NEGATION", "UNSUPPORTED_CHARACTER_RANGE", "UNSUPPORTED_ESCAPED_HASH", "INVALID_OWNER_TOKEN_LOCAL"} <= codes
    assert report["claims"]["github_server_syntax_verified"] is False


def test_duplicate_exact_pattern_warns_about_order(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, ".github/CODEOWNERS", "* @a\n/.github/ @a\n*.py @a\n*.py @b\n")
    report = audit(root)
    assert report["status"] == "CODEOWNERS_NEEDS_REVIEW"
    dup = [f for f in report["findings"] if f["code"] == "DUPLICATE_EXACT_PATTERN"]
    assert len(dup) == 1 and dup[0]["line"] == 4


def test_self_protection_absence_is_warning_not_security_claim(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, ".github/CODEOWNERS", "src/ @dev\n")
    report = audit(root)
    assert report["security"]["explicit_codeowners_self_protection_found"] is False
    assert any(f["code"] == "SELF_PROTECTION_NOT_PROVEN" for f in report["findings"])
    assert report["claims"]["repository_security_guaranteed"] is False


def test_symlink_candidate_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.write_text("* @owner\n", encoding="utf-8")
    (root / ".github").mkdir()
    (root / ".github" / "CODEOWNERS").symlink_to(outside)
    with pytest.raises(AuditError, match="symlink"):
        audit(root)


def test_oversized_candidate_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    p = write(root, "CODEOWNERS", "x")
    p.write_bytes(b"x" * (1024 * 1024 + 1))
    with pytest.raises(AuditError, match="exceeds"):
        audit(root)


def test_output_must_be_outside_repository(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, "CODEOWNERS", "* @owner\n")
    with pytest.raises(AuditError, match="outside"):
        run(root, "en", root / "evidence")


def test_en_es_share_truth_state_and_report_is_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, ".github/CODEOWNERS", "* @owner\n/.github/ @owner\n")
    en = run(root, "en", tmp_path / "en")
    es = run(root, "es", tmp_path / "es")
    en2 = run(root, "en", tmp_path / "en2")
    assert en["status"] == es["status"] == en2["status"]
    assert en["report_sha256"] == es["report_sha256"] == en2["report_sha256"]
    assert Path(en["guide_path"]).read_text() != Path(es["guide_path"]).read_text()
    raw = Path(en["report_path"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == en["report_sha256"]
    assert str(root) not in raw.decode("utf-8")


def test_report_never_promotes_server_side_or_policy_claims(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    write(root, "CODEOWNERS", "* @owner\n")
    report = audit(root)
    assert all(value is False for value in report["claims"].values())
    assert all(value is False for value in report["execution"].values())


def test_source_has_no_network_or_subprocess_executor() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts" / "p055_codeowners_assistant.py").read_text(encoding="utf-8")
    forbidden = ["import requests", "urllib.request", "http.client", "subprocess.", "os.system(", "socket."]
    for token in forbidden:
        assert token not in source
