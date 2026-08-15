from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import safefix_sandbox
from safefix_sandbox import (
    MARKER,
    SandboxSafeFixError,
    apply_text_change,
    inspect_recovery,
    rollback,
)


def _sandbox(tmp_path: Path) -> Path:
    (tmp_path / MARKER).write_text("sandbox acceptance only\n", encoding="utf-8")
    return tmp_path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_refuses_unmarked_directory(tmp_path: Path) -> None:
    target = tmp_path / "config.txt"
    target.write_text("before\n", encoding="utf-8")
    with pytest.raises(SandboxSafeFixError, match="marker"):
        apply_text_change(
            tmp_path,
            "config.txt",
            "after\n",
            transaction_id="tx-001",
            approval_present=True,
        )
    assert target.read_text(encoding="utf-8") == "before\n"


def test_missing_approval_fails_before_mutation_or_recovery(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")
    with pytest.raises(SandboxSafeFixError, match="approval"):
        apply_text_change(
            root,
            "config.txt",
            "after\n",
            transaction_id="tx-002",
            approval_present=False,
        )
    assert target.read_text(encoding="utf-8") == "before\n"
    assert not (root / ".safefix-recovery").exists()


def test_before_digest_precondition_fails_closed(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")
    with pytest.raises(SandboxSafeFixError, match="digest mismatch"):
        apply_text_change(
            root,
            "config.txt",
            "after\n",
            transaction_id="tx-003",
            approval_present=True,
            expected_before_sha256="0" * 64,
        )
    assert target.read_text(encoding="utf-8") == "before\n"
    assert not (root / ".safefix-recovery").exists()


def test_mutation_is_snapshotted_attested_and_rollback_restores_exact_bytes(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "nested" / "config.txt"
    target.parent.mkdir()
    before = b"before\n"
    target.write_bytes(before)

    apply_record = apply_text_change(
        root,
        "nested/config.txt",
        "after\n",
        transaction_id="tx-004",
        approval_present=True,
        expected_before_sha256=_sha(before),
    )

    assert apply_record["status"] == "MUTATION_ATTESTED"
    assert apply_record["mode"] == "SANDBOX_ONLY"
    assert apply_record["mutation_performed"] is True
    assert apply_record["recovery_snapshot_created"] is True
    assert apply_record["post_change_attested"] is True
    assert apply_record["journal_phase"] == "COMMITTED"
    assert apply_record["production_safe_to_infer"] is False
    assert target.read_bytes() == b"after\n"

    recovery_file = root / ".safefix-recovery" / "tx-004" / "nested" / "config.txt"
    assert recovery_file.read_bytes() == before
    manifest = json.loads((root / ".safefix-recovery" / "tx-004" / "transaction.json").read_text())
    assert manifest["phase"] == "COMMITTED"
    assert manifest["recovery_sha256"] == _sha(before)

    inspection = inspect_recovery(root, "nested/config.txt", transaction_id="tx-004")
    assert inspection["journal_phase"] == "COMMITTED"
    assert inspection["observed_state"] == "DESIRED_STATE_PRESENT"
    assert inspection["mutation_performed"] is False

    rollback_record = rollback(root, "nested/config.txt", transaction_id="tx-004")
    assert rollback_record["status"] == "ROLLBACK_ATTESTED"
    assert rollback_record["post_rollback_attested"] is True
    assert rollback_record["journal_phase"] == "ROLLED_BACK"
    assert rollback_record["production_safe_to_infer"] is False
    assert target.read_bytes() == before
    assert rollback_record["restored_sha256"] == _sha(before)


def test_noop_is_attested_without_mutation_or_snapshot(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("same\n", encoding="utf-8")
    record = apply_text_change(
        root,
        "config.txt",
        "same\n",
        transaction_id="tx-005",
        approval_present=False,
    )
    assert record["status"] == "NOOP_ATTESTED"
    assert record["mutation_performed"] is False
    assert record["recovery_snapshot_created"] is False
    assert target.read_text(encoding="utf-8") == "same\n"


def test_rejects_path_escape_and_control_targets(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    (root / "config.txt").write_text("before\n", encoding="utf-8")
    with pytest.raises(SandboxSafeFixError):
        apply_text_change(
            root,
            "../outside.txt",
            "after\n",
            transaction_id="tx-006",
            approval_present=True,
        )
    with pytest.raises(SandboxSafeFixError):
        apply_text_change(
            root,
            MARKER,
            "tamper\n",
            transaction_id="tx-007",
            approval_present=True,
        )


def test_rejects_symlink_target(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = root / "link.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this platform")

    with pytest.raises(SandboxSafeFixError, match="symlink"):
        apply_text_change(
            root,
            "link.txt",
            "changed\n",
            transaction_id="tx-008",
            approval_present=True,
        )
    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_transaction_replay_is_refused(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("v1\n", encoding="utf-8")
    apply_text_change(
        root,
        "config.txt",
        "v2\n",
        transaction_id="tx-009",
        approval_present=True,
    )
    with pytest.raises(SandboxSafeFixError, match="replay refused"):
        apply_text_change(
            root,
            "config.txt",
            "v3\n",
            transaction_id="tx-009",
            approval_present=True,
        )
    assert target.read_text(encoding="utf-8") == "v2\n"


def test_corrupted_recovery_snapshot_is_refused_before_target_mutation(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")
    apply_text_change(
        root,
        "config.txt",
        "after\n",
        transaction_id="tx-010",
        approval_present=True,
    )
    recovery_file = root / ".safefix-recovery" / "tx-010" / "config.txt"
    recovery_file.write_text("corrupted\n", encoding="utf-8")

    with pytest.raises(SandboxSafeFixError, match="recovery snapshot digest mismatch"):
        rollback(root, "config.txt", transaction_id="tx-010")
    assert target.read_text(encoding="utf-8") == "after\n"


def test_interruption_after_prepared_journal_is_detectable_and_recoverable(tmp_path: Path, monkeypatch) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")

    real_atomic_write = safefix_sandbox._atomic_write

    def interrupt_target_write(path: Path, data: bytes) -> None:
        if path == target and data == b"after\n":
            raise OSError("simulated interruption after durable recovery preparation")
        real_atomic_write(path, data)

    monkeypatch.setattr(safefix_sandbox, "_atomic_write", interrupt_target_write)
    with pytest.raises(OSError, match="simulated interruption"):
        apply_text_change(
            root,
            "config.txt",
            "after\n",
            transaction_id="tx-011",
            approval_present=True,
        )

    assert target.read_text(encoding="utf-8") == "before\n"
    inspection = inspect_recovery(root, "config.txt", transaction_id="tx-011")
    assert inspection["journal_phase"] == "PREPARED"
    assert inspection["observed_state"] == "BEFORE_STATE_PRESENT"

    monkeypatch.setattr(safefix_sandbox, "_atomic_write", real_atomic_write)
    record = rollback(root, "config.txt", transaction_id="tx-011")
    assert record["status"] == "ROLLBACK_ATTESTED"
    assert target.read_text(encoding="utf-8") == "before\n"


def test_diverged_current_state_is_reported_without_mutation(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")
    apply_text_change(
        root,
        "config.txt",
        "after\n",
        transaction_id="tx-012",
        approval_present=True,
    )
    target.write_text("third-party-change\n", encoding="utf-8")
    inspection = inspect_recovery(root, "config.txt", transaction_id="tx-012")
    assert inspection["observed_state"] == "DIVERGED_STATE_PRESENT"
    assert target.read_text(encoding="utf-8") == "third-party-change\n"


def test_adapter_has_no_shell_or_subprocess_executor() -> None:
    source = (ROOT / "scripts" / "safefix_sandbox.py").read_text(encoding="utf-8")
    assert "import subprocess" not in source
    assert "os.system(" not in source
    assert "shell=True" not in source
