# Universal Evidence — explicit Sigstore bundle material inspection

**Roadmap mapping:** F-05 Universal Evidence Standard; supports P-050, P-212, P-213 and P-224.  
**State:** IN PROGRESS supporting evidence — not a completion, SLSA-level or production-readiness claim.

## Purpose

The initial keyless acceptance used a successful pinned Cosign verification as the cryptographic verifier result and then mapped that result into the DAIS trust-policy evaluator. That was useful, but the retained claim record should also prove that the exact Sigstore bundle actually carries the verification-material classes required by the profile instead of inferring their presence from a successful verifier exit alone.

This follow-up makes those bundle-material preconditions machine-checkable.

## Search-before-build

No new signing or timestamp protocol is introduced. The implementation continues to adopt the Sigstore bundle format and pinned Cosign verifier.

The Sigstore bundle specification defines canonical lower-camel-case JSON fields for verification material. In bundle v0.3, transparency-log entries are carried in `verificationMaterial.tlogEntries` and RFC3161 signed timestamps are carried in `verificationMaterial.timestampVerificationData.rfc3161Timestamps`.

The acceptance therefore validates the existing standard-shaped material rather than inventing a parallel DAIS signature container.

## Exact main evidence inspected before this change

The retained artifact from exact public main commit:

`b0a953b2a5ca0c57d1d69f5193bfa1016c78b2de`

and workflow run:

`31873601340`

contained a keyless bundle with:

```text
mediaType = application/vnd.dev.sigstore.bundle.v0.3+json
tlogEntries = 1
rfc3161Timestamps = 1
```

The same exact-main workflow run completed successfully. This observation is supporting evidence for the workflow design, not a permanent assumption about all future bundles.

## New fail-closed checks

The workflow now fails unless every run independently observes:

1. exact bundle media type `application/vnd.dev.sigstore.bundle.v0.3+json`;
2. at least one transparency-log entry;
3. at least one RFC3161 signed timestamp;
4. successful pinned Cosign verification for the exact artifact, exact workflow certificate identity and exact GitHub OIDC issuer.

Only after those checks does the normalized verifier observation set:

```text
transparency_verified = true
timestamp_verified = true
timestamp_source = SIGSTORE_TSA
```

The retained `bundle-material-inspection.json` records counts and presence booleans so downstream review does not have to trust a prose assertion.

## Negative controls retained

The workflow still fails if:

- the correct artifact verifies under an intentionally incorrect workflow identity; or
- a one-newline-modified artifact verifies under the correct identity and issuer.

## Claim boundary retained

Even when all cryptographic, identity, bundle-material and exact trust-policy gates pass, the evidence record keeps these false:

```text
slsa_conformance_verified = false
builder_identity_verified = false
artifact_goodness_proven = false
statement_semantic_truth_verified = false
production_readiness_proven = false
```

This is deliberate. Presence and verification of signing/transparency/timestamp material do not establish semantic truth, safety, usefulness, SLSA level or production fitness.

## Privacy boundary

The acceptance uses only a sanitized public fixture, ephemeral GitHub-hosted compute, short-lived GitHub OIDC, and public Sigstore verification material. It does not retain a credential value, long-lived private signing key, user/device data, private repository material, private infrastructure details or production secrets.

## Remaining F-05 frontier

The highest-value remaining gaps are now narrower:

- real signed provenance/attestation acceptance with exact builder policy without overclaiming SLSA conformance;
- independent/external implementation interoperability review;
- long-term trusted-root/version archival and offline-verification policy;
- dedicated reusable public distribution and explicit release/version lifecycle;
- independent security/standards review and final canonical completion evidence.

F-05 therefore remains **IN PROGRESS**.
