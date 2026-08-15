# SafeFix Multi-Resource Sandbox Acceptance v0.1

Status: **F-01 IN PROGRESS — disposable recovery acceptance only**

This tranche tests a harder SafeFix failure mode: a change that logically spans more than one resource.

A one-file rollback can be exact while a multi-file operation still leaves a broken mixed state if the process stops after file A changes but before file B changes. `scripts/safefix_bundle_sandbox.py` makes that state explicit and recoverable inside the existing marked SafeFix sandbox.

## Search-before-build

SafeFix is not intended to replace mature platform-native transaction/recovery ecosystems.

- Ansible provides check/diff modes for previewing supported changes, but check mode remains a simulation and module support varies.
- Nix/NixOS retains generations and supports switching/rollback to prior configurations.
- OSTree is built around atomic operating-system deployment transitions and rollback.

Those systems should remain preferred native mechanisms when they fit the target. SafeFix's public-good role is a cross-platform governance/evidence/recovery contract that can wrap specialist mechanisms rather than claiming one generic mutation algorithm is universally atomic.

## Acceptance invariant

For a bundle of 2–8 existing regular text files under an explicit `.safefix-sandbox` root:

```text
validate sandbox + targets + preconditions
        ↓
require explicit approval
        ↓
create recovery snapshot for EVERY target
        ↓
attest EVERY recovery snapshot
        ↓
write PREPARED bundle journal
        ↓
ONLY THEN write first target
        ↓
write/attest targets sequentially
        ↓
COMMITTED or visible PARTIAL_COMMIT
```

The crucial property is not pretend atomicity. The crucial property is that a mixed state is observable and every original resource was snapshotted before the first mutation.

## Deliberate interruption acceptance

`simulate_interrupt_after_writes` exists solely for deterministic sandbox tests. With a two-resource bundle, the acceptance test interrupts after the first durable target write.

`inspect_bundle_recovery()` then must report one `DESIRED_STATE_PRESENT` and one `BEFORE_STATE_PRESENT`, with journal phase `PARTIAL_COMMIT`.

It does not relabel that state as success or failure of the whole repair. It records what is actually present.

## Compensating rollback

Before `rollback_bundle()` restores the first target, it verifies **every retained recovery snapshot** against its before-state digest.

If even one snapshot is corrupted, the entire rollback is refused before any restore write begins. This avoids beginning a compensation sequence whose complete recovery set is already known to be invalid.

After preflight, restores are sequential and every restored digest is attested.

## What is still NOT proven

This harness is intentionally explicit about its limits:

- multi-file writes are not a single atomic filesystem transaction;
- a crash during forward commit can expose mixed state;
- a crash during rollback can expose mixed state;
- no fsync/rename pattern can by itself prove end-to-end power-loss safety across arbitrary filesystems/storage hardware;
- no distributed transaction or cross-host recovery is implemented;
- no package manager, service manager, Windows Registry, firmware, driver, bootloader or device adapter exists here;
- no privilege escalation, shell, subprocess or network executor exists;
- passing hosted CI is not representative production acceptance.

Therefore every result keeps:

```text
production_atomicity_proven = false
power_loss_atomicity_proven = false
distributed_transaction_proven = false
production_safe_to_infer = false
```

## Security/privacy boundary

The harness accepts only caller-supplied relative file paths and desired text inside an explicit sandbox marker. It inherits the existing SafeFix rejection of symlinks, path traversal, control-file targeting and oversized resources.

No credentials, arbitrary commands, environment export, remote host, service, package, registry, firmware or production resource should be used as test input.

## F-01 progression

Together with the existing SafeFix sandbox tranches, F-01 now demonstrates:

- before-state preconditions;
- explicit approval;
- recovery-before-mutation;
- exact digest attestation;
- atomic replacement of an individual regular file;
- PREPARED / COMMITTED / ROLLED_BACK recovery journal states;
- deterministic interruption after durable recovery preparation;
- recovery-corruption refusal;
- visible diverged state;
- bounded multi-resource partial-commit detection and compensating rollback.

F-01 remains **IN PROGRESS**. Dedicated distribution, governed native adapters, representative real-world acceptance, stronger crash/power-loss semantics, external review, versioned release and the rest of the canonical completion contract remain outstanding.
