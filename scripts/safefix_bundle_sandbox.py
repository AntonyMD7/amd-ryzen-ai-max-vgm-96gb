#!/usr/bin/env python3
"""SafeFix multi-resource sandbox acceptance harness v0.1.

This module extends the existing file-only SafeFix sandbox with a deliberately
bounded *bundle* transaction. It proves that recovery snapshots for every target
can be durably prepared before the first target write, that a partial commit can
be detected after interruption, and that all snapshots are integrity-checked
before compensating rollback begins.

It does NOT provide filesystem-wide atomicity, power-loss atomicity, distributed
transactions, service/package/registry/firmware mutation, or a production repair
engine. Sequential file replacement means a crash can expose a mixed state;
that mixed state is retained and classified rather than hidden.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from safefix_sandbox import (
    RECOVERY_DIR,
    SandboxSafeFixError,
    _atomic_write,
    _read_regular_file,
    _sha256,
    _utcnow,
    _validated_root,
    _validated_target,
    _validated_transaction_id,
)

BUNDLE_MANIFEST = "bundle-transaction.json"
MIN_TARGETS = 2
MAX_TARGETS = 8


def _bundle_root(sandbox: Path, transaction_id: str) -> Path:
    return sandbox / RECOVERY_DIR / transaction_id


def _manifest_path(recovery_root: Path) -> Path:
    return recovery_root / BUNDLE_MANIFEST


def _write_manifest(recovery_root: Path, record: dict[str, Any]) -> None:
    payload = json.dumps(record, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    _atomic_write(_manifest_path(recovery_root), payload)


def _read_manifest(recovery_root: Path) -> dict[str, Any]:
    path = _manifest_path(recovery_root)
    try:
        record = json.loads(_read_regular_file(path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SandboxSafeFixError("bundle recovery manifest is invalid") from exc
    if record.get("schema_version") != "0.1" or record.get("transaction_type") != "SAFEFIX_SANDBOX_BUNDLE":
        raise SandboxSafeFixError("unsupported bundle recovery manifest")
    return record


def _normalize_changes(
    sandbox: Path,
    changes: Mapping[str, str],
    expected_before_sha256: Mapping[str, str] | None,
) -> list[dict[str, Any]]:
    if not isinstance(changes, Mapping):
        raise SandboxSafeFixError("changes must be a mapping of relative path to desired text")
    if not (MIN_TARGETS <= len(changes) <= MAX_TARGETS):
        raise SandboxSafeFixError(f"bundle must contain {MIN_TARGETS}..{MAX_TARGETS} targets")
    expected = dict(expected_before_sha256 or {})
    if set(expected) - set(changes):
        raise SandboxSafeFixError("preconditions contain a target not present in changes")

    prepared: list[dict[str, Any]] = []
    canonical_paths: set[str] = set()
    for raw_path in sorted(changes):
        desired_text = changes[raw_path]
        if not isinstance(raw_path, str) or not isinstance(desired_text, str):
            raise SandboxSafeFixError("bundle paths and desired values must be strings")
        target, rel = _validated_target(sandbox, raw_path)
        rel_name = rel.as_posix()
        if rel_name in canonical_paths:
            raise SandboxSafeFixError("bundle contains duplicate canonical target")
        canonical_paths.add(rel_name)
        before = _read_regular_file(target)
        before_sha = _sha256(before)
        if raw_path in expected and expected[raw_path] != before_sha:
            raise SandboxSafeFixError(f"precondition failed for {rel_name}: before-state digest mismatch")
        desired = desired_text.encode("utf-8")
        # Reuse the bounded writer as the single authoritative size check without
        # actually writing: the existing sandbox limit is checked explicitly here.
        if len(desired) > 1024 * 1024:
            raise SandboxSafeFixError(f"desired content exceeds sandbox size limit: {rel_name}")
        prepared.append(
            {
                "relative_path": rel_name,
                "target": target,
                "before": before,
                "before_sha256": before_sha,
                "desired": desired,
                "desired_sha256": _sha256(desired),
            }
        )
    return prepared


def _validate_recovery_snapshots(
    sandbox: Path,
    recovery_root: Path,
    record: dict[str, Any],
) -> list[dict[str, Any]]:
    manifest_targets = record.get("targets")
    if not isinstance(manifest_targets, list) or not (MIN_TARGETS <= len(manifest_targets) <= MAX_TARGETS):
        raise SandboxSafeFixError("bundle manifest target list is invalid")

    validated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in manifest_targets:
        if not isinstance(item, dict):
            raise SandboxSafeFixError("bundle manifest target entry is invalid")
        rel_name = item.get("relative_path")
        if not isinstance(rel_name, str) or rel_name in seen:
            raise SandboxSafeFixError("bundle manifest target identity is invalid")
        seen.add(rel_name)
        target, rel = _validated_target(sandbox, rel_name)
        if rel.as_posix() != rel_name:
            raise SandboxSafeFixError("bundle manifest target canonicalization mismatch")
        recovery_file = recovery_root / "snapshots" / rel
        recovery = _read_regular_file(recovery_file)
        recovery_sha = _sha256(recovery)
        if recovery_sha != item.get("recovery_sha256") or recovery_sha != item.get("before_sha256"):
            raise SandboxSafeFixError(f"recovery snapshot digest mismatch for {rel_name}; bundle rollback refused")
        desired_sha = item.get("desired_sha256")
        if not isinstance(desired_sha, str) or len(desired_sha) != 64:
            raise SandboxSafeFixError(f"bundle manifest desired digest invalid for {rel_name}")
        validated.append(
            {
                "relative_path": rel_name,
                "target": target,
                "recovery": recovery,
                "before_sha256": item["before_sha256"],
                "desired_sha256": desired_sha,
                "recovery_sha256": recovery_sha,
            }
        )
    return validated


def apply_text_bundle(
    root: str | Path,
    changes: Mapping[str, str],
    *,
    transaction_id: str,
    approval_present: bool,
    expected_before_sha256: Mapping[str, str] | None = None,
    simulate_interrupt_after_writes: int | None = None,
) -> dict[str, Any]:
    """Apply 2..8 bounded text-file changes inside an explicit SafeFix sandbox.

    ``simulate_interrupt_after_writes`` exists only for deterministic acceptance
    testing. When supplied it raises after that many successful target writes and
    leaves the recovery journal/snapshots intact for inspection and rollback.
    """
    started = _utcnow()
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    prepared = _normalize_changes(sandbox, changes, expected_before_sha256)

    if not isinstance(approval_present, bool) or not approval_present:
        raise SandboxSafeFixError("bundle mutation blocked: explicit approval is absent")
    if simulate_interrupt_after_writes is not None:
        if not isinstance(simulate_interrupt_after_writes, int) or not (1 <= simulate_interrupt_after_writes < len(prepared)):
            raise SandboxSafeFixError("simulate_interrupt_after_writes must interrupt after 1..N-1 writes")

    recovery_root = _bundle_root(sandbox, tx)
    if recovery_root.exists():
        raise SandboxSafeFixError("transaction_id already has recovery state; replay refused")
    snapshot_root = recovery_root / "snapshots"
    snapshot_root.mkdir(parents=True, exist_ok=False)

    target_records: list[dict[str, Any]] = []
    for item in prepared:
        rel = Path(item["relative_path"])
        snapshot = snapshot_root / rel
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        _atomic_write(snapshot, item["before"])
        recovery_sha = _sha256(_read_regular_file(snapshot))
        if recovery_sha != item["before_sha256"]:
            raise SandboxSafeFixError(f"recovery snapshot attestation failed before bundle mutation: {item['relative_path']}")
        target_records.append(
            {
                "relative_path": item["relative_path"],
                "before_sha256": item["before_sha256"],
                "desired_sha256": item["desired_sha256"],
                "recovery_sha256": recovery_sha,
            }
        )

    manifest: dict[str, Any] = {
        "schema_version": "0.1",
        "transaction_type": "SAFEFIX_SANDBOX_BUNDLE",
        "transaction_id": tx,
        "phase": "PREPARED",
        "prepared_at_utc": _utcnow(),
        "target_count": len(target_records),
        "writes_completed": 0,
        "targets": target_records,
        "production_atomicity_proven": False,
        "power_loss_atomicity_proven": False,
        "distributed_transaction_proven": False,
        "production_safe_to_infer": False,
    }
    _write_manifest(recovery_root, manifest)

    # Critical invariant: every snapshot + PREPARED manifest exists before the
    # first target write. The writes below remain sequential and non-atomic as a
    # group; the journal makes partial state observable and recoverable.
    writes_completed = 0
    for item in prepared:
        _atomic_write(item["target"], item["desired"])
        observed_sha = _sha256(_read_regular_file(item["target"]))
        if observed_sha != item["desired_sha256"]:
            manifest.update(
                {
                    "phase": "PARTIAL_COMMIT",
                    "writes_completed": writes_completed,
                    "last_error": f"post-write attestation failed: {item['relative_path']}",
                    "last_updated_at_utc": _utcnow(),
                }
            )
            _write_manifest(recovery_root, manifest)
            raise SandboxSafeFixError("bundle post-write attestation failed; explicit bundle rollback required")
        writes_completed += 1
        manifest.update(
            {
                "phase": "PARTIAL_COMMIT" if writes_completed < len(prepared) else "COMMITTED",
                "writes_completed": writes_completed,
                "last_updated_at_utc": _utcnow(),
            }
        )
        if writes_completed == len(prepared):
            manifest["committed_at_utc"] = _utcnow()
        _write_manifest(recovery_root, manifest)

        if simulate_interrupt_after_writes == writes_completed:
            raise SandboxSafeFixError("simulated interruption after durable partial bundle commit")

    return {
        "schema_version": "0.1",
        "evidence_type": "safefix-sandbox-bundle-acceptance",
        "transaction_id": tx,
        "status": "BUNDLE_MUTATION_ATTESTED",
        "mode": "SANDBOX_ONLY",
        "started_at_utc": started,
        "completed_at_utc": _utcnow(),
        "target_count": len(prepared),
        "writes_completed": writes_completed,
        "journal_phase": "COMMITTED",
        "all_recovery_snapshots_prepared_before_first_write": True,
        "all_target_writes_attested": True,
        "rollback_available": True,
        "mutation_performed": True,
        "production_atomicity_proven": False,
        "power_loss_atomicity_proven": False,
        "distributed_transaction_proven": False,
        "production_safe_to_infer": False,
    }


def inspect_bundle_recovery(root: str | Path, *, transaction_id: str) -> dict[str, Any]:
    """Classify every target in a retained bundle without mutation."""
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    recovery_root = _bundle_root(sandbox, tx)
    record = _read_manifest(recovery_root)
    if record.get("transaction_id") != tx:
        raise SandboxSafeFixError("bundle recovery manifest transaction mismatch")
    targets = _validate_recovery_snapshots(sandbox, recovery_root, record)

    states: list[dict[str, str]] = []
    for item in targets:
        current_sha = _sha256(_read_regular_file(item["target"]))
        if current_sha == item["before_sha256"]:
            state = "BEFORE_STATE_PRESENT"
        elif current_sha == item["desired_sha256"]:
            state = "DESIRED_STATE_PRESENT"
        else:
            state = "DIVERGED_STATE_PRESENT"
        states.append(
            {
                "relative_path": item["relative_path"],
                "observed_state": state,
                "current_sha256": current_sha,
            }
        )

    return {
        "schema_version": "0.1",
        "evidence_type": "safefix-sandbox-bundle-recovery-inspection",
        "transaction_id": tx,
        "mode": "SANDBOX_ONLY",
        "journal_phase": record.get("phase"),
        "writes_completed": record.get("writes_completed"),
        "target_states": states,
        "recovery_snapshots_integrity_verified": True,
        "mutation_performed": False,
        "production_atomicity_proven": False,
        "production_safe_to_infer": False,
    }


def rollback_bundle(root: str | Path, *, transaction_id: str) -> dict[str, Any]:
    """Compensate every bundle target from pre-verified snapshots.

    All snapshot digests are verified *before* the first restore write. Restore
    writes are still sequential; production-grade atomic/power-loss semantics are
    explicitly not inferred.
    """
    started = _utcnow()
    sandbox = _validated_root(root)
    tx = _validated_transaction_id(transaction_id)
    recovery_root = _bundle_root(sandbox, tx)
    record = _read_manifest(recovery_root)
    if record.get("transaction_id") != tx:
        raise SandboxSafeFixError("bundle recovery manifest transaction mismatch")

    # Fail closed before any target is restored when any snapshot is corrupt.
    targets = _validate_recovery_snapshots(sandbox, recovery_root, record)
    pre_rollback: dict[str, str] = {
        item["relative_path"]: _sha256(_read_regular_file(item["target"])) for item in targets
    }

    restored: list[dict[str, str]] = []
    for item in targets:
        _atomic_write(item["target"], item["recovery"])
        restored_sha = _sha256(_read_regular_file(item["target"]))
        if restored_sha != item["before_sha256"]:
            raise SandboxSafeFixError(f"bundle rollback attestation failed: {item['relative_path']}")
        restored.append(
            {
                "relative_path": item["relative_path"],
                "pre_rollback_sha256": pre_rollback[item["relative_path"]],
                "restored_sha256": restored_sha,
            }
        )

    record.update(
        {
            "phase": "ROLLED_BACK",
            "rolled_back_at_utc": _utcnow(),
            "restore_writes_completed": len(restored),
        }
    )
    _write_manifest(recovery_root, record)

    return {
        "schema_version": "0.1",
        "evidence_type": "safefix-sandbox-bundle-rollback",
        "transaction_id": tx,
        "status": "BUNDLE_ROLLBACK_ATTESTED",
        "mode": "SANDBOX_ONLY",
        "started_at_utc": started,
        "completed_at_utc": _utcnow(),
        "target_count": len(restored),
        "restored_targets": restored,
        "all_snapshots_verified_before_first_restore_write": True,
        "all_restore_writes_attested": True,
        "journal_phase": "ROLLED_BACK",
        "rollback_performed": True,
        "production_atomicity_proven": False,
        "power_loss_atomicity_proven": False,
        "distributed_transaction_proven": False,
        "production_safe_to_infer": False,
    }
