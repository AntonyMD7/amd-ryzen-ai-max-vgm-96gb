# DAIS Public Build Depth Update — through PR #70

**Date:** 2026-08-15  
**Authority boundary:** supporting public proving-ground status only. The canonical `DAIS_PUBLIC_BUILD_OPPORTUNITY_MASTER_ROADMAP_v1.0.md` remains authoritative for IDs and completion requirements.

## Portfolio truth

The portfolio remains:

| State | Count |
|---|---:|
| COMPLETE | 0 |
| IN PROGRESS | 227 |
| BLOCKED | 0 |
| DEFERRED | 0 |
| NOT STARTED | 0 |

`227 IN PROGRESS` means every canonical opportunity has an initial public source/reference surface. It does not mean that 227 projects satisfy the completion contract.

## Newly promoted depth evidence

### PR #68 — F-01 SafeFix Linux durability barriers

The marked disposable sandbox now uses Linux parent-directory `fsync` barriers after atomic replacement and recovery-directory creation, while preserving compatibility with prior v0.3 recovery journals. Failures in an attempted Linux directory durability barrier fail closed.

The evidence continues to state that this does **not** prove filesystem-specific crash consistency, hardware write-cache durability, true multi-resource atomicity, power-loss safety or production readiness.

**F-01 remains IN PROGRESS.**

### PR #69 — F-05 network-isolated frozen-root verification

The Universal Evidence proving ground now exercises an exact signed public fixture with pinned Cosign and the Sigstore public-good TrustedRoot. Verification occurs inside a Linux network namespace with no default external route and an explicit frozen TrustedRoot. Negative controls require an emptied trust root and tampered artifact bytes to fail.

The retained supporting evidence does **not** establish future revocation awareness, indefinite root freshness, operational air-gap readiness, SLSA level, artifact goodness, semantic truth, production readiness or roadmap completion.

### PR #70 — F-05 trusted-root archive/refresh policy

A strict archival metadata contract now records the upstream root snapshot source, acquisition time, exact digest/size, component counts, verifier version, explicit local refresh deadline and an optional SHA-256 link to the previous snapshot record. A deterministic evaluator requires an explicit UTC `--as-of` time, fails closed after the local refresh deadline, and rejects a supplied previous-record hash mismatch.

The evaluator deliberately performs no TUF verification, cryptography, revocation lookup or network contact. `ARCHIVE_POLICY_SATISFIED` therefore describes only the local archival record/refresh contract, not global root validity.

**F-05 remains IN PROGRESS.**

## Search-before-build record

These tranches continue to adopt established upstream mechanisms rather than introduce parallel infrastructure:

- Sigstore/Cosign for signed bundles, identities, transparency/timestamp material and explicit TrustedRoot verification;
- Sigstore `protobuf-specs` for TrustedRoot/bundle structures;
- Sigstore `root-signing` and The Update Framework (TUF) for authenticated trust-root distribution and rotation semantics;
- native filesystem primitives only for the SafeFix disposable file-sandbox durability experiment, with higher-level native rollback/transaction systems preferred where applicable.

DAIS does not create another certificate authority, transparency log, timestamp authority, TUF replacement, root-signing service or operating-system transaction engine in these tranches.

## Remaining flagship blockers

### F-01 SafeFix

Still requires dedicated reusable distribution, governed native adapters, representative non-production recovery acceptance, explicit native transaction integration where available, release/version lifecycle, and independent review. Power-loss/group atomicity remains unproven.

### F-05 Universal Evidence Standard

Still requires a real multi-snapshot authenticated TUF refresh/import lifecycle exercised over time, rollback/freeze-resistance evidence through an upstream TUF client, independent implementation interoperability using a second verifier/toolchain, independent builder/security assessment, dedicated released distribution, external standards/security review, representative community feedback and the full canonical completion record.

## Completion boundary

No roadmap item is promoted to `COMPLETE` by this update. Source promotion, unit/hosted acceptance, cryptographic verification and policy evidence are supporting gates only. The canonical completion contract remains unchanged.
