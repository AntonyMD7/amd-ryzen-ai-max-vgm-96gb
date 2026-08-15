#!/usr/bin/env python3
"""SafeFix v0.3 sandbox acceptance adapter.

This module proves recovery-first lifecycle mechanics without touching a real
operating system, service, device, package manager, firmware setting, or network.
It will only mutate regular files underneath a directory containing an explicit
``.safefix-sandbox`` marker. It has no shell/command executor.

v0.3 adds a local transaction journal so interrupted sandbox mutations can be
classified and recovery-snapshot corruption is detected before rollback.
It remains an acceptance harness for F-01 SafeFix, not a production repair engine.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
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
    if record.get("schema_version") != "0.3":
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
        "schema_version": "0.3",
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

    if expected_before_sha256 is not None and expected_before_sha256 != before_sha:
        raise SandboxSafeFixError("precondition failed: before-state digest mismatch")

    desired = desired_text.encode("utf-8")
    if len(desired) > MAX_FILE_BYTES:
        raise SandboxSafeFixError("desired content exceeds sandbox acceptance size limit")
    desired_sha = _sha256(desired)

    if desired_sha == before_sha:
        return {
            "schema_version": "0.3",
            "evidence_type": "safefix-sandbox-acceptance",
            "transaction_id": tx,
            "status": "NOOP_ATTESTED",
            "mode": "SANDBOX_ONLY",
            "target": rel.as_posix(),
            "started_at_utc": started,
            "completed_at_utc": _utcnow(),
            "before_sha256": before_sha,
            "after_sha256": before_sha,
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
    recovery_file.parent.mkdir(parents=True, exist_ok=False)
    _atomic_write(recovery_file, before)
    snapshot_sha = _sha256(_read_regular_file(recovery_file))
    if snapshot_sha != before_sha:
        raise SandboxSafeFixError("recovery snapshot attestation failed before mutation")

    manifest: dict[str, Any] = {
        "schema_version": "0.3",
        "transaction_id": tx,
        "target": rel.as_posix(),
        "phase": "PREPARED",
        "prepared_at_utc": _utcnow(),
        "before_sha256": before_sha,
        "desired_sha256": desired_sha,
        "recovery_sha256": snapshot_sha,
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
        "schema_version": "0.3",
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
        "schema_version": "0.3",
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
        "rollback_performed": True,
        "post_rollback_attested": True,
        "production_safe_to_infer": False,
    }
