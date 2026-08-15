# Universal Evidence Integrity v0.2

Status: **IN PROGRESS — integrity detection without identity/trust claims**

Canonical roadmap mapping: **F-05 Universal Evidence Standard**, supporting P-207/P-209/P-212/P-213/P-216 through P-227 where evidence integrity is relevant.

## Purpose

Universal Evidence v0.1 established a portable evidence envelope and interoperability mapping layer. This tranche adds a deterministic integrity sidecar so a consumer can answer a narrower question:

> Are these exact evidence bytes, normalized diagnostic content, and optionally declared artifact files unchanged from the sidecar that was created for them?

That is useful, but it is deliberately **not** the same as proving who created the evidence, whether the timestamp is trustworthy, whether authorization was valid, or whether the observation itself is true.

## Search-before-build / standards boundary

This project should not invent its own signing ecosystem.

- **RFC 8785 / JSON Canonicalization Scheme (JCS)** defines a canonical JSON representation intended for repeatable cryptographic operations. DAIS's current `DAIS_SORTED_JSON_V0.1` is a simpler project-local diagnostic normalization and explicitly does **not** claim RFC 8785/JCS conformance: https://www.rfc-editor.org/rfc/rfc8785
- **DSSE (Dead Simple Signing Envelope)** signs typed payload bytes and deliberately avoids depending on JSON canonicalization for the payload. A future signed DAIS evidence path should prefer a reviewed typed-envelope/signature standard such as DSSE rather than treating the project-local sorted JSON digest as a signature format: https://github.com/secure-systems-lab/dsse
- **in-toto attestations** remain the external attestation ecosystem that DAIS already maps toward. Integrity sidecars complement rather than replace in-toto/SLSA-style provenance and verification: https://github.com/in-toto/attestation

## Two integrity bindings

`scripts/evidence_integrity.py` creates two SHA-256 digests:

1. `exact_bytes_sha256` binds the exact UTF-8 JSON evidence file bytes. Reformatting the file changes this digest even if the parsed JSON semantics are the same.
2. `dais_sorted_json_v0_1_sha256` binds a deterministic project-local sorted/minified JSON rendering for diagnostic comparison.

The second digest is useful for identifying semantic-equivalent formatting differences, but its profile is intentionally marked:

- `rfc8785_jcs_conformance_claimed: false`
- `signature_format: false`

No cryptographic identity claim is built on that normalization.

## Duplicate-key refusal

Evidence JSON is parsed with duplicate-object-key rejection before schema validation. This matters because permissive JSON parsers can otherwise silently keep one of two identically named fields, creating ambiguity about what was actually signed/hashed/validated.

For example, a document containing two `result` or `schema_version` keys is rejected rather than normalized.

## Semantic and privacy guards

Before creating a sidecar, the integrity layer:

- validates Universal Evidence v0.1 with Draft 2020-12 JSON Schema and date-time format checking;
- rejects mutation evidence that is not classified `MUTATING`;
- rejects a `READ_ONLY` operation that declares an intended change;
- rejects successful mutating evidence without a `post_state`;
- rejects an overall `PASS` that conflicts with a failed acceptance item;
- applies a high-confidence public-evidence privacy prefilter for private-key material, common token patterns, email addresses, MAC addresses, RFC1918/CGNAT addresses, and user home paths.

The privacy scanner is a prefilter, not a complete DLP system. Its purpose is to fail closed on high-confidence unsafe public evidence, not to certify that every possible sensitive value has been removed.

## Artifact binding

Universal Evidence may declare artifacts by name and SHA-256.

When an explicit artifact root is supplied, the integrity helper verifies each declared artifact from that root and refuses:

- absolute paths;
- `.` / `..` path traversal;
- paths escaping the supplied root;
- symlink paths;
- missing/non-regular files;
- files over the acceptance size limit;
- digest mismatches.

Artifact verification is opt-in because a consumer may receive an evidence envelope without having the original artifact files locally.

## Trust model

Every sidecar schema-enforces these values as `false`:

- `signature_present`
- `signature_verified`
- `producer_identity_verified`
- `trusted_timestamp_verified`
- `authorization_truth_verified`
- `provenance_truth_verified`
- `evidence_truth_verified`

A successful verification result is therefore named:

`INTEGRITY_VERIFIED_NOT_TRUST_VERIFIED`

This naming is intentional. SHA-256 can prove byte equality with a prior digest; it cannot prove that the original record was honest.

## Beginner view

> The evidence system can now notice if a saved report or attached evidence file changed after its integrity record was created. It still cannot tell you who created the report or whether what the report says is true. Those require trusted signatures, identity, and independent verification.

## Engineer view

The sidecar binds raw bytes plus a project-local normalized form and optionally re-hashes declared local artifact files. The sidecar validates against its own strict schema. Verification recomputes all bindings and refuses sidecars whose trust fields are altered to claim signatures/trust that do not exist.

The tool contains no signer, private key, timestamp authority, network client, transparency-log publisher, subprocess executor, or mutation path.

## Security and privacy review

- No private signing key exists in this tranche.
- No key management is attempted.
- No network request/upload occurs.
- No evidence is automatically redacted and then published; suspicious public evidence is refused.
- No subject device/repository is mutated.
- Artifact verification is bounded to an explicit root and rejects symlinks/path escape.
- Exact-byte binding prevents silent whitespace/formatting changes from passing as the same original file.
- Duplicate JSON keys are rejected before schema validation.

## Accessibility / multilingual path

The integrity sidecar is a machine contract. User-facing tools should translate states such as `INTEGRITY_VERIFIED_NOT_TRUST_VERIFIED` into plain language without hiding the trust limitation, while retaining the raw engineering view. Localization must preserve the distinction between integrity, identity, provenance, authorization, and truth.

## What remains before F-05 can be COMPLETE

F-05 remains **IN PROGRESS**. Material unresolved gates include:

- a dedicated public standard/specification release with stable namespace/version policy;
- a reviewed signed-envelope profile (preferably interoperable with DSSE/in-toto rather than a bespoke signature format);
- explicit trust-policy/key-identity model;
- trusted timestamp/transparency-log design where appropriate;
- conformance vectors for external implementations;
- independent verification implementation in a second language/toolchain;
- formal interoperability/conformance testing against in-toto/SLSA/OpenTelemetry/W3C PROV/SPDX/CycloneDX mappings;
- revocation/correction/supersession semantics;
- accessibility and multilingual human review;
- external security/cryptography review before any signature/trust claim;
- versioned release/tag/changelog and canonical completion record.

No production/device mutation is authorized by this tranche.
