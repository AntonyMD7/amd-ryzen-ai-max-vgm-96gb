from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import safefix_sandbox
from safefix_sandbox import MARKER, apply_text_change, inspect_recovery, rollback


def _sandbox(tmp_path: Path) -> Path:
    (tmp_path / MARKER).write_text("sandbox acceptance only\n", encoding="utf-8")
    return tmp_path


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def test_durability_profile_never_claims_power_loss_or_filesystem_proof() -> None:
    profile = safefix_sandbox._durability_profile()
    assert profile["file_fsync_before_replace"] is True
    assert profile["atomic_replace_requested"] is True
    assert profile["power_loss_atomicity_proven"] is False
    assert profile["filesystem_specific_crash_consistency_proven"] is False
    assert profile["hardware_write_cache_durability_proven"] is False


def test_atomic_write_requests_parent_directory_barrier(tmp_path: Path, monkeypatch) -> None:
    calls: list[Path] = []

    def record_sync(directory: Path) -> bool:
        calls.append(Path(directory))
        return True

    monkeypatch.setattr(safefix_sandbox, "_sync_directory", record_sync)
    target = tmp_path / "target.txt"
    safefix_sandbox._atomic_write(target, b"durable-ish\n")

    assert target.read_bytes() == b"durable-ish\n"
    assert calls == [tmp_path]


def test_recovery_directory_creation_requests_parent_barrier_for_each_new_entry(
    tmp_path: Path, monkeypatch
) -> None:
    calls: list[Path] = []

    def record_sync(directory: Path) -> bool:
        calls.append(Path(directory))
        return True

    monkeypatch.setattr(safefix_sandbox, "_sync_directory", record_sync)
    target_dir = tmp_path / ".safefix-recovery" / "tx-durable" / "nested"
    safefix_sandbox._mkdir_recovery_chain(tmp_path, target_dir)

    assert target_dir.is_dir()
    assert calls == [
        tmp_path,
        tmp_path / ".safefix-recovery",
        tmp_path / ".safefix-recovery" / "tx-durable",
    ]


def test_success_record_exposes_truthful_durability_profile(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    target.write_text("before\n", encoding="utf-8")

    record = apply_text_change(
        root,
        "config.txt",
        "after\n",
        transaction_id="tx-durability-record",
        approval_present=True,
    )

    profile = record["durability_barrier_profile"]
    assert profile["file_fsync_before_replace"] is True
    assert profile["power_loss_atomicity_proven"] is False
    assert record["production_safe_to_infer"] is False

    inspection = inspect_recovery(root, "config.txt", transaction_id="tx-durability-record")
    assert inspection["durability_barrier_profile"] == profile


def test_v03_prepared_manifest_remains_inspectable_and_recoverable(tmp_path: Path) -> None:
    root = _sandbox(tmp_path)
    target = root / "config.txt"
    before = b"before\n"
    desired = b"after\n"
    target.write_bytes(desired)

    tx = "tx-v03-compat"
    recovery_root = root / ".safefix-recovery" / tx
    recovery_root.mkdir(parents=True)
    recovery_file = recovery_root / "config.txt"
    recovery_file.write_bytes(before)
    manifest = {
        "schema_version": "0.3",
        "transaction_id": tx,
        "target": "config.txt",
        "phase": "COMMITTED",
        "prepared_at_utc": "2026-08-15T00:00:00Z",
        "committed_at_utc": "2026-08-15T00:00:01Z",
        "before_sha256": _sha(before),
        "desired_sha256": _sha(desired),
        "recovery_sha256": _sha(before),
        "after_sha256": _sha(desired),
        "production_safe_to_infer": False,
    }
    (recovery_root / "transaction.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    inspection = inspect_recovery(root, "config.txt", transaction_id=tx)
    assert inspection["journal_phase"] == "COMMITTED"
    assert inspection["observed_state"] == "DESIRED_STATE_PRESENT"
    assert inspection["durability_barrier_profile"] is None

    restored = rollback(root, "config.txt", transaction_id=tx)
    assert restored["status"] == "ROLLBACK_ATTESTED"
    assert restored["durability_barrier_profile"] is None
    assert target.read_bytes() == before


def test_linux_directory_sync_failure_is_fail_closed(tmp_path: Path, monkeypatch) -> None:
    if not (sys.platform.startswith("linux") and hasattr(safefix_sandbox.os, "O_DIRECTORY")):
        pytest.skip("Linux directory fsync acceptance only")

    real_fsync = safefix_sandbox.os.fsync
    directory_fds: set[int] = set()
    real_open = safefix_sandbox.os.open

    def recording_open(path, flags, *args, **kwargs):
        fd = real_open(path, flags, *args, **kwargs)
        if Path(path) == tmp_path:
            directory_fds.add(fd)
        return fd

    def fail_directory_fsync(fd: int) -> None:
        if fd in directory_fds:
            raise OSError("injected directory fsync failure")
        real_fsync(fd)

    monkeypatch.setattr(safefix_sandbox.os, "open", recording_open)
    monkeypatch.setattr(safefix_sandbox.os, "fsync", fail_directory_fsync)

    with pytest.raises(safefix_sandbox.SandboxSafeFixError, match="durability barrier fsync failed"):
        safefix_sandbox._atomic_write(tmp_path / "target.txt", b"after\n")
