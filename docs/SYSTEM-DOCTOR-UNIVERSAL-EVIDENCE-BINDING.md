# Universal System Doctor → Universal Evidence signed binding

**Roadmap:** F-02 Universal System Doctor + F-05 Universal Evidence Standard  
**Status:** both remain IN PROGRESS

## Purpose

F-02 can now produce bounded cross-platform diagnostic observations, but a naked SHA-256 inside a diagnostic result is only a content-binding claim. It does not authenticate who produced the evidence or establish a trustworthy execution provenance chain.

This tranche connects F-02 to the existing F-05 evidence/trust work without inventing a new signing system.

## Search-before-build

The implementation deliberately composes existing standards and tooling:

- **DAIS Universal Evidence v0.1** remains the local portable evidence envelope and hash-manifest contract.
- **in-toto Attestation Framework** remains an external attestation interoperability direction rather than something DAIS reimplements.
- **SLSA provenance** remains the external provenance model for tracing software artifacts to how they were produced.
- **Sigstore/Cosign** remains the keyless signing, identity, transparency and timestamp verification implementation already exercised by F-05.

The binder therefore does not implement a CA, OIDC provider, transparency log, timestamp authority, signature algorithm, or competing provenance protocol.

References:

- https://in-toto.io/docs/specs/
- https://slsa.dev/spec/v1.2/provenance
- https://docs.sigstore.dev/cosign/signing/signing_with_blobs/

## Binding pipeline

```text
real bounded psutil hosted acceptance
        ↓
validate F-02 privacy / mutation / overclaim boundary
        ↓
retain exact bounded source evidence
        ↓ SHA-256
retain F-02 observation case
        ↓ SHA-256
retain conflict/UNKNOWN-aware fused result
        ↓ SHA-256
DAIS Universal Evidence v0.1 envelope
        ↓ schema + exact artifact hash validation
keyless Cosign sign-blob
        ↓
exact GitHub workflow identity + issuer verification
        ↓
transparency-log + RFC3161 timestamp material inspection
        ↓
wrong-identity + tamper negative controls
        ↓
existing F-05 exact trust-policy evaluation
```

## What the binder enforces

`system_doctor_universal_evidence.py` fails closed unless:

1. the bounded source record's canonical SHA-256 matches the acceptance record;
2. every F-02 observation points to exactly that source digest;
3. the fused result retains exactly that source digest;
4. the observation-case and fused-result case IDs match;
5. all source privacy and mutation declarations remain false;
6. all F-02 overclaim flags remain false;
7. the real psutil acceptance marker is explicit;
8. the caller supplies a concrete Git source commit and portable evidence ID.

It then writes three exact JSON artifacts and a Universal Evidence envelope referencing their byte-level SHA-256 values.

## Universal Evidence semantics

The envelope uses `evidence_type=acceptance` and `operation.classification=VERIFY` because this tranche verifies and binds evidence; it does not mutate the diagnosed machine.

The mapped roadmap IDs are:

- `F-02` — Universal System Doctor;
- `F-05` — Universal Evidence Standard;
- `P-002` — Universal PC Diagnostic Assistant;
- `P-212` — Universal Evidence Schema.

The envelope records hard-false post-state claims for root cause, hardware health, repair authority, production safety and roadmap completion.

## Signed hosted acceptance

The dedicated GitHub-hosted workflow:

1. runs focused F-02/F-05 binding tests;
2. executes the real pinned psutil adapter on disposable Ubuntu 24.04;
3. creates the exact Universal Evidence envelope;
4. uses the existing fail-closed `evidence_validate.py` to verify schema plus referenced artifact hashes;
5. keyless-signs the exact Universal Evidence bytes with pinned Cosign v3.0.6;
6. verifies the exact GitHub Actions workflow identity and GitHub OIDC issuer;
7. requires transparency-log and RFC3161 timestamp material in the Sigstore bundle;
8. proves wrong signer identity fails;
9. proves one-byte-class tampering fails;
10. feeds normalized verifier output into the existing F-05 exact trust-policy evaluator;
11. retains only sanitized, short-lived public CI evidence.

## Critical truth boundary

Even if every acceptance gate passes:

- the cryptographic signature authenticates the workflow identity for the exact bytes; it does not prove those diagnostic observations are medically, mechanically, or technically true;
- Universal Evidence schema validity does not prove the claimed observation occurred;
- source hashes prove byte identity, not correctness;
- GitHub-hosted psutil acceptance does not prove a physical device is healthy;
- no repair is authorized;
- no production safety can be inferred;
- no SLSA Build level is claimed;
- F-02 and F-05 remain IN PROGRESS.

This separation is intentional: **identity, integrity, provenance, semantic truth and operational safety are distinct claims.**

## Privacy and public-evidence review

The public CI path contains only disposable GitHub-hosted coarse capacity data and bounded semantic observations. It does not collect usernames, hostnames, IP addresses, interface lists, processes, command lines, credentials, user documents or private infrastructure.

For future physical-device use, the evidence publication policy must be reconsidered. Exact capacity, serial, device, firmware, network or vendor identifiers may be sensitive even when they are not credentials. A physical-device adapter should default to local/private retention and publish only explicitly reviewed evidence.

## Remaining F-02/F-05 gates

### F-02

- deeper specialist bounded adapters and real troubleshooting cases;
- physical non-production acceptance where justified;
- beginner and assistive-technology acceptance through F-06;
- versioned public distribution and community feedback.

### F-05

- authenticated multi-snapshot TUF refresh lifecycle and rollback/freeze resistance;
- independent verifier/toolchain evidence;
- independent security/standards review;
- reusable released distribution and community interoperability testing.

Neither foundation is promoted to COMPLETE by this tranche.
