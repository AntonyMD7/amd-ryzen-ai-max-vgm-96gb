# SafeFix interruption and recovery integrity v0.3

Status: **IN PROGRESS — sandbox interruption acceptance only**  
Canonical foundation: **F-01 SafeFix**.

## Purpose

SafeFix v0.2 proved snapshot-before-mutation, atomic replacement, post-change hashing and exact rollback inside a marked disposable sandbox. This tranche targets the next unresolved safety question: **what evidence remains if execution stops after recovery preparation but before the requested mutation is durably completed?**

The implementation remains a file-only sandbox harness. It does not gain package, service, firmware, registry, network, privilege, reboot or arbitrary-command capability.

## Search-before-build continuity

SafeFix continues to prefer platform-native transactional systems where they already exist. The earlier acceptance record identifies Ansible preview semantics, NixOS generations and OSTree/rpm-ostree deployment rollback as upstream primitives to integrate rather than reimplement. This tranche therefore does not attempt to become an operating-system transaction engine; it hardens the portable evidence/recovery contract around SafeFix's isolated reference adapter.

## Transaction journal

Before the target mutation, SafeFix now retains a sandbox-local transaction manifest containing:

- transaction ID;
- relative target path;
- `PREPARED` phase;
- before-state SHA-256;
- desired-state SHA-256;
- recovery-snapshot SHA-256;
- preparation timestamp;
- explicit `production_safe_to_infer: false`.

Only after the requested target bytes are atomically replaced and re-read with the expected SHA-256 does the journal advance to `COMMITTED`. A successful rollback advances the journal to `ROLLED_BACK`.

## Read-only recovery inspection

`inspect_recovery()` validates transaction identity, target identity and recovery-snapshot integrity without changing the target. It classifies the currently observed target as:

- `BEFORE_STATE_PRESENT`;
- `DESIRED_STATE_PRESENT`; or
- `DIVERGED_STATE_PRESENT`.

This lets a future controller distinguish a prepared-but-not-applied transaction from an applied transaction or an independently changed target before deciding what recovery action to request.

## Corruption boundary

Rollback no longer trusts the retained snapshot merely because it exists. The recovery bytes must hash to both the recorded `recovery_sha256` and the original `before_sha256`. If they do not, rollback fails closed **before the target is written**.

This protects against accidental recovery-file corruption in the acceptance harness. It is not a cryptographic anti-tamper trust system because an attacker able to rewrite both journal and snapshot is outside this sandbox model; F-05 signed evidence/trust profiles are a separate concern.

## Interruption acceptance

The test suite injects a deterministic failure at the target-write boundary **after** the recovery snapshot and `PREPARED` journal are written. It then verifies:

1. the original target remains unchanged;
2. recovery inspection reports `PREPARED` + `BEFORE_STATE_PRESENT`;
3. a subsequent explicit rollback restores/attests the original bytes and advances the journal to `ROLLED_BACK`.

Additional tests verify corrupted recovery snapshots are refused and independently diverged target state is reported without mutation.

## What this proves

Only the isolated file-sandbox lifecycle is exercised. It provides stronger evidence for:

- durable recovery preparation before requested mutation;
- interruption visibility;
- recovery-snapshot integrity checking;
- explicit state classification before recovery;
- fail-closed rollback on corrupted recovery bytes.

## What remains

F-01 remains **IN PROGRESS**. This does not prove crash consistency across every filesystem or power-loss model, multi-file transactions, service/process coordination, OS-native rollback, privilege separation, real-device safety, or production readiness. Those require separately bounded adapters, threat review and acceptance on non-production test systems before any completion claim.
