# AMD Ryzen AI Max — 96 GB Variable Graphics Memory (VGM)

A field-tested, evidence-driven community toolkit for configuring supported **AMD Ryzen AI Max / Radeon integrated graphics systems with 128 GB unified physical memory** from a 64 GB graphics-memory profile to AMD ADLX's **Custom 96 GB graphics / 32 GB system** profile.

> [!IMPORTANT]
> This repository does **not** add physical RAM. It changes AMD **Variable Graphics Memory (VGM)** allocation on compatible 128 GB systems. After the verified transition described here, Windows exposed about **31.79 GiB** system-visible memory and the AMD graphics driver exposed **96 GB dedicated GPU memory**.

> [!TIP]
> New to this? Start with **[START-HERE.md](START-HERE.md)** and then **[docs/BEGINNER-GUIDE.md](docs/BEGINNER-GUIDE.md)**. The same repository also contains the deeper engineering evidence and ABI notes for advanced users.

## Verified reference result

On the reference Ryzen AI Max platform, AMD ADLX 1.5.0.124 reported:

```text
BEFORE
Current option: High
GPU carved:      64 GB
System remain:   64 GB
Windows visible: 63.79 GiB

TARGET
Unique target:   Custom
GPU carved:      96 GB
System remain:   32 GB

AFTER REBOOT
Current option:  Custom
GPU carved:      96 GB
System remain:   32 GB
Windows visible: 31.79 GiB
Driver GPU memory: 96 GB
```

Windows Task Manager independently displayed approximately **95.8 GB dedicated GPU memory** and approximately **112 GB total GPU memory** when shared GPU memory was included.

## Two audiences, one engineering standard

This repository is intentionally designed for both newcomers and technical reviewers.

**Beginner layer:** numbered instructions, plain-language explanations, clear stop conditions, and explicit labels showing whether a step is read-only or mutating.

**Engineering layer:** AMD ADLX interface details, vtable/ABI reasoning, security-control observations, deterministic state gates, evidence preservation, at-most-once mutation semantics, and post-reboot attestation.

The beginner experience is simpler; the underlying safety contract is not weaker.

## Governing workflow

```text
DISCOVER -> VERIFY -> PREFLIGHT -> APPROVE -> MUTATE -> REBOOT -> ATTEST
```

The project deliberately keeps these stages separate. A tool presented as discovery must not silently perform mutation.

## Safety states

- **SAFE / READ ONLY** — discovery, option enumeration, compatibility checks, post-change attestation.
- **REVIEW** — unexpected state, missing prerequisite, unsupported target, or ambiguous evidence.
- **MUTATING** — the explicitly approved operation that may call AMD ADLX `SetOption`.
- **VERIFY** — post-reboot attestation; never an automatic mutation retry.

## Why this repository exists

The difficult part was not discovering that a 96 GB profile existed. The difficult part was changing it **without guessing**, while preserving remote recovery and producing evidence that the requested profile was actually supported by the installed AMD runtime.

The successful reference workflow was:

1. Establish recovery before changing memory allocation.
2. Inspect AMD's ADLX Variable Graphics Memory support in read-only mode.
3. Enumerate all VGM options and confirm a unique `Custom / 96 GB / 32 GB` target.
4. Preserve Windows application-control protections rather than disabling them.
5. Use the installed, signed AMD ADLX runtime.
6. Gate the write on the observed current state and exact target.
7. Invoke `IADLXVariableGraphicsMemory::SetOption` **once**.
8. Reboot Windows.
9. Reconnect and independently attest Windows memory, driver memory, and ADLX current state.
10. Never blindly retry a successful `SetOption` after SSH disappears during reboot.

## Compatibility

This is intended only for systems where the **live installed AMD ADLX runtime** reports Variable Graphics Memory support and explicitly enumerates the desired 96/32 profile.

**Do not assume Option 12 is 96 GB on another machine.** The reference machine happened to expose the target as its twelfth entry. Community tooling must match the semantic values (`Custom`, `96`, `32`) instead of relying on an ordinal.

See **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)** for the evidence vocabulary and community matrix.

## Security model

Do not disable Smart App Control, WDAC, VBS, Code Integrity, Secure Boot, or similar protections merely to execute an unsigned helper. On the reference system, a locally compiled unsigned helper was correctly blocked by Code Integrity. The successful route used a trusted Python runtime with the signed AMD ADLX DLL while leaving host security policy intact.

A 96 GB VGM carve-out substantially reduces memory available to Windows. Close important workloads, preserve console/recovery access, and expect a reboot.

Read **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** and **[docs/RECOVERY.md](docs/RECOVERY.md)** before designing or reviewing any mutating helper.

## Repository map

| Path | Audience | Purpose |
|---|---|---|
| `START-HERE.md` | Everyone | Safe entry point and lane selection |
| `docs/BEGINNER-GUIDE.md` | New users | Plain-language guided sequence |
| `docs/VERIFIED_SEQUENCE.md` | Technical | Field-tested sequence and evidence |
| `docs/TECHNICAL_NOTES.md` | Engineering | ADLX ABI, vtables, app-control findings |
| `docs/ARCHITECTURE.md` | Engineering | State machine, trust boundaries, fail-closed rules |
| `docs/RECOVERY.md` | Everyone | Remote/reboot recovery and anti-retry rules |
| `docs/TROUBLESHOOTING.md` | Everyone | Failure interpretation and safe next actions |
| `docs/COMPATIBILITY.md` | Community | Cross-platform evidence matrix |
| `docs/COMMUNITY-SAFETY.md` | Contributors | Beginner UX + engineering review standard |
| `scripts/vgm_readonly_probe.py` | Technical | Non-mutating ADLX runtime baseline probe |
| `scripts/post_reboot_attestation.ps1` | Technical | Non-mutating Windows verification |
| `.github/ISSUE_TEMPLATE/vgm-support.yml` | Community | Structured sanitized compatibility submissions |
| `.github/workflows/safety-checks.yml` | Maintainers | Automated safety-contract checks |
| `SECURITY.md` | Everyone | Safety and disclosure guidance |
| `CONTRIBUTING.md` | Contributors | Contribution requirements |

## Quick verification after a change

Open **Task Manager -> Performance -> GPU**. On the verified 96 GB configuration, the dedicated GPU-memory limit was approximately **95.8 GB**. That is useful visual evidence, but it should be paired with AMD ADLX current-state verification and Windows/driver memory values.

## Community reports

Use the repository's **VGM support / compatibility report** issue template. Submit sanitized output only. Reports should distinguish discovery-only results from fully post-reboot-attested transitions.

The project uses these evidence labels:

```text
VERIFIED
DISCOVERY-ONLY
COMMUNITY-REPORTED
UNSUPPORTED/NO-TARGET
UNKNOWN
```

## Automated safety checks

GitHub Actions validates Python syntax, required safety documentation, the declared read-only probe contract, and terminology intended to prevent this project from being misrepresented as a physical RAM upgrade.

These checks are guardrails, not a substitute for technical review.

## Important terminology

This is sometimes described casually as “upgrading 64 GB to 96 GB RAM,” but technically that is incorrect. On a 128 GB unified-memory system, the operation changes the graphics carve-out from 64 GB to 96 GB, leaving 32 GB for the operating system.

## Provenance

The workflow was developed from a real Ryzen AI Max recovery/configuration session using AMD's public ADLX SDK interfaces, Windows instrumentation, strict pre/post-state checks, at-most-once mutation handling, and independent Task Manager confirmation. Secrets, SSH keys, usernames, infrastructure addresses, Tailscale identity data, and other private operational details are intentionally excluded.

## Disclaimer

This is an independent community project, not an AMD product and not endorsed by AMD. Hardware, firmware, driver, Windows, and ADLX behavior can differ between systems. Verify support on your own machine before mutation and maintain a recovery path.
