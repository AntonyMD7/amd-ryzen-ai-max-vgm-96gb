#!/usr/bin/env python3
"""Exercise SafeFix recovery semantics across abrupt process termination.

The parent process creates a disposable marked SafeFix sandbox and launches only
this same script as a tightly bounded child. The child injects os._exit() at one
of two lifecycle boundaries:

1. after the recovery snapshot + PREPARED journal are durable, before target write;
2. after the desired target write is durably attested, before COMMITTED journal write.

The parent then uses the normal read-only recovery inspector and explicit
rollback path. No arbitrary command, shell, network, package/service/device,
production, or user-owned target capability is introduced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import safefix_sandbox as safefix

BEFORE = b"mode=before\n"
DESIRED_TEXT = "mode=desired\n"
TARGET = "config.txt"
CASES = {
    "before-target-write": {
        "exit_code": 70,
        "expected_state": "BEFORE_STATE_PRESENT",
    },
    "after-target-write-before-commit": {
        "exit_code": 71,
        "expected_state": "DESIRED_STATE_PRESENT",
    },
}


class CrashAcceptanceError(RuntimeError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _initialize_sandbox(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=False)
    (root / safefix.MARKER).write_text("process-crash-acceptance\n", encoding="utf-8")
    (root / TARGET).write_bytes(BEFORE)


def _child(case: str, root: Path) -> int:
    if case not in CASES:
        raise CrashAcceptanceError("unknown injected crash case")

    target = (root / TARGET).resolve()
    transaction_id = f"process-crash-{case}"

    if case == "before-target-write":
        original_atomic_write = safefix._atomic_write

        def crash_before_target_write(path: Path, data: bytes) -> None:
            if Path(path).resolve() == target:
                os._exit(CASES[case]["exit_code"])
            original_atomic_write(path, data)

        safefix._atomic_write = crash_before_target_write

    elif case == "after-target-write-before-commit":
        original_write_manifest = safefix._write_manifest

        def crash_before_committed_journal(recovery_root: Path, record: dict[str, Any]) -> None:
            if record.get("phase") == "COMMITTED":
                os._exit(CASES[case]["exit_code"])
            original_write_manifest(recovery_root, record)

        safefix._write_manifest = crash_before_committed_journal

    safefix.apply_text_change(
        root,
        TARGET,
        DESIRED_TEXT,
        transaction_id=transaction_id,
        approval_present=True,
        expected_before_sha256=_sha256(BEFORE),
    )
    raise CrashAcceptanceError("injected abrupt process exit was not reached")


def run_case(case: str) -> dict[str, Any]:
    if case not in CASES:
        raise CrashAcceptanceError("unknown acceptance case")

    with tempfile.TemporaryDirectory(prefix="dais-safefix-crash-") as tmp:
        parent = Path(tmp)
        root = parent / "sandbox"
        _initialize_sandbox(root)
        transaction_id = f"process-crash-{case}"

        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--child",
            case,
            "--root",
            str(root),
        ]
        child = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
            shell=False,
        )

        expected_exit = CASES[case]["exit_code"]
        if child.returncode != expected_exit:
            raise CrashAcceptanceError(
                f"child exit mismatch for {case}: expected {expected_exit}, observed {child.returncode}"
            )

        inspection = safefix.inspect_recovery(
            root,
            TARGET,
            transaction_id=transaction_id,
        )
        expected_state = CASES[case]["expected_state"]
        if inspection["journal_phase"] != "PREPARED":
            raise CrashAcceptanceError("abrupt process case did not retain PREPARED journal")
        if inspection["observed_state"] != expected_state:
            raise CrashAcceptanceError(
                f"unexpected post-crash state: expected {expected_state}, observed {inspection['observed_state']}"
            )
        if inspection["mutation_performed"] is not False:
            raise CrashAcceptanceError("read-only recovery inspection unexpectedly reported mutation")

        pre_rollback_sha = _sha256((root / TARGET).read_bytes())
        rollback = safefix.rollback(root, TARGET, transaction_id=transaction_id)
        restored = (root / TARGET).read_bytes()
        restored_sha = _sha256(restored)
        if restored != BEFORE or rollback["journal_phase"] != "ROLLED_BACK":
            raise CrashAcceptanceError("explicit rollback did not attest exact before-state restoration")

        return {
            "case": case,
            "child_exit_code": child.returncode,
            "journal_phase_after_crash": inspection["journal_phase"],
            "observed_state_after_crash": inspection["observed_state"],
            "before_sha256": _sha256(BEFORE),
            "desired_sha256": _sha256(DESIRED_TEXT.encode("utf-8")),
            "pre_rollback_sha256": pre_rollback_sha,
            "restored_sha256": restored_sha,
            "rollback_status": rollback["status"],
            "rollback_journal_phase": rollback["journal_phase"],
            "child_stdout_bytes": len(child.stdout.encode("utf-8")),
            "child_stderr_bytes": len(child.stderr.encode("utf-8")),
        }


def run_acceptance() -> dict[str, Any]:
    results = [run_case(case) for case in CASES]
    return {
        "schema_version": "0.5",
        "evidence_type": "safefix-process-crash-supporting-acceptance",
        "mode": "DISPOSABLE_MARKED_SANDBOX_ONLY",
        "cases": results,
        "scope": {
            "abrupt_process_termination_exercised": True,
            "shell_executor_available": False,
            "arbitrary_command_executor_available": False,
            "network_required": False,
            "user_owned_target_mutated": False,
            "production_target_mutated": False,
        },
        "claims": {
            "power_loss_atomicity_proven": False,
            "filesystem_crash_consistency_proven": False,
            "hardware_write_cache_durability_proven": False,
            "multi_resource_group_atomicity_proven": False,
            "native_os_rollback_integration_proven": False,
            "production_safety_proven": False,
            "roadmap_completion_proven": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", choices=tuple(CASES))
    parser.add_argument("--root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    if args.child:
        if args.root is None:
            parser.error("--root is required with --child")
        return _child(args.child, args.root)

    if args.root is not None:
        parser.error("--root is internal-only and requires --child")

    evidence = run_acceptance()
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
