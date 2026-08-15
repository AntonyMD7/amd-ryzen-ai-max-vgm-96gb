# SafeFix abrupt-process recovery acceptance v0.5

Status: **IN PROGRESS — disposable sandbox supporting acceptance only**  
Canonical foundation: **F-01 SafeFix**

## Purpose

SafeFix already retains recovery state before mutation, classifies PREPARED/COMMITTED/ROLLED_BACK transactions, detects corrupted snapshots, and uses file plus Linux parent-directory durability barriers. This tranche closes a narrower remaining gap: exercise those recovery semantics after the mutating process terminates abruptly rather than raising a normal Python exception.

The acceptance remains deliberately below the operating-system transaction layer. It does not mutate a package manager, service, registry, boot state, firmware, network configuration, device, user file, or production target.

## Search-before-build continuity

SafeFix continues to prefer established native transactional/recovery systems when they fit the target platform. The prior architecture review identifies Nix/NixOS generations, OSTree/rpm-ostree deployments, and Ansible preview/diff semantics as upstream capabilities to integrate rather than reimplement.

This tranche therefore does **not** create another OS transaction engine. It tests the portable recovery/evidence contract around the existing marked file-sandbox reference adapter.

## Two abrupt termination boundaries

A parent acceptance process creates a fresh temporary directory containing the required `.safefix-sandbox` marker and one bounded fixture file. It starts only the same acceptance script as a child process, with `shell=False` and a fixed argument shape.

The child injects `os._exit()` at two lifecycle boundaries:

1. **Before target write** — after the recovery snapshot and `PREPARED` journal have already been written through the normal SafeFix durability path, but before desired bytes reach the target.
2. **After target write, before COMMITTED journal** — after the desired target bytes have passed the normal atomic-write/durability path, but before the journal can advance from `PREPARED` to `COMMITTED`.

`os._exit()` intentionally bypasses Python exception unwinding and normal cleanup in the child. The parent then operates on the retained on-disk state.

## Required observations

For the first crash boundary, the parent requires:

```text
journal_phase = PREPARED
observed_state = BEFORE_STATE_PRESENT
```

For the second crash boundary, the parent requires:

```text
journal_phase = PREPARED
observed_state = DESIRED_STATE_PRESENT
```

That second result is especially important: a stale `PREPARED` journal does not cause SafeFix to pretend the requested mutation never reached the target. The existing read-only inspector derives state from exact before/desired hashes and keeps the ambiguity visible.

Both cases then perform an explicit, integrity-checked rollback and require exact restoration of the original SHA-256 plus a `ROLLED_BACK` journal phase.

## Safety boundary

The harness has no arbitrary command parameter and no shell executor. The only subprocess is the exact same acceptance script invoked by the current Python interpreter. Each case runs in a newly created temporary marked sandbox. The evidence retains only hashes, state labels, child exit codes, and bounded status data; temporary paths and fixture contents are not retained.

No network is required.

## What a PASS proves

A PASS provides supporting evidence that, on the tested hosted process/filesystem environment:

- recovery preparation survived an abrupt child-process exit before target mutation;
- a desired target state written before abrupt exit remained distinguishable from the original state even when the journal still said `PREPARED`;
- the normal read-only recovery inspector could classify both retained states;
- the normal explicit rollback path restored and re-attested the exact before-state in both cases.

## What a PASS does not prove

The following remain hard false:

- power-loss atomicity;
- filesystem-specific crash consistency under kernel/power failure;
- hardware write-cache durability;
- true multi-resource group atomicity;
- native OS rollback integration;
- production safety;
- roadmap completion.

A user-space process crash is materially different from power removal or kernel/filesystem failure. Those must not be inferred from this acceptance.

## Remaining F-01 completion frontier

F-01 remains **IN PROGRESS**. High-value remaining work includes:

- governed adapters around established native transactional/recovery systems rather than general shell execution;
- representative non-production native-adapter acceptance;
- stronger multi-resource recovery semantics without falsely claiming distributed/group atomicity;
- platform/filesystem-specific crash or power-interruption evidence where safely testable;
- security/threat review of recovery storage and authority boundaries;
- accessible beginner/operator flows;
- versioned public distribution/release;
- community acceptance and canonical completion record.

No CI pass from this tranche changes F-01 to COMPLETE.
