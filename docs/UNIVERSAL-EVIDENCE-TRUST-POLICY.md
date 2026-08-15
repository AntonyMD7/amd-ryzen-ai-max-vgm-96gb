# Universal Evidence Trust Policy v0.1

Status: **IN PROGRESS — policy layer, not a trust root or completion claim**

This tranche deepens **F-05 Universal Evidence Standard** by separating four questions that are easy to collapse incorrectly:

1. Do these artifact bytes match the expected digest?
2. Did a cryptographic verifier authenticate the expected signer identity and issuer?
3. Do required transparency/timestamp/provenance observations satisfy the selected policy?
4. Is the artifact actually safe, correct, useful, or semantically true?

The first three can contribute to a cryptographic/provenance trust decision. They do **not** answer the fourth.

## Search-before-build

DAIS does not implement another signing service, certificate authority, transparency log, timestamp authority, OIDC provider, or SLSA verifier.

The intended integration boundary is the existing Sigstore/Cosign and SLSA ecosystems:

- Sigstore keyless verification can bind a signature to an expected certificate identity and an expected OIDC issuer.
- Sigstore transparency and timestamp mechanisms provide separately verifiable evidence classes; a policy can require them without pretending that a timestamp proves semantic correctness.
- SLSA verification is policy-sensitive: builder/provenance identity is part of the trust decision and should be allowlisted deliberately rather than accepted merely because provenance exists.
- Sigstore's threat model explicitly distinguishes authenticated signer identity from whether the signed artifact is actually “good.”

Therefore `scripts/evidence_trust_policy.py` consumes a **normalized verification observation produced by a separately trusted verifier**. It does not do cryptography itself and never reports that it does.

## Exact-match policy

The initial profile intentionally allows only exact signer identity, exact HTTPS OIDC issuer, exact artifact SHA-256 and exact allowed builder IDs.

Wildcards and regular-expression signer policies are rejected in v0.1. This is conservative by design: a future pattern language would require its own escaping, ambiguity and policy-review contract.

A profile may independently require:

- transparency verification;
- a verified timestamp from `SIGSTORE_TSA` or `REKOR_V2_TSA`;
- verified provenance with a builder ID in an explicit allowlist.

## Two inputs

### Trust profile

`schemas/evidence-trust-profile-v0.1.schema.json` captures expected policy:

```text
artifact digest
expected signer identity
expected OIDC issuer
transparency requirement
timestamp requirement + accepted sources
builder/provenance requirement + allowed builders
explicit false claims for goodness/semantic truth
```

### Verification observation

A verification observation is deliberately normalized and small:

```text
artifact digest observed
cryptographic signature verified? yes/no
certificate identity
certificate OIDC issuer
transparency verified? yes/no
timestamp verified? yes/no + source
provenance verified? yes/no + builder id
verifier label
```

The evaluator does **not** automatically trust the observation. Its result always contains:

```text
verifier_observation_trusted_by_this_module = false
```

That forces the caller to retain evidence about which verifier/version/trust root generated the normalized observation.

## Result semantics

`POLICY_SATISFIED` means only that every enabled policy check evaluates true against the supplied normalized observation.

It always keeps these claims false/null:

```text
artifact_goodness_proven = false
semantic_truth_proven = false
slsa_level_proven = null
network_contact_performed = false
cryptography_performed = false
artifact_execution_performed = false
```

A policy pass therefore cannot be used as shorthand for software security, clinical validity, compatibility, accessibility, correctness, or production readiness.

## Synthetic fixtures

The included profile and observation use `.invalid` identities and a synthetic digest. They exist to test policy semantics only.

They do **not** establish:

- a real Sigstore/Fulcio identity;
- Rekor inclusion;
- a trusted timestamp;
- a real builder identity;
- SLSA conformance or level;
- external interoperability;
- a production trust root.

## Security and privacy

Trust profiles should contain public policy identifiers only. Do not place credentials, private keys, bearer tokens, identity tokens or private infrastructure secrets in profiles or observations.

A real integration should retain the minimum public/sanitized verification evidence needed to reproduce the trust decision and should avoid publishing unnecessary identity attributes.

## F-05 progression

F-05 now has separate reference layers for:

- Universal Evidence schema and validation;
- fail-honest in-toto/SLSA/OpenTelemetry/W3C PROV/SPDX/CycloneDX mappings;
- exact-blob Cosign signature/tamper acceptance in hosted CI;
- explicit exact-identity/issuer/transparency/timestamp/builder trust-policy evaluation.

F-05 remains **IN PROGRESS**. Completion still requires real trust identities/trust roots, external interoperability fixtures/review, dedicated public standard/distribution, release/versioning, retained acceptance evidence and the rest of the canonical completion contract.
