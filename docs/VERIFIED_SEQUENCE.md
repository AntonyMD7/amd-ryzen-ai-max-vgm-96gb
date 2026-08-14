# Verified 64 GB → 96 GB VGM Sequence

## Scope

This document records the successful reference sequence for changing a compatible 128 GB AMD Ryzen AI Max platform from AMD ADLX **High (64 GB graphics / 64 GB remaining)** to **Custom (96 GB graphics / 32 GB remaining)**.

The sequence is deliberately evidence-first. Values below are observations from the reference system, not universal constants.

## 1. Establish recovery first

Before touching VGM, verify that your recovery mechanisms survive a Windows reboot. The reference machine had both OpenSSH and Tailscale configured with automatic startup and confirmed running.

Record current physical/system-visible memory and ensure someone can reach the console if remote networking fails after reboot.

## 2. Use AMD ADLX for authoritative enumeration

AMD's official ADLX VariableGraphicsMemory sample exposed:

```text
Variable Graphics Memory is supported.
Default option: Minimum
Default carved size: 0.5 GB
Default remaining size: 127.5 GB

Current option: High
Current carved size: 64 GB
Current remaining size: 64 GB
```

It enumerated 12 choices on the reference machine:

| # | Name | Mode | GPU carved | Remaining |
|---:|---|---:|---:|---:|
| 1 | Minimum | 0 | 0.5 GB | 127.5 GB |
| 2 | Medium | 0 | 32 GB | 96 GB |
| 3 | High | 0 | 64 GB | 64 GB |
| 4 | Custom | 1 | 0.5 GB | 127.5 GB |
| 5 | Custom | 1 | 1 GB | 127 GB |
| 6 | Custom | 1 | 2 GB | 126 GB |
| 7 | Custom | 1 | 4 GB | 124 GB |
| 8 | Custom | 1 | 8 GB | 120 GB |
| 9 | Custom | 1 | 16 GB | 112 GB |
| 10 | Custom | 1 | 32 GB | 96 GB |
| 11 | Custom | 1 | 64 GB | 64 GB |
| 12 | Custom | 1 | 96 GB | 32 GB |

**Never select by ordinal alone.** The implementation must locate the unique option whose semantic values are `Name=Custom`, `MemoryCarved=96`, and `MemoryRemaining=32`.

## 3. Application Control finding

A locally compiled ADLX helper was blocked by Windows Code Integrity because it was unsigned. The relevant Code Integrity event identified an Enterprise signing-level policy violation.

This was treated as a security boundary, not an obstacle to disable.

The installed AMD runtime was instead verified as:

```text
ADLX version: 1.5.0.124
Authenticode: Valid
Signer: Microsoft Windows Hardware Compatibility Publisher
```

Python 3.12 was already permitted to execute. `ctypes` successfully loaded `amdadlx64.dll` and located the ADLX exports.

No Smart App Control, Code Integrity, VBS, Secure Boot, or WDAC policy was disabled.

## 4. Extract and verify the ABI

The public ADLX headers established the relevant C ABI.

`IADLXVariableGraphicsMemory` contains:

```text
0 Acquire
1 Release
2 QueryInterface
3 IsSupported
4 GetDefaultOption
5 GetOption
6 GetAvailableOptions
7 SetOption
```

`IADLXVariableGraphicsMemoryOption` contains Name, Mode, MemoryCarved and MemoryRemaining methods after its three base-interface methods.

`IADLXVariableGraphicsMemoryOptionList` exposes the typed `At_OptionList` method used to enumerate options.

The read-only probe intentionally never bound or called VGM vtable slot 7.

## 5. Read-only preflight gates

Immediately before mutation the reference machine passed all of these conditions:

```text
VGM_SUPPORTED=TRUE
CURRENT_NAME=High
CURRENT_CARVED_GB=64
CURRENT_REMAINING_GB=64
AVAILABLE_COUNT=12
TARGET_MATCH_COUNT=1
TARGET_NAME=Custom
TARGET_CARVED_GB=96
TARGET_REMAINING_GB=32
SETOPTION_BOUND=FALSE
SETOPTION_CALLED=FALSE
```

The Windows-visible pre-change memory was approximately `63.79 GiB`.

If any expected gate fails, stop and investigate. Do not coerce the machine into matching this reference system.

## 6. Guard the mutation

The successful transaction enforced these invariants:

- current state must be the expected 64/64 state;
- exactly one semantic 96/32 target must exist;
- the selected target object must be the one discovered during the current enumeration;
- maximum `SetOption` call count = 1;
- write an attempt marker before calling the mutating method;
- log the call count before and after;
- do not retry simply because SSH drops during reboot.

The reference transaction produced:

```text
SETOPTION_CALL_COUNT_BEFORE=0
SETOPTION_ABOUT_TO_BE_CALLED=TRUE
SETOPTION_CALL_COUNT_AFTER=1
SETOPTION_RC=0
SETOPTION_ACCEPTED=TRUE
AMD_TRANSACTION=SUCCESS
WINDOWS_REBOOT_SCHEDULED=TRUE
```

`ADLXTerminate` returned 11 after the accepted mutation on the reference run. This did not negate `SetOption RC=0`; the subsequent reboot and independent post-state attestation determined the actual outcome.

## 7. Expect remote connectivity to disappear

During reboot, the original SSH process may end with a transport failure. That is **not evidence that SetOption failed** when the transaction log already recorded `SETOPTION_RC=0`.

Wait for:

1. the Tailscale node to return;
2. port 22 to reopen;
3. a fresh SSH login to succeed.

Do not issue a second SetOption while state is unknown.

## 8. Post-reboot attestation

The reference machine returned with:

```text
WINDOWS_VISIBLE_GIB=31.79
DRIVER_GPU_MEMORY_GIB=96
CURRENT_NAME=Custom
CURRENT_MODE=1
CURRENT_CARVED_GB=96
CURRENT_REMAINING_GB=32
VGM_SUPPORTED=TRUE
```

Recovery services also returned running/automatic.

The old preflight condition `CURRENT_64_64_GATE` naturally became `FAIL` after success. That is expected: the read-only probe was originally designed to authorize a transition *from* 64/64. For post-attestation, inspect the current values directly rather than treating that pre-change gate as a post-change failure.

## 9. Independent GUI verification

Windows Task Manager → Performance → GPU independently showed approximately:

```text
Dedicated GPU memory: 1.3 / 95.8 GB
Shared GPU memory:    0.3 / 15.9 GB
GPU Memory:           2 / 112 GB
```

The 95.8-versus-96 difference is presentation/unit rounding, not evidence of a different profile.

## 10. What success means

The reference system did not acquire additional physical memory. Its 128 GB unified memory was repartitioned:

```text
Before: 64 GB GPU + 64 GB system
After:  96 GB GPU + 32 GB system
```

That distinction should remain explicit in support discussions and issue reports.
