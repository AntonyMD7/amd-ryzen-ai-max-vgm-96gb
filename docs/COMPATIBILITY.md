# Compatibility Matrix

This file records what is **verified**, what is **reported by the community**, and what is **unknown**.

Do not infer compatibility from processor family name alone. Firmware, OEM implementation, driver version, Windows build, and installed ADLX runtime can change behavior.

## Status vocabulary

- **VERIFIED** — evidence includes live ADLX enumeration and post-change attestation.
- **DISCOVERY-ONLY** — read-only enumeration supplied; no mutation verified.
- **COMMUNITY-REPORTED** — result reported but not yet independently checked against the project evidence contract.
- **UNSUPPORTED/NO-TARGET** — ADLX does not expose the required VGM support/target.
- **UNKNOWN** — not yet tested.

## Reference platform

| Field | Result |
|---|---|
| Platform class | AMD Ryzen AI Max, 128 GB unified physical memory |
| Pre-change VGM | High / 64 GB carved / 64 GB remaining |
| AMD ADLX runtime | 1.5.0.124 |
| VGM support | Yes |
| Available options | 12 |
| 96/32 target | Exactly one `Custom / 96 / 32` target |
| Mutation | `SetOption` called once, return code 0 |
| Reboot | Required and observed |
| Post-change ADLX | Custom / 96 / 32 |
| Windows visible memory | ~31.79 GiB |
| Driver GPU memory | 96 GB |
| Task Manager | ~95.8 GB dedicated GPU memory |
| Status | VERIFIED |

## Community submissions

When adding a platform, use this format:

| System/OEM | CPU/APU | Physical memory | Windows | AMD driver | ADLX | VGM supported | 96/32 target | Result | Evidence status |
|---|---|---:|---|---|---|---|---|---|---|
| Reference platform | Ryzen AI Max class | 128 GB | recorded in verified case | recorded in verified case | 1.5.0.124 | Yes | Yes | 96/32 verified | VERIFIED |

## Submission requirements

A useful compatibility report should include sanitized output for:

```text
physical memory
Windows build
GPU name
AMD driver version
ADLX version
VGM_SUPPORTED
AVAILABLE_COUNT
all option name/mode/carved/remaining values
current option
```

For a claimed successful transition also include:

```text
pre-change current state
unique target match
SetOption call count
SetOption return code
reboot observation
post-change current state
Windows visible memory
driver GPU memory
Task Manager observation (optional but useful)
```

## Never add secrets

Do not include private keys, access tokens, usernames you do not want public, public/private infrastructure addresses, device-auth secrets, or other credentials.
