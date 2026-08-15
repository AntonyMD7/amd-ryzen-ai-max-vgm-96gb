# Universal Evidence — keyless identity/trust acceptance

**Roadmap mapping:** F-05 Universal Evidence Standard; supports P-050, P-212, P-213 and P-224.  
**State:** IN PROGRESS supporting acceptance — not a completion or production-trust claim.

## Why this tranche exists

The earlier disposable-key Cosign acceptance proves exact-byte signature verification and tamper rejection, but intentionally proves no signer identity, transparency-log inclusion or trusted timestamp. The F-05 roadmap gap therefore remains material: a reusable evidence standard needs a way to bind an exact artifact to an exact signer identity and issuer, while preserving the distinction between cryptographic verification and semantic truth.

## Search before build

This repository does **not** implement another certificate authority, OIDC provider, transparency log, timestamp authority or signing system.

It adopts the existing Sigstore/Cosign keyless-signing ecosystem and GitHub Actions OIDC:

- Sigstore recommends a bundle for blob signatures; the bundle carries the signature, certificate and transparency-log verification material.
- Sigstore keyless signing binds an ephemeral signing key to an OIDC identity.
- Cosign `verify-blob` supports exact certificate identity and exact OIDC issuer checks against a bundle.
- GitHub Actions requires only `id-token: write` to request an OIDC token; that permission alone does not grant repository-content write permission.
- GitHub's OIDC issuer is `https://token.actions.githubusercontent.com`.

The workflow uses the already-pinned `sigstore/cosign-installer` commit and Cosign `v3.0.6` used by the repository's prior signature acceptance.

## Acceptance architecture

```text
exact sanitized Universal Evidence fixture
        |
        | SHA-256 retained
        v
GitHub-hosted disposable Ubuntu job
        |
        | id-token: write only + contents: read
        v
Cosign keyless sign-blob
        |
        | Sigstore bundle
        v
Cosign verify-blob
        |
        +-- exact workflow certificate identity
        +-- exact GitHub OIDC issuer
        +-- transparency inclusion verification via bundle
        +-- signed timestamp verification via bundle
        |
        v
normalized verifier observation
        |
        v
existing DAIS exact trust-policy evaluator
        |
        v
POLICY_SATISFIED or fail closed
```

The expected certificate identity is derived from `GITHUB_WORKFLOW_REF` and verified as the exact workflow URI rather than using a wildcard or permissive regular expression.

## Negative controls

The workflow must fail if either of these negative controls unexpectedly verifies:

1. the correct blob under an intentionally wrong workflow identity;
2. a one-newline-modified copy of the signed blob under the correct identity and issuer.

These controls demonstrate that a green run is not simply accepting any Sigstore identity or any payload.

## Existing DAIS trust-policy integration

After Cosign succeeds, the workflow emits a normalized observation for `scripts/evidence_trust_policy.py` with:

- exact artifact SHA-256;
- cryptographic verification result;
- exact workflow certificate identity;
- exact GitHub OIDC issuer;
- transparency verification result;
- trusted timestamp verification result;
- no SLSA builder/provenance claim.

The generated exact trust profile requires the digest, identity, issuer, transparency and timestamp. It deliberately does **not** infer artifact goodness or semantic truth.

## Privacy and secret boundary

This acceptance uses only:

- one already-public sanitized fixture;
- GitHub-hosted ephemeral compute;
- a short-lived GitHub OIDC token requested by the job;
- public Sigstore verification infrastructure.

It does not retain the OIDC token, a private key, a long-lived signing credential, private repository content, user data, device data, production infrastructure details or private prompts/corpora.

The retained artifact may include the public workflow identity, public certificate/signature material and transparency verification material. Those are expected public evidence for this acceptance class.

## What PASS means

A passing run supports the following narrow claims for the exact fixture and exact workflow run:

- the exact bytes were signed using Sigstore keyless signing;
- Cosign accepted the exact workflow certificate identity;
- Cosign accepted the exact GitHub Actions OIDC issuer;
- Cosign verified the bundle's transparency-log inclusion and signed timestamp verification material;
- a wrong identity was rejected;
- tampered bytes were rejected;
- the normalized observation satisfied the DAIS exact trust profile.

## What PASS does not mean

A passing run does **not** prove:

- that the artifact is correct, safe, useful or semantically true;
- SLSA conformance or any SLSA level;
- a verified builder identity/provenance statement;
- that every Sigstore client interoperates with the DAIS schema;
- production signing-policy quality;
- organizational identity governance beyond this exact workflow identity;
- long-term archival verification policy;
- completion of F-05, P-212, P-224 or any other roadmap item.

## Remaining F-05 gates after this tranche

This tranche materially narrows the signer-identity/transparency/timestamp gap, but F-05 remains IN PROGRESS. Remaining high-value work includes:

1. signed in-toto/SLSA provenance fixtures with exact builder policy;
2. external implementation interoperability fixtures and independent review;
3. trust-root/version archival and long-term verification policy;
4. a dedicated reusable distribution/repository when governed repository creation is available;
5. versioned release/tag and retained completion evidence;
6. independent security/standards review and canonical completion handover.

## Workflow

`.github/workflows/universal-evidence-keyless-identity-acceptance.yml`

The workflow is source/CI acceptance only. It must never be treated as permission to sign or publish production artifacts automatically.
