# SafeFix Sandbox Acceptance v0.2

Status: **IN PROGRESS — sandbox acceptance only**

Canonical roadmap mapping: **F-01 SafeFix** and supporting evidence for **P-211 SafeFix Framework**, **P-213 Evidence-First Automation Library**, and **P-214 Recovery-First Mutation Framework**.

## Why this tranche exists

SafeFix v0.1 already defined the required lifecycle and fail-closed transition gates, but it intentionally had no mutation adapter. That was the correct first safety boundary, but it meant recovery, atomic mutation, idempotency/replay protection, and post-change attestation had not been exercised even in an isolated environment.

This tranche adds a deliberately constrained acceptance adapter that can mutate **only regular files inside an explicitly marked temporary/sandbox directory**. It is not a repair engine and it is not authorized for operating-system, package, service, firmware, network, credential, or production changes.

## Search-before-build / upstream positioning

SafeFix should not recreate mature transaction or configuration-management ecosystems.

- Ansible documents check mode and diff mode for validating what tasks would change before applying them. SafeFix can use similar preview semantics when a future adapter wraps Ansible, but check mode alone is not recovery proof. Source: https://docs.ansible.com/projects/ansible/latest/playbook_guide/playbooks_checkmode.html
- NixOS keeps system generations and supports switching/rolling back to previous generations. SafeFix should treat generation-based rollback as a strong native recovery primitive when operating on NixOS rather than inventing a second rollback store. Sources: https://nixos.org/guides/how-nix-works/ and https://wiki.nixos.org/wiki/Nixos-rebuild
- OSTree/rpm-ostree use deployment-based system updates and retain rollback deployments. A future immutable-host SafeFix adapter should integrate those deployment primitives rather than emulate them with ad-hoc file copies. Sources: https://ostreedev.github.io/ostree/deployment/ and https://coreos.github.io/rpm-ostree/administrator-handbook/

SafeFix's independent value is the **cross-platform governance/evidence contract** around discovery, verification, recovery, approval, mutation, restart when needed, post-state attestation, and publishable evidence. Platform-native transaction engines remain preferred where available.

## Sandbox safety boundary

`scripts/safefix_sandbox.py` refuses to operate unless all of the following are true:

1. The supplied root exists and is not a filesystem root.
2. The root contains an explicit `.safefix-sandbox` marker file.
3. The target is a non-empty relative path beneath that root.
4. The target is an existing regular non-symlink file.
5. The target is at most 1 MiB in this acceptance harness.
6. SafeFix's own marker/recovery paths are not targets.
7. If a before-state digest is supplied, it matches exactly.
8. A real change has explicit approval.
9. Recovery bytes are written and hashed before mutation.
10. Mutation uses an atomic file replacement.
11. The post-state SHA-256 matches the requested content before success is returned.
12. Transaction-ID replay with existing recovery state is refused.

The adapter contains no shell, subprocess, package, service, reboot, network, firmware, registry, privilege-elevation, or arbitrary-command executor.

## Acceptance semantics

The test suite proves the following in an ephemeral CI sandbox:

- an unmarked directory is rejected;
- absent approval fails before mutation or snapshot creation;
- stale before-state digests fail closed;
- the original bytes are captured and hash-attested before mutation;
- the changed bytes are hash-attested after mutation;
- rollback restores the exact original bytes and re-attests them;
- path traversal and symlink escape attempts are rejected;
- no-op requests create no mutation/recovery state;
- transaction replay is refused;
- no subprocess/shell executor has been introduced.

This is **sandbox acceptance**, not a real-world device acceptance test. `production_safe_to_infer` remains `false` in every emitted record.

## Beginner view

> SafeFix now proves that it can make and undo a tiny approved change inside a disposable test folder. It still cannot change your real computer.

## Engineer view

The acceptance adapter is intentionally a narrow reference implementation for lifecycle invariants. It proves snapshot-before-mutate, digest preconditions, explicit approval, atomic replacement, post-state hashing, exact rollback, transaction replay refusal, and sandbox containment. It does not prove operating-system semantics, privilege boundaries, crash consistency across all filesystems, service restart behavior, platform-specific rollback, or multi-resource transactions.

## Security and privacy review

- No network access is required.
- No environment values or credentials are read.
- No arbitrary command strings are accepted.
- No raw machine identity is collected.
- The evidence record contains transaction metadata, relative target path, booleans, timestamps, and SHA-256 digests only.
- Symlinks and sandbox escape paths fail closed.
- Recovery remains local to the marked sandbox.

## Accessibility / multilingual path

The current adapter is a Python reference API, not the final user interface. The final SafeFix distribution must expose the roadmap's Beginner / Intermediate / Engineer views and accessible plain-language rendering through F-06. User-facing strings must be externalized/localizable rather than embedded indefinitely in the execution layer.

## What this does **not** complete

F-01 remains **IN PROGRESS**. The canonical completion contract still requires, as applicable:

- a dedicated public distribution surface rather than only a proving-ground module;
- explicit project-level release/versioning and changelog;
- reproducible packaging/install/use path;
- platform-specific adapters with least privilege and independent threat review;
- recovery primitives appropriate to Windows, Linux and immutable/declarative systems;
- crash/interruption testing;
- real-world acceptance on non-production test systems;
- accessibility and multilingual acceptance;
- external/community review;
- retained release evidence and canonical completion record.

No production or device mutation is authorized by this tranche.
