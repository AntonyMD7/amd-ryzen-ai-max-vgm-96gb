# Start Here — Safe Community Guide

This repository helps owners of **compatible 128 GB AMD Ryzen AI Max systems** inspect and, when explicitly supported by AMD ADLX, change Variable Graphics Memory (VGM) from a 64 GB graphics / 64 GB system allocation to a 96 GB graphics / 32 GB system allocation.

> [!WARNING]
> This does **not** upgrade physical RAM. It reallocates unified memory. The operating system will have roughly 32 GB remaining after a 96 GB graphics carve-out.

## Choose your lane

### Beginner lane

Use this lane if you want a guided, explain-as-you-go sequence.

1. Read `docs/BEGINNER-GUIDE.md`.
2. Run only the **read-only** checks first.
3. Confirm that your machine itself reports a unique `Custom / 96 GB / 32 GB` target.
4. Confirm you have a recovery path before any mutation.
5. Do not run a write step merely because another machine used the same option number.
6. After any approved change and reboot, verify independently with AMD ADLX, Windows, and Task Manager.

### Engineering lane

Use this lane if you want the ABI, vtable, state-machine, evidence, and safety-contract details.

1. Read `docs/VERIFIED_SEQUENCE.md`.
2. Read `docs/TECHNICAL_NOTES.md`.
3. Read `docs/ARCHITECTURE.md`.
4. Validate your own runtime and option set.
5. Preserve evidence before and after any state transition.

## Safety states

- **SAFE / READ ONLY** — discovery, enumeration, compatibility checks, post-change attestation.
- **REVIEW** — prerequisite missing, ambiguous result, unsupported platform, or unexpected state.
- **MUTATING** — the one operation that calls AMD ADLX `SetOption`; requires explicit human approval.
- **VERIFY** — post-reboot attestation only; never silently retries the mutation.

## The governing workflow

```text
DISCOVER -> VERIFY -> PREFLIGHT -> APPROVE -> MUTATE -> REBOOT -> ATTEST
```

A safe implementation must not collapse those stages into one opaque command.

## Stop conditions

Stop and ask for help if any of the following are true:

- your machine does not have 128 GB physical unified memory;
- AMD ADLX reports VGM unsupported;
- no exact `Custom / 96 / 32` target exists;
- more than one target matches;
- your current state is not what the write procedure expects;
- Tailscale/OpenSSH or your chosen recovery path is unavailable;
- Windows security controls would need to be disabled merely to make the procedure run;
- the machine reboots and a previous mutation may already have succeeded.

## Success criteria

A verified 96 GB state should be demonstrated by more than one source. On the reference platform the successful post-reboot state was:

```text
AMD ADLX current option: Custom
AMD ADLX carved memory: 96 GB
AMD ADLX remaining memory: 32 GB
Windows visible memory: ~31.79 GiB
Driver GPU memory: 96 GB
Task Manager dedicated GPU memory: ~95.8 GB
```

The exact displayed GiB values can vary slightly because Windows UI and APIs use different unit conventions.

## Need help?

Open an issue using the repository's support template and include **sanitized read-only output only**. Never post SSH private keys, access tokens, private IP details you do not intend to disclose, account credentials, or personal identifiers.
