# v0.1.0 — AMD Ryzen AI Max 96 GB VGM Community Toolkit

This first public release packages the field-tested **Unified/Variable Memory Configuration Assistant** work tracked as DAIS roadmap item **P-025**.

## What is included

- beginner-safe entry points in `START-HERE.md` and `docs/BEGINNER-GUIDE.md`;
- evidence-driven compatibility and preflight guidance;
- a read-only AMD ADLX VGM probe;
- a documented, bounded mutation sequence for compatible 128 GB Ryzen AI Max systems;
- recovery-first and anti-retry guidance around reboot/remote-access loss;
- post-reboot attestation guidance and tooling;
- architecture, security, troubleshooting, compatibility and community-contribution documentation;
- automated safety-contract tests and CI.

## Verified reference scope

The retained reference evidence covers one compatible **128 GB AMD Ryzen AI Max** system where the installed AMD ADLX runtime explicitly enumerated a `Custom / 96 GB graphics / 32 GB system` profile. The verified sequence changed the reference system from a 64/64 profile to 96/32, rebooted, and independently verified the resulting Windows-visible memory, driver-reported GPU memory and ADLX current state.

## Safety boundary

This release does **not** claim universal Ryzen AI Max compatibility. Operators must use the live installed AMD runtime to confirm VGM support and the exact semantic target on their own machine. Do not assume an option ordinal is portable between systems.

A 96 GB GPU carve-out substantially reduces memory left to Windows. Establish recovery access before mutation, preserve host security controls, close important workloads, expect a reboot, and never blindly retry a successful mutation merely because SSH or another remote session disappears during the reboot.

## Known limitations

- field acceptance is limited to the documented reference configuration;
- public documentation is primarily English, although localization architecture has been considered;
- accessibility review is documented but is not a WCAG conformance claim or assistive-technology user acceptance;
- no universal compatibility certification, production-safety guarantee or automatic remediation authority is implied;
- firmware, driver and platform changes can alter compatibility and must be re-verified from current evidence.

## Evidence and review

Start with:

- `docs/VERIFIED_SEQUENCE.md`
- `docs/P025-COMPLETION-READINESS.md`
- `docs/ARCHITECTURE.md`
- `docs/RECOVERY.md`
- `docs/COMPATIBILITY.md`
- `SECURITY.md`

The release tag is intended to bind the published public state to exact commit `704f7bab429b1f67896b32bf90b99d3d0d9cd39c`. Release publication alone does not mark P-025 complete; a separate post-publication verification and canonical completion handover are required.
