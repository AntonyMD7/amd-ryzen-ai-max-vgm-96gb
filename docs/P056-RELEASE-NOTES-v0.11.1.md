# DAIS License Compliance Checker v0.11.1

Roadmap ID: **P-056 — License Compliance Checker**

## Why this patch exists

The first governed `v0.11.0` publication succeeded and the public tag resolved to the exact reviewed source, but the stronger released-ref acceptance correctly failed before completion promotion.

The failure was substantive: `v0.11.0` embedded the SHA-256 of exact raw REUSE JSON bytes inside the sanitized report whose own SHA-256 was advertised as deterministic. Independent REUSE 6.2.0 executions produced the same bounded compliance state and the same resolved dependency environment, while upstream JSON byte ordering differed. Therefore the raw-byte digest changed, which necessarily changed the sanitized-report digest. The product had conflated **run identity** with **semantic evidence identity**.

No completion gate was weakened and the failed released-ref evidence is retained as part of the engineering history.

## Permanent fix

`v0.11.1` separates the two identities:

- the privacy-minimized DAIS report is the deterministic semantic record;
- exact raw REUSE bytes keep a separate per-run SHA-256 Action output;
- the raw-byte digest is intentionally excluded from the deterministic report;
- the report explicitly records `evidence_identity_profile = semantic-v1` and that the raw digest is not embedded;
- raw REUSE JSON remains runner-temporary because it can contain repository-relative paths and copyright information;
- product version advances to `0.11.1` in emitted evidence.

This follows the general canonicalization principle that semantic identity must not depend on incidental serialization differences. It does not claim full RFC 8785/JCS conformance: DAIS uses a smaller typed, privacy-minimized evidence projection rather than attempting to canonicalize and publish the privacy-sensitive upstream REUSE document.

## Regression acceptance

The added regression suite deliberately creates semantically equivalent REUSE JSON documents with different object ordering, indentation and privacy-sensitive list ordering. It requires:

1. different raw byte strings and different raw SHA-256 values;
2. byte-identical sanitized DAIS reports;
3. identical sanitized-report SHA-256 values across English/Spanish and repeated executions;
4. distinct localized guides over one technical state;
5. no repository path, copyright identity or literal used-license identifier in sanitized evidence;
6. no consumer repository mutation.

Hosted real-REUSE acceptance also repeats P-056 against the pinned public `learning-git` snapshot and requires deterministic semantic evidence while retaining exact raw-run digests separately.

## Unchanged truth boundary

P-056 remains a bounded wrapper around REUSE Specification 3.3 / REUSE tool 6.2.0. It does not provide legal advice, redistribution permission, license compatibility, dependency-license safety, third-party-notice completeness, repository-security guarantees or distribution approval.

The top-level REUSE package remains exact-version pinned and the resolved environment is hashed, but a fully hash-locked transitive dependency closure is still **not** claimed.

## Completion boundary

`v0.11.1` is not COMPLETE merely because the fix exists. P-056 still requires green exact-head CI, merge to canonical public main, governed exact-source `v0.11.1` publication, released-ref public-consumer acceptance, retained release evidence, independent 19-gate completion record/final handover, fresh post-merge verification and canonical DAIS synchronization.
