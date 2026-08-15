import hashlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from safefix_bundle_sandbox import (  # noqa: E402
    apply_text_bundle,
    inspect_bundle_recovery,
    rollback_bundle,
)
from safefix_sandbox import RECOVERY_DIR, SandboxSafeFixError  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sandbox(tmp_path: Path) -> Path:
    (tmp_path / ".safefix-sandbox").write_text("acceptance only\n", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a-before\n", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "b.txt").write_text("b-before\n", encoding="utf-8")
    return tmp_path


def test_two_target_commit_and_exact_bundle_rollback(tmp_path):
    root = sandbox(tmp_path)
    result = apply_text_bundle(
        root,
        {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
        transaction_id="bundle-commit",
        approval_present=True,
    )
    assert result["status"] == "BUNDLE_MUTATION_ATTESTED"
    assert result["target_count"] == 2
    assert result["all_recovery_snapshots_prepared_before_first_write"] is True
    assert result["production_atomicity_proven"] is False
    assert result["power_loss_atomicity_proven"] is False
    assert (root / "a.txt").read_text() == "a-after\n"
    assert (root / "nested/b.txt").read_text() == "b-after\n"

    restored = rollback_bundle(root, transaction_id="bundle-commit")
    assert restored["status"] == "BUNDLE_ROLLBACK_ATTESTED"
    assert restored["all_snapshots_verified_before_first_restore_write"] is True
    assert (root / "a.txt").read_text() == "a-before\n"
    assert (root / "nested/b.txt").read_text() == "b-before\n"


def test_simulated_interruption_exposes_truthful_mixed_state_then_recovers(tmp_path):
    root = sandbox(tmp_path)
    with pytest.raises(SandboxSafeFixError, match="simulated interruption"):
        apply_text_bundle(
            root,
            {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
            transaction_id="bundle-interrupt",
            approval_present=True,
            simulate_interrupt_after_writes=1,
        )

    inspected = inspect_bundle_recovery(root, transaction_id="bundle-interrupt")
    assert inspected["journal_phase"] == "PARTIAL_COMMIT"
    assert inspected["writes_completed"] == 1
    states = {item["relative_path"]: item["observed_state"] for item in inspected["target_states"]}
    assert sorted(states.values()) == ["BEFORE_STATE_PRESENT", "DESIRED_STATE_PRESENT"]
    assert inspected["production_atomicity_proven"] is False

    rollback_bundle(root, transaction_id="bundle-interrupt")
    assert (root / "a.txt").read_text() == "a-before\n"
    assert (root / "nested/b.txt").read_text() == "b-before\n"


def test_corrupt_snapshot_refuses_before_any_restore_write(tmp_path):
    root = sandbox(tmp_path)
    with pytest.raises(SandboxSafeFixError, match="simulated interruption"):
        apply_text_bundle(
            root,
            {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
            transaction_id="bundle-corrupt",
            approval_present=True,
            simulate_interrupt_after_writes=1,
        )

    before_attempt_a = (root / "a.txt").read_bytes()
    before_attempt_b = (root / "nested/b.txt").read_bytes()
    snapshot = root / RECOVERY_DIR / "bundle-corrupt" / "snapshots" / "nested" / "b.txt"
    snapshot.write_text("corrupted snapshot\n", encoding="utf-8")

    with pytest.raises(SandboxSafeFixError, match="snapshot digest mismatch"):
        rollback_bundle(root, transaction_id="bundle-corrupt")

    assert (root / "a.txt").read_bytes() == before_attempt_a
    assert (root / "nested/b.txt").read_bytes() == before_attempt_b


def test_missing_approval_has_no_recovery_state_and_no_mutation(tmp_path):
    root = sandbox(tmp_path)
    before_a = (root / "a.txt").read_bytes()
    before_b = (root / "nested/b.txt").read_bytes()
    with pytest.raises(SandboxSafeFixError, match="approval"):
        apply_text_bundle(
            root,
            {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
            transaction_id="bundle-no-approval",
            approval_present=False,
        )
    assert (root / "a.txt").read_bytes() == before_a
    assert (root / "nested/b.txt").read_bytes() == before_b
    assert not (root / RECOVERY_DIR / "bundle-no-approval").exists()


def test_precondition_mismatch_fails_before_recovery_or_mutation(tmp_path):
    root = sandbox(tmp_path)
    before_a = (root / "a.txt").read_bytes()
    with pytest.raises(SandboxSafeFixError, match="precondition failed"):
        apply_text_bundle(
            root,
            {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
            transaction_id="bundle-precondition",
            approval_present=True,
            expected_before_sha256={"a.txt": "0" * 64},
        )
    assert (root / "a.txt").read_bytes() == before_a
    assert not (root / RECOVERY_DIR / "bundle-precondition").exists()


def test_valid_preconditions_commit(tmp_path):
    root = sandbox(tmp_path)
    before_a = (root / "a.txt").read_bytes()
    before_b = (root / "nested/b.txt").read_bytes()
    result = apply_text_bundle(
        root,
        {"a.txt": "a-after\n", "nested/b.txt": "b-after\n"},
        transaction_id="bundle-preconditions-pass",
        approval_present=True,
        expected_before_sha256={"a.txt": digest(before_a), "nested/b.txt": digest(before_b)},
    )
    assert result["status"] == "BUNDLE_MUTATION_ATTESTED"


def test_bundle_size_is_bounded(tmp_path):
    root = sandbox(tmp_path)
    with pytest.raises(SandboxSafeFixError, match="2..8"):
        apply_text_bundle(root, {"a.txt": "x"}, transaction_id="one", approval_present=True)


def test_bundle_adapter_has_no_shell_or_subprocess_executor():
    text = (ROOT / "scripts/safefix_bundle_sandbox.py").read_text(encoding="utf-8")
    assert "import subprocess" not in text
    assert "os.system" not in text
    assert "shell=True" not in text
