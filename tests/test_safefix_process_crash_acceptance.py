from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from safefix_process_crash_acceptance import BEFORE, DESIRED_TEXT, run_acceptance, run_case


def test_before_target_write_crash_retains_before_state_and_recovers():
    result = run_case("before-target-write")
    assert result["child_exit_code"] == 70
    assert result["journal_phase_after_crash"] == "PREPARED"
    assert result["observed_state_after_crash"] == "BEFORE_STATE_PRESENT"
    assert result["pre_rollback_sha256"] == result["before_sha256"]
    assert result["restored_sha256"] == result["before_sha256"]
    assert result["rollback_status"] == "ROLLBACK_ATTESTED"
    assert result["rollback_journal_phase"] == "ROLLED_BACK"


def test_after_target_write_before_commit_crash_is_visible_and_recovers():
    result = run_case("after-target-write-before-commit")
    assert result["child_exit_code"] == 71
    assert result["journal_phase_after_crash"] == "PREPARED"
    assert result["observed_state_after_crash"] == "DESIRED_STATE_PRESENT"
    assert result["pre_rollback_sha256"] == result["desired_sha256"]
    assert result["restored_sha256"] == result["before_sha256"]
    assert result["rollback_status"] == "ROLLBACK_ATTESTED"
    assert result["rollback_journal_phase"] == "ROLLED_BACK"


def test_acceptance_preserves_non_claims_and_has_no_user_or_production_mutation():
    evidence = run_acceptance()
    assert evidence["mode"] == "DISPOSABLE_MARKED_SANDBOX_ONLY"
    assert len(evidence["cases"]) == 2
    assert evidence["scope"]["abrupt_process_termination_exercised"] is True
    assert evidence["scope"]["shell_executor_available"] is False
    assert evidence["scope"]["arbitrary_command_executor_available"] is False
    assert evidence["scope"]["network_required"] is False
    assert evidence["scope"]["user_owned_target_mutated"] is False
    assert evidence["scope"]["production_target_mutated"] is False
    assert all(value is False for value in evidence["claims"].values())


def test_public_evidence_does_not_leak_temp_paths_or_file_contents():
    evidence = run_acceptance()
    rendered = repr(evidence)
    assert "dais-safefix-crash-" not in rendered
    assert BEFORE.decode().strip() not in rendered
    assert DESIRED_TEXT.strip() not in rendered


def test_child_process_is_silent_at_abrupt_exit_boundaries():
    for case in ("before-target-write", "after-target-write-before-commit"):
        result = run_case(case)
        assert result["child_stdout_bytes"] == 0
        assert result["child_stderr_bytes"] == 0
