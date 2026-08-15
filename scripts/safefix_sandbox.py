#!/usr/bin/env python3
"""SafeFix v0.4 sandbox acceptance adapter.

This module proves recovery-first lifecycle mechanics without touching a real
operating system, service, device, package manager, firmware setting, or network.
It will only mutate regular files underneath a directory containing an explicit
``.safefix-sandbox`` marker. It has no shell/command executor.

v0.3 added a local transaction journal so interrupted sandbox mutations can be
classified and recovery-snapshot corruption is detected before rollback.
v0.4 adds explicit Linux parent-directory fsync barriers around durable directory
creation and atomic replacement. This narrows a durability gap but does not prove
power-loss atomicity or production safety on any filesystem or hardware stack.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any


MARKER = ".safefix-sandbox"
RECOVERY_DIR = ".safefix-recovery"
MANIFEST = "transaction.json"
MAX_FILE_BYTES = 1024 * 1024
_TX_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class SandboxSafeFixError(RuntimeError):
    """Raised when a sandbox operation would violate the SafeFix boundary."""


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _durability_profile() -> dict[str, Any]:
    """Describe barriers this adapter can honestly claim on the current host.

    Linux receives a parent-directory fsync after each atomic replace and after
    each newly created recovery-directory entry. Other platforms retain the
    pre-existing file-fsync + atomic-replace behavior but make no directory
    durability claim because Python does not expose one portable contract here.
    """
    linux_directory_fsync = sys.platform.startswith("linux") and hasattr(os, "O_DIRECTORY")
    return {
        "file_fsync_before_replace": True,
        "atomic_replace_requested": True,
        "linux_parent_directory_fsync_after_replace": linux_directory_fsync,
        "linux_parent_directory_fsync_after_recovery_mkdir": linux_directory_fsync,
        "power_loss_atomicity_proven": False,
        "filesystem_specific_crash_consistency_proven": False,
        "hardware_write_cache_durability_proven": False,
    }


def _sync_directory(directory: Path) -> bool:
    """Issue a fail-closed Linux directory fsync barrier when supported.

    A failure is surfaced because silently continuing after an attempted
    durability barrier would overstate the retained evidence. Non-Linux hosts
    return False and the public evidence explicitly records that limitation.
    """
    profile = _durability_profile()
    if not profile["linux_parent_directory_fsync_after_replace"]:
        return False
    flags = os.O_RDONLY | os.O_DIRECTORY
    try:
        fd = os.open(directory, flags)
    except OSError as exc:
        raise SandboxSafeFixError("linux directory durability barrier open failed") from exc
    try:
        os.fsync(fd)
    except OSError as exc:
        raise SandboxSafeFixError("linux directory durability barrier fsync failed") from exc
    finally:
        os.close(fd)
    return True


def _mkdir_recovery_chain(sandbox: Path, directory: Path) -> None:
    """Create a recovery directory path one component at a time.

    On Linux, each new child directory is followed by fsync of its parent so
    the directory-entry creation is not silently treated as durable merely
    because mkdir returned successfully.
    """
    try:
        rel = directory.relative_to(sandbox)
    except ValueError as exc:
        raise SandboxSafeFixError("recovery directory escapes sandbox") from exc

    cursor = sandbox
    for part in rel.parts:
        child = cursor / part
        if child.exists():
            if not child.is_dir() or child.is_symlink():
                raise SandboxSafeFixError("recovery path contains non-directory or symlink component")
        else:
            child.mkdir()
            _sync_directory(cursor)
        cursor = child


def _validated_root(root: str | Path) -> Path:
    p = Path(root).expanduser().resolve(strict=True)
    if p == Path(p.anchor):
        raise SandboxSafeFixError("filesystem root can never be a SafeFix sandbox")
    if not (p / MARKER).is_file():
        raise SandboxSafeFixError(f"sandbox marker missing: {MARKER}")
    return p


def _validated_transaction_id(transaction_id: str) -> str:
    if not _TX_RE.fullmatch(transaction_id):
        raise SandboxSafeFixError("invalid transaction_id")
    return transaction_id


def _validated_target(root: Path, relative_path: str | Path) -> tuple[Path, Path]:
    rel = Path(relative_path)
    if rel.is_absolute() or not rel.parts:
        raise SandboxSafeFixError("target must be a non-empty relative path")
    if any(part in ("", ".", "..") for part in rel.parts):
        raise SandboxSafeFixError("target contains an unsafe path component")
    if rel.parts[0] in (MARKER, RECOVERY_DIR):
        raise SandboxSafeFixError("SafeFix control files cannot be mutation targets")

    cursor = root
    for part in rel.parts:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise SandboxSafeFixError("symlink targets are not permitted")

    resolved = (root / rel).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SandboxSafeFixError("target escapes sandbox root") from exc
    return resolved, rel


def _read_regular_file(path: Path) -> bytes:
    if not path.exists():
        raise SandboxSafeFixError("target must already exist so recovery is provable")
    if not path.is_file() or path.is_symlink():
        raise SandboxSafeFixError("target must be a regular non-symlink file")
    data = path.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise SandboxSafeFixError("target exceeds sandbox acceptance size limit")
    return data


def _atomic_write(path: Path, data: bytes) -> None:
    if len(data) > MAX_FILE_BYTES:
        raise SandboxSafeFixError("desired content exceeds sandbox acceptance size limit")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.safefix-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
        _sync_directory(path.parent)
    finally:
        try:
            Path(tmp_name).unlink(missing_ok=True)
        except OSError:
            pass


def _manifest_path(recovery_root: Path) -> Path:
    return recovery_root / MANIFEST


def _write_manifest(recovery_root: Path, record: dict[str, Any]) -> None:
    payload = json.dumps(record, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _atomic_write(_manifest_path(recovery_root), payload)


def _read_manifest(recovery_root: Path) -> dict[str, Any]:
    path = _manifest_path(recovery_root)
    try:
        record = json.loads(_read_regular_file(path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SandboxSafeFixError("recovery transaction manifest is invalid") from exc
    if record.get("schema_version") not in {"0.3", "0.4"}:
        raise SandboxSafeFixError("unsupported recovery transaction manifest")
    return record


def inspect_recovery(
    root: str | Path,
    relative_path: str | Path,
    *,
    transaction_id: str,
) -> dict[str, Any]:
    """Classify retained recovery state without mutating anything."""
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    target, rel = _validated_target(sandbox, relative_path)
    recovery_root = sandbox / RECOVERY_DIR / tx
    record = _read_manifest(recovery_root)

    if record.get("transaction_id") != tx or record.get("target") != rel.as_posix():
        raise SandboxSafeFixError("recovery manifest identity/target mismatch")

    recovery_file = recovery_root / rel
    recovery = _read_regular_file(recovery_file)
    recovery_sha = _sha256(recovery)
    if recovery_sha != record.get("recovery_sha256"):
        raise SandboxSafeFixError("recovery snapshot digest mismatch; rollback refused")

    current = _read_regular_file(target)
    current_sha = _sha256(current)
    if current_sha == record.get("before_sha256"):
        observed_state = "BEFORE_STATE_PRESENT"
    elif current_sha == record.get("desired_sha256"):
        observed_state = "DESIRED_STATE_PRESENT"
    else:
        observed_state = "DIVERGED_STATE_PRESENT"

    return {
        "schema_version": "0.4",
        "evidence_type": "safefix-sandbox-recovery-inspection",
        "transaction_id": tx,
        "mode": "SANDBOX_ONLY",
        "target": rel.as_posix(),
        "journal_phase": record.get("phase"),
        "observed_state": observed_state,
        "current_sha256": current_sha,
        "before_sha256": record.get("before_sha256"),
        "desired_sha256": record.get("desired_sha256"),
        "recovery_sha256": recovery_sha,
        "durability_barrier_profile": record.get("durability_barrier_profile"),
        "mutation_performed": False,
        "production_safe_to_infer": False,
    }


def apply_text_change(
    root: str | Path,
    relative_path: str | Path,
    desired_text: str,
    *,
    transaction_id: str,
    approval_present: bool,
    expected_before_sha256: str | None = None,
) -> dict[str, Any]:
    """Apply one text-file change inside an explicitly marked sandbox."""
    started = _utcnow()
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    target, rel = _validated_target(sandbox, relative_path)
    before = _read_regular_file(target)
    before_sha = _sha256(before)
    durability = _durability_profile()

    if expected_before_sha256 is not None and expected_before_sha256 != before_sha:
        raise SandboxSafeFixError("precondition failed: before-state digest mismatch")

    desired = desired_text.encode("utf-8")
    if len(desired) > MAX_FILE_BYTES:
        raise SandboxSafeFixError("desired content exceeds sandbox acceptance size limit")
    desired_sha = _sha256(desired)

    if desired_sha == before_sha:
        return {
            "schema_version": "0.4",
            "evidence_type": "safefix-sandbox-acceptance",
            "transaction_id": tx,
            "status": "NOOP_ATTESTED",
            "mode": "SANDBOX_ONLY",
            "target": rel.as_posix(),
            "started_at_utc": started,
            "completed_at_utc": _utcnow(),
            "before_sha256": before_sha,
            "after_sha256": before_sha,
            "durability_barrier_profile": durability,
            "mutation_performed": False,
            "approval_present": bool(approval_present),
            "recovery_snapshot_created": False,
            "post_change_attested": True,
            "production_safe_to_infer": False,
        }

    if not approval_present:
        raise SandboxSafeFixError("mutation blocked: explicit approval is absent")

    recovery_root = sandbox / RECOVERY_DIR / tx
    recovery_file = recovery_root / rel
    if recovery_root.exists():
        raise SandboxSafeFixError("transaction_id already has recovery state; replay refused")
    _mkdir_recovery_chain(sandbox, recovery_file.parent)
    _atomic_write(recovery_file, before)
    snapshot_sha = _sha256(_read_regular_file(recovery_file))
    if snapshot_sha != before_sha:
        raise SandboxSafeFixError("recovery snapshot attestation failed before mutation")

    manifest: dict[str, Any] = {
        "schema_version": "0.4",
        "transaction_id": tx,
        "target": rel.as_posix(),
        "phase": "PREPARED",
        "prepared_at_utc": _utcnow(),
        "before_sha256": before_sha,
        "desired_sha256": desired_sha,
        "recovery_sha256": snapshot_sha,
        "durability_barrier_profile": durability,
        "production_safe_to_infer": False,
    }
    _write_manifest(recovery_root, manifest)

    _atomic_write(target, desired)
    after = _read_regular_file(target)
    after_sha = _sha256(after)
    if after_sha != desired_sha:
        _atomic_write(target, before)
        restored_sha = _sha256(_read_regular_file(target))
        raise SandboxSafeFixError(
            "post-change attestation failed; rollback attempted; "
            f"restored={restored_sha == before_sha}"
        )

    manifest.update({"phase": "COMMITTED", "committed_at_utc": _utcnow(), "after_sha256": after_sha})
    _write_manifest(recovery_root, manifest)

    return {
        "schema_version": "0.4",
        "evidence_type": "safefix-sandbox-acceptance",
        "transaction_id": tx,
        "status": "MUTATION_ATTESTED",
        "mode": "SANDBOX_ONLY",
        "target": rel.as_posix(),
        "started_at_utc": started,
        "completed_at_utc": _utcnow(),
        "before_sha256": before_sha,
        "desired_sha256": desired_sha,
        "recovery_sha256": snapshot_sha,
        "after_sha256": after_sha,
        "journal_phase": "COMMITTED",
        "durability_barrier_profile": durability,
        "mutation_performed": True,
        "approval_present": True,
        "recovery_snapshot_created": True,
        "post_change_attested": True,
        "rollback_available": True,
        "production_safe_to_infer": False,
    }


def rollback(
    root: str | Path,
    relative_path: str | Path,
    *,
    transaction_id: str,
) -> dict[str, Any]:
    """Restore a target from its integrity-checked sandbox snapshot."""
    started = _utcnow()
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    target, rel = _validated_target(sandbox, relative_path)
    recovery_root = sandbox / RECOVERY_DIR / tx
    manifest = _read_manifest(recovery_root)
    if manifest.get("transaction_id") != tx or manifest.get("target") != rel.as_posix():
        raise SandboxSafeFixError("recovery manifest identity/target mismatch")

    recovery_file = recovery_root / rel
    recovery = _read_regular_file(recovery_file)
    recovery_sha = _sha256(recovery)
    if recovery_sha != manifest.get("recovery_sha256") or recovery_sha != manifest.get("before_sha256"):
        raise SandboxSafeFixError("recovery snapshot digest mismatch; rollback refused")

    current = _read_regular_file(target)
    current_sha = _sha256(current)
    _atomic_write(target, recovery)
    restored_sha = _sha256(_read_regular_file(target))
    if restored_sha != recovery_sha:
        raise SandboxSafeFixError("rollback attestation failed")

    manifest.update({
        "phase": "ROLLED_BACK",
        "rolled_back_at_utc": _utcnow(),
        "pre_rollback_sha256": current_sha,
        "restored_sha256": restored_sha,
    })
    _write_manifest(recovery_root, manifest)

    return {
        "schema_version": "0.4",
        "evidence_type": "safefix-sandbox-rollback",
        "transaction_id": tx,
        "status": "ROLLBACK_ATTESTED",
        "mode": "SANDBOX_ONLY",
        "target": rel.as_posix(),
        "started_at_utc": started,
        "completed_at_utc": _utcnow(),
        "pre_rollback_sha256": current_sha,
        "recovery_sha256": recovery_sha,
        "restored_sha256": restored_sha,
        "journal_phase": "ROLLED_BACK",
        "durability_barrier_profile": manifest.get("durability_barrier_profile"),
        "rollback_performed": True,
        "post_rollback_attested": True,
        "production_safe_to_infer": False,
    }
