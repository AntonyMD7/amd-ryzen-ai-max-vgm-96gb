# Safety Architecture

This project treats a VGM reconfiguration as a controlled state transition, not as a one-line tweak.

## Governing state machine

```text
DISCOVER -> VERIFY -> PREFLIGHT -> APPROVE -> MUTATE -> REBOOT -> ATTEST
```

Each stage has a different trust level and failure policy.

## 1. DISCOVER

Read-only. Gather platform, driver, ADLX, VGM support, current state, and available options.

Mutation APIs must not be called.

## 2. VERIFY

Read-only. Confirm that the desired target is genuinely exposed by the live AMD runtime and that recovery access exists.

Targets are matched semantically:

```text
name=Custom
carved=96
remaining=32
```

A numeric menu position is evidence only, never the primary selector.

## 3. PREFLIGHT

Read-only and fresh. Re-run critical checks immediately before any mutation. Stale evidence is insufficient for a guarded write.

Fail closed on ambiguity.

## 4. APPROVE

Human authorization boundary. The user must know that the next stage may change VGM and reboot the machine.

No approval should be inferred from merely running discovery tooling.

## 5. MUTATE

The only stage allowed to call AMD ADLX `IADLXVariableGraphicsMemory::SetOption`.

Required controls:

- exact live-state gates;
- unique target match;
- at-most-once call semantics;
- attempt marker written before the call;
- return code captured;
- no automatic retry after transport loss.

## 6. REBOOT

Expected disruptive boundary. Remote connectivity may disappear temporarily. Transport failure during this phase must not be interpreted as mutation failure.

## 7. ATTEST

Strictly read-only. Verify the resulting state independently.

Preferred evidence sources:

1. AMD ADLX current option and carved/remaining values;
2. Windows visible system memory;
3. driver-reported GPU memory;
4. Task Manager visual confirmation.

## Trust boundaries

### AMD runtime

The installed, signed AMD ADLX DLL is the authoritative runtime interface for VGM support and profile enumeration.

### Windows security controls

Smart App Control, WDAC, VBS, Code Integrity, Secure Boot, and similar protections are not prerequisites to disable. If an unsigned helper is blocked, redesign the tooling rather than weakening the host by default.

### Transport

SSH and Tailscale are recovery/observation channels, not evidence that the VGM change itself succeeded. The machine must be re-attested after reboot.

## Evidence model

Every significant run should preserve:

- UTC timestamp;
- host/platform metadata with secrets sanitized;
- runtime version and signature state;
- preflight values;
- target match details;
- mutation call count and return code, if mutation is authorized;
- reboot observation;
- post-reboot attestation;
- cryptographic hashes of evidence artifacts when practical.

## Fail-closed principles

The toolchain should stop when:

- required evidence is missing;
- a target is ambiguous;
- current state differs from the expected transition source;
- recovery prerequisites fail;
- a mutation attempt marker already exists for the active transaction;
- post-reboot state is not yet known.

## Community engineering rule

A contribution that makes the workflow easier must not make the mutation boundary less explicit. Convenience is subordinate to observability, recoverability, and at-most-once semantics.
