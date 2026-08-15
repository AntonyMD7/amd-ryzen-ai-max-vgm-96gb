# Universal Evidence — signed provenance acceptance

**Roadmap mapping:** F-05 Universal Evidence Standard; supporting P-050, P-212, P-213 and P-224.  
**State:** IN PROGRESS supporting acceptance only.

## Search-before-build decision

This tranche adopts existing standards and tooling rather than creating another provenance or attestation protocol:

- in-toto Statement v1 for binding a subject to a typed predicate;
- SLSA Provenance v1 as the predicate shape;
- Sigstore/Cosign complete-statement attestation and keyless identity verification;
- the existing DAIS exact trust-policy evaluator for signer/builder allowlisting.

The implementation deliberately does **not** claim a SLSA Build level. SLSA requires more than a correctly shaped provenance document: consumers must reason about a trusted builder/root of trust, and higher levels require stronger build-platform guarantees. The demonstration provenance is assembled by repository-controlled workflow logic, so its builder documentation explicitly claims no assessed SLSA level.

## Acceptance flow

```text
exact public source commit
        |
        v
sanitized deterministic fixture artifact
        |
        v
in-toto Statement/v1 + SLSA provenance/v1 predicate
        |
        | exact subject SHA-256
        | exact source repo + commit
        | exact workflow ref
        | exact buildType
        | exact demo builder.id
        v
Cosign attest-blob --statement (keyless)
        |
        v
Sigstore bundle / DSSE envelope
        |
        +-- exact workflow signer identity
        +-- exact GitHub OIDC issuer
        +-- expected subject digest
        +-- transparency material
        +-- RFC3161 timestamp material
        v
authenticated statement extracted from signed DSSE payload
        |
        v
fail-closed DAIS provenance semantic parser
        |
        v
existing exact signer + builder trust policy
```

## Why the authenticated payload is parsed

The semantic policy does not trust the unsigned pre-signing file merely because it was generated in the same job. After Cosign verifies the attestation, the workflow decodes the DSSE payload from the verified bundle, checks that it semantically matches the generated statement, and runs the provenance policy against that authenticated payload.

This prevents a gap where cryptography verifies one statement while policy evaluates another.

## Exact semantic checks

`scripts/slsa_provenance_observation.py` requires:

- `_type == https://in-toto.io/Statement/v1`;
- `predicateType == https://slsa.dev/provenance/v1`;
- exactly one named subject with only the expected SHA-256 digest;
- the repository-defined build type;
- exactly the expected `sourceRepository`, `sourceCommit` and `workflowRef` external parameters;
- exactly one resolved Git source dependency at the expected commit;
- the exact documented demonstration `builder.id`;
- a GitHub Actions invocation identifier.

The parser is intentionally a narrow policy fixture, not a general SLSA validator.

## Negative controls

A run fails if any of these unexpectedly passes:

1. attestation verification under a wrong signer identity;
2. attestation verification for a wrong subject digest;
3. semantic validation after replacing the authenticated `builder.id`;
4. semantic validation after replacing the authenticated source commit.

## Trust-profile integration

Only after cryptographic verification, bundle-material validation and authenticated provenance semantic validation succeed does the normalized observation set:

```text
provenance_verified = true
builder_id = <exact documented demo builder ID>
```

The existing `scripts/evidence_trust_policy.py` then requires that exact builder ID in addition to exact artifact digest, signer identity, OIDC issuer, transparency and timestamp requirements.

## Privacy / safety boundary

The workflow uses public repository source, a public sanitized fixture, GitHub-hosted ephemeral compute and short-lived GitHub OIDC/Sigstore credentials. It retains no OIDC token, long-lived signing key, private repository data, user/device data, production secret or private infrastructure detail.

No production system or physical device is mutated.

## What PASS establishes

For the exact workflow run, PASS supports only that:

- an in-toto Statement v1 carrying SLSA Provenance v1 semantics was signed and verified;
- the authenticated statement names the exact demonstration artifact digest;
- exact repository/commit/workflow/build-type/builder fields satisfied the narrow policy;
- the signer identity and issuer satisfied the exact Sigstore identity policy;
- required bundle transparency/timestamp material was present and verified through the acceptance path;
- negative signer/subject/semantic controls failed closed;
- the exact signer-builder DAIS trust profile was satisfied.

## What PASS does not establish

PASS does **not** establish:

- SLSA Build L1, L2 or L3 conformance;
- independent assessment of the builder security model;
- trusted-control-plane generation of every provenance field;
- artifact safety, goodness or semantic truth;
- production-readiness of the signing policy;
- independent interoperability across implementations;
- F-05 or any roadmap project as COMPLETE.

## Remaining F-05 frontier

After this acceptance, the major remaining gates include independent/external interoperability evidence, long-term trust-root/version archival and offline verification policy, dedicated reusable distribution/release lifecycle, independent security/standards review, and the roadmap's complete public release/acceptance/handover contract.
