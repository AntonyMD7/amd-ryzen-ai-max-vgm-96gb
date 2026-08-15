# Universal Evidence exact-blob signature acceptance

**Foundation:** F-05 Universal Evidence Standard — **IN PROGRESS**.

This tranche closes one specific gap in the Universal Evidence proving ground: demonstrate that exact evidence bytes can be signed and cryptographically verified by an established specialist tool, and that modified bytes are rejected.

## Search-before-build decision

DAIS does not implement a new signature algorithm or PKI. This lane adopts **Sigstore Cosign**, an established open-source signing/verifying tool. The workflow pins Cosign `v3.0.6` and pins the official `sigstore/cosign-installer` action to an exact commit corresponding to installer `v4.1.2`.

Sigstore's documented blob workflow supports `sign-blob` with a local key and bundle output, and `verify-blob` with the artifact, bundle and verification material. The project also recommends bundles as the preferred carrier for verification material.

## Acceptance fixture

The workflow uses the existing sanitized `examples/universal-evidence-readonly-example.json` as the exact blob under test.

It generates a disposable P-256 key pair entirely inside the hosted CI job, signs the exact fixture, verifies it with the public key and bundle, then appends one newline to a copy and requires verification of the modified copy to fail.

The private key is deleted before any artifact upload. It is not a production key and must never be reused.

## What this proves

A successful run provides supporting evidence that:

- the exact fixture bytes can be signed with the pinned Cosign implementation;
- the generated bundle/public key can verify those exact bytes;
- a changed copy is rejected by that signature verification path;
- no private key is retained in the uploaded evidence set.

## What this does not prove

This fixture deliberately does **not** claim:

- verified real-world signer identity;
- Fulcio/OIDC identity binding;
- Rekor transparency-log inclusion;
- trusted timestamp validation;
- SLSA conformance;
- truth or correctness of the signed statement;
- production key-management quality;
- cross-implementation interoperability.

A valid signature proves a cryptographic relationship to key material. It does not make the underlying operational claim true.

## Why this is only a supporting gate

The canonical F-05 completion path still requires stable normative versioning, independent review, signed in-toto/SLSA profiles where claimed, identity/trust-policy verification profiles, external interoperability fixtures, cross-language reference behavior, a dedicated public distribution/release, and retained completion evidence.

This workflow therefore advances signed-evidence capability without changing F-05 from **IN PROGRESS**.
