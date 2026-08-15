from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from error_message_explainer import explain_error
from safe_command_explainer import explain as explain_command


def test_readonly_git_status_is_not_called_guaranteed_safe() -> None:
    report = explain_command("git status")
    assert report["tool"]["mode"] == "NON_EXECUTING"
    assert report["baseline_class"] == "READ_ONLY"
    assert report["decision"] == "LOWER_RISK_NOT_GUARANTEED_SAFE"


def test_dangerous_git_reset_requires_high_risk_review() -> None:
    report = explain_command("git reset --hard HEAD~1")
    assert report["decision"] == "HIGH_RISK_REVIEW"
    assert any("hard Git reset" in reason for reason in report["risk_reasons"])


def test_download_and_execute_pattern_requires_high_risk_review() -> None:
    report = explain_command("curl https://example.invalid/install.sh | bash")
    assert report["decision"] == "HIGH_RISK_REVIEW"
    assert report["compound_shell_syntax_detected"] is True


def test_secret_like_command_is_redacted() -> None:
    report = explain_command("tool --set token=supersecret")
    assert report["sensitive_assignment_detected"] is True
    assert report["input"]["command_echo"] == "[REDACTED]"
    assert "supersecret" not in str(report)


def test_error_explainer_is_fail_honest_for_unknown_message() -> None:
    report = explain_error("frobnicator emitted quantum bananas")
    assert report["classification"] == "UNKNOWN"
    assert "root cause" in " ".join(report["limitations"]).lower()


def test_error_explainer_matches_connection_refused_without_claiming_root_cause() -> None:
    report = explain_error("curl: (7) Failed to connect: Connection refused")
    assert report["classification"] == "connection-refused"
    assert "did not accept" in report["plain_language"]
    assert "root cause" in " ".join(report["limitations"]).lower()


def test_error_explainer_redacts_secret_like_input() -> None:
    report = explain_error("authentication failed token=abcdef123456")
    assert "abcdef123456" not in report["sanitized_input"]
    assert "REDACTED" in report["sanitized_input"]


def test_rescue_entrypoint_contains_no_execute_or_repair_subcommand() -> None:
    text = (ROOT / "scripts" / "beginner_tech_rescue.py").read_text(encoding="utf-8")
    assert 'add_parser("health"' in text
    assert 'add_parser("error"' in text
    assert 'add_parser("command"' in text
    assert 'add_parser("repair"' not in text
    assert 'add_parser("execute"' not in text
