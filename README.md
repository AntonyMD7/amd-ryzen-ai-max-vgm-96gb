# AMD Ryzen AI Max — 96 GB Variable Graphics Memory (VGM)

A field-tested, evidence-driven guide for configuring supported **AMD Ryzen AI Max / Radeon integrated graphics systems with 128 GB unified physical memory** from a 64 GB graphics-memory profile to AMD ADLX's **Custom 96 GB graphics / 32 GB system** profile.

> [!IMPORTANT]
> This repository does **not** add physical RAM. It changes AMD **Variable Graphics Memory (VGM)** allocation on compatible 128 GB systems. After the verified transition described here, Windows exposed about **31.79 GiB** system-visible memory and the AMD graphics driver exposed **96 GB dedicated GPU memory**.

## Verified reference result

On the reference Ryzen AI Max platform, AMD ADLX 1.5.0.124 reported:

```text
BEFORE
Current option: High
GPU carved:     64 GB
System remain:  64 GB
Windows visible: 63.79 GiB

TARGET
Option 12: Custom
GPU carved:     96 GB
System remain:  32 GB

AFTER REBOOT
Current option: Custom
GPU carved:     96 GB
System remain:  32 GB
Windows visible: 31.79 GiB
Driver GPU memory: 96 GB
```

Windows Task Manager independently displayed approximately **95.8 GB dedicated GPU memory** (binary-unit/display rounding) and approximately **112 GB total GPU memory** when shared GPU memory was included.

## Why this repository exists

The difficult part was not discovering that a 96 GB profile existed. The difficult part was changing it **without guessing**, while preserving remote recovery and producing evidence that the requested profile was actually supported by the installed AMD runtime.

The successful workflow was:

1. Establish remote recovery (Tailscale + OpenSSH) before changing memory allocation.
2. Inspect AMD's official ADLX `VariableGraphicsMemory` sample in read-only mode.
3. Enumerate all VGM options and confirm a unique `Custom / 96 GB / 32 GB` target.
4. Preserve Windows application-control protections rather than disabling them.
5. Use the installed, Microsoft-signed AMD ADLX runtime.
6. Gate the write on the observed current state and exact target.
7. Invoke `IADLXVariableGraphicsMemory::SetOption` **once**.
8. Reboot Windows.
9. Reconnect and independently attest Windows memory, driver memory, and ADLX current state.
10. Never blindly retry a successful `SetOption` after the SSH connection disappears during reboot.

## Compatibility

This is intended for compatible AMD systems where the installed ADLX runtime reports Variable Graphics Memory support and explicitly enumerates the desired 96/32 profile.

**Do not assume Option 12 is 96 GB on another machine.** Enumerate and match by semantic values (`Custom`, `96`, `32`) before any write.

The reference system reported 12 options including Minimum, Medium, High, and Custom allocations from 0.5 GB through 96 GB.

## Safety model

The repository deliberately separates **discovery**, **preflight**, **mutation**, **reboot**, and **post-reboot attestation**.

Do not disable Smart App Control, WDAC, VBS, Code Integrity, Secure Boot, or other security controls merely to execute an unsigned helper. On the reference machine, an unsigned locally compiled executable was correctly blocked by Windows Code Integrity. The successful route used an already trusted Python runtime to call the signed AMD ADLX DLL while leaving the security policy intact.

A VGM transition can reduce memory available to Windows substantially. Close important workloads first, maintain console access where possible, and expect a reboot.

## Repository layout

- `docs/VERIFIED_SEQUENCE.md` — complete engineering sequence and observed evidence.
- `docs/TECHNICAL_NOTES.md` — ADLX interfaces, vtable layout, application-control finding, and interpretation.
- `scripts/post_reboot_attestation.ps1` — non-mutating Windows verification.
- `scripts/vgm_readonly_probe.py` — reference read-only ctypes/ADLX probe framework.
- `SECURITY.md` — safety and disclosure guidance.
- `CONTRIBUTING.md` — how to contribute results from other AMD platforms.
- `LICENSE` — MIT license for repository-authored code/docs.

## Quick verification after a change

Open **Task Manager → Performance → GPU**. On a successful 96 GB configuration, the dedicated GPU-memory limit should be around **95.8 GB** in Task Manager. Then run the read-only attestation in this repository to confirm the ADLX state itself.

## Important terminology

This is often described casually as “upgrading from 64 GB to 96 GB RAM,” but technically that is not what occurs. On a 128 GB unified-memory machine, the operation changes the amount carved out for graphics from 64 GB to 96 GB, leaving 32 GB for the operating system.

## Provenance

The workflow was developed from an actual recovery/configuration session using AMD's public ADLX SDK interfaces, Windows instrumentation, strict pre/post-state checks, and independent Task Manager confirmation. Machine-specific secrets, SSH keys, usernames, public IP addresses, Tailscale identities, and private infrastructure details are intentionally excluded.

## Disclaimer

This is an independent community project, not an AMD product and not endorsed by AMD. Hardware, firmware, driver, Windows, and ADLX behavior can differ between systems. Verify support on your own machine before mutation and maintain a recovery path.
