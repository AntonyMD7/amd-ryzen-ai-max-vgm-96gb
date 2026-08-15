# Universal Evidence — network-isolated trusted-root verification acceptance

**Roadmap mapping:** F-05 Universal Evidence Standard; supports P-050, P-212, P-213 and P-224.  
**State:** IN PROGRESS supporting acceptance only.

## Why this tranche exists

Earlier F-05 tranches established exact-byte Cosign verification, keyless GitHub workflow identity, exact issuer policy, explicit transparency-log and RFC3161 timestamp material, and an authenticated signed in-toto/SLSA provenance path. A remaining high-value question is whether the retained artifact and verification material can be checked without live access to Sigstore services when a frozen trusted root is supplied.

This tranche tests that narrow property. It does not claim long-term archival sufficiency, future revocation awareness or operational air-gap readiness.

## Search-before-build

The implementation adopts Sigstore/Cosign's existing bundle and TrustedRoot mechanisms rather than introducing a DAIS trust-root format.

Primary upstream guidance says the protobuf-specs bundle format is designed to support offline verification and can carry signatures, certificates, transparency material and signed timestamps in a single file. Cosign `verify-blob` accepts an explicit `--trusted-root` file. Sigstore also warns that an air-gapped trusted-root copy must be refreshed intentionally because trust material can rotate; a frozen copy cannot tell the verifier about future revocations or key changes.

The TrustedRoot itself uses Sigstore's standard protocol shape and is retained with its exact SHA-256 digest for this acceptance run.

## Acceptance sequence

```text
ONLINE PREPARATION PHASE
  pinned Cosign v3.0.6
        |
        +-- initialize current Sigstore public-good TUF trust material
        +-- copy exact trusted_root.json + SHA-256
        +-- keyless-sign sanitized public Universal Evidence fixture
        +-- retain v0.3 Sigstore bundle
        |
        v
NETWORK-ISOLATED VERIFICATION PHASE
  Linux network namespace created with sudo unshare --net
        |
        +-- only namespace loopback interface exists
        +-- no default route exists
        +-- clean temporary HOME
        +-- explicit frozen --trusted-root
        +-- exact workflow identity
        +-- exact GitHub Actions OIDC issuer
        +-- --use-signed-timestamps
        |
        v
  cosign verify-blob PASS
```

The workflow also sets HTTP/HTTPS/ALL proxy variables to an unusable loopback endpoint during the positive verification. The network namespace—not those proxy settings—is the primary isolation control.

## Why the trusted root is security-relevant

The workflow creates a second copy of the TrustedRoot with certificate authorities, transparency logs and timestamp authorities removed. Verification inside the same network-isolated environment must reject that broken root.

It separately modifies one byte sequence in the signed artifact and requires verification with the correct frozen root to reject the tampered artifact.

These negative controls make a green run stronger than merely proving that the command executed.

## Retained evidence

The workflow retains only public/sanitized material:

- exact fixture and digest;
- Sigstore bundle;
- exact frozen TrustedRoot and digest;
- counts/media-type inspection of the root and bundle;
- exact signer identity and issuer strings;
- network-namespace interface/route observation;
- verifier output and fail-honest claim record.

It does **not** retain an OIDC token, long-lived private key, private repository data, user/device data, production secret or private infrastructure detail.

## What PASS establishes

A PASS supports the narrow claim that the exact signed public fixture can be verified with pinned Cosign using the exact frozen Sigstore TrustedRoot while the verifier runs in a Linux network namespace with no external route, and that an emptied trusted root and tampered artifact fail closed.

## What PASS does not establish

PASS does **not** prove:

- that a frozen root remains current indefinitely;
- awareness of revocations or key rotations that happen after the root snapshot;
- a safe root-refresh/import procedure for a real air-gapped organization;
- reproducible verification across every operating system/client;
- SLSA conformance or a SLSA Build level;
- artifact safety, goodness or semantic truth;
- production signing/verifier policy quality;
- completion of F-05 or any roadmap project.

## Long-term verification policy implication

A production archival design needs at least a governed rule for:

1. when trusted-root snapshots are acquired;
2. how their origin and digest are recorded;
3. how fresh root material is introduced into an offline enclave;
4. how historical material is retained for evidence reproducibility;
5. how revocation/key-rotation information is handled;
6. which verifier versions are supported and retained;
7. how failed refresh or inconsistent trust metadata is surfaced.

This CI acceptance proves only one building block for that policy.

## Remaining F-05 gates

F-05 remains **IN PROGRESS**. Major remaining gates include independent external implementation interoperability, a fully governed trust-root/version archival and refresh policy exercised over time, independently assessed builder/security model, dedicated reusable distribution/release lifecycle, external standards/security review, representative community feedback and the full canonical completion record.
