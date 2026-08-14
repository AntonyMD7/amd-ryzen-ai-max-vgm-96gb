# Beginner Guide — Ryzen AI Max 96 GB VGM

This guide is intentionally simple. It explains **what** each phase does and **why** it exists without requiring prior knowledge of AMD ADLX, Windows Code Integrity, Python ctypes, or C/C++ vtables.

## What you are changing

On a compatible 128 GB unified-memory Ryzen AI Max system, AMD Variable Graphics Memory can reserve part of the unified memory for graphics.

A common starting state is:

```text
64 GB graphics + 64 GB system
```

The target described by this project is:

```text
96 GB graphics + 32 GB system
```

You are **not adding RAM**. You are changing how the existing 128 GB is allocated.

## Before you begin

You should have:

- a compatible Ryzen AI Max system with 128 GB physical memory;
- current AMD graphics drivers;
- Windows access with administrator capability;
- a way to recover the machine if it reboots or remote access temporarily disappears;
- important files and workloads saved;
- enough confidence to stop if your machine reports results different from the reference case.

## Phase 1 — Discover

Goal: find out what your machine supports without changing anything.

A safe discovery tool should answer:

- Is Variable Graphics Memory supported?
- What is the current VGM allocation?
- What profiles are available?
- Is there exactly one `Custom` profile with `96 GB` carved and `32 GB` remaining?

If the answer to the last question is not an unambiguous **yes**, stop.

## Phase 2 — Verify recovery

Before a change, verify that your recovery services are actually working. The reference case used Windows OpenSSH and Tailscale, both configured to start automatically.

The important principle is not the specific product. The important principle is this:

> Do not deliberately reduce system memory and reboot a remote machine unless you have a tested way back in.

## Phase 3 — Preflight

A professional preflight checks the live state again immediately before a write. It must not rely only on output from an earlier session.

The reference transition required all of these to be true:

```text
VGM supported = true
current carved = 64 GB
current remaining = 64 GB
available target count = 1
target name = Custom
target carved = 96 GB
target remaining = 32 GB
recovery services = healthy
```

If any gate fails, do not continue automatically.

## Phase 4 — Approve

The mutation step should be obvious and separate. A beginner should never have to wonder whether a command is merely inspecting the machine or changing it.

The project uses this distinction:

```text
SAFE / READ ONLY   = no VGM change
MUTATING           = may call SetOption
VERIFY             = confirms state after reboot
```

## Phase 5 — Mutate once

AMD ADLX exposes `IADLXVariableGraphicsMemory::SetOption` for changing the selected VGM profile.

The safe contract is:

- select the target by values, not by a hard-coded menu number;
- verify the live current state again;
- call `SetOption` at most once;
- record that the attempt occurred before the call;
- record the return code;
- do not blindly retry if the connection drops because reboot has started.

## Phase 6 — Reboot

The configuration becomes observable after reboot. During this period remote access can disappear for several minutes.

A disappearing SSH connection after a successful `SetOption` is **not** proof of failure. Treat the state as unknown until the machine returns and can be attested.

## Phase 7 — Attest

After Windows returns, use independent evidence.

The verified reference result was:

```text
WINDOWS_VISIBLE_GIB=31.79
DRIVER_GPU_MEMORY_GIB=96
CURRENT_NAME=Custom
CURRENT_MODE=1
CURRENT_CARVED_GB=96
CURRENT_REMAINING_GB=32
```

Task Manager additionally showed approximately `95.8 GB` dedicated GPU memory.

## Why Task Manager may say 95.8 GB instead of 96 GB

Different Windows components can display memory using decimal GB, binary GiB, driver-reported values, or rounded presentation values. A Task Manager value near 95.8 GB is consistent with the successful 96 GB ADLX configuration observed in the reference case.

## What not to do

Do not:

- disable Secure Boot, VBS, Smart App Control, WDAC, or Code Integrity just to run an unsigned helper;
- assume every Ryzen AI Max machine exposes identical option ordering;
- blindly choose “Option 12” because the reference machine used it;
- rerun a mutation after reboot simply because an earlier SSH command returned an error;
- publish credentials or private infrastructure details in an issue;
- treat a Task Manager screenshot alone as the entire engineering proof.

## Where to go next

For the complete verified sequence, read `VERIFIED_SEQUENCE.md`.

For the ABI and Windows security details, read `TECHNICAL_NOTES.md`.

For the project safety model and component boundaries, read `ARCHITECTURE.md`.
