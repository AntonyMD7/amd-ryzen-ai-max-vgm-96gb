# Infrastructure, Fleet & Evidence — Public Reference Layer

**Roadmap status:** `P-211` through `P-227` are **IN PROGRESS** reference work only. Several of these already have earlier proving-ground implementations; this tranche consolidates their shared contract and explicitly starts `P-221` through `P-227`.

## Search-before-build

Use mature infrastructure/evidence ecosystems rather than creating opaque alternatives. **in-toto Attestation Framework** defines a reusable attestation format; **SLSA 1.2** defines current software-supply-chain provenance/build/source tracks and uses in-toto predicates for build provenance; **OpenTelemetry** standardizes traces, metrics and logs for observability. **osquery** provides cross-platform system instrumentation, while **hw-probe/linux-hardware** is an existing hardware probe/compatibility evidence ecosystem. DAIS should interoperate with these where their trust/privacy model fits.

## Shared contract

- SafeFix/recovery-first lifecycle separates discovery, verification, preflight, approval, mutation and post-change evidence. A plan is never execution evidence.
- Universal Evidence envelopes bind subject IDs/hashes and standard references but do not equate a valid hash/schema with event truth or signature verification.
- Device/fleet records default to privacy-minimizing plan/evidence state: no unique identifier collection, arbitrary remote command or orchestration is implied.
- Compatibility records report an observed PASS/FAIL/PARTIAL/UNKNOWN against evidence; they never become universal compatibility guarantees.
- Public community evidence must be redaction-reviewed before publication and must not contain credentials or private infrastructure detail.
- Troubleshooting knowledge graphs may connect symptoms/checks/evidence, but graph structure alone does not establish a root cause.
- Reference implementations and architecture kits must distinguish source/tests/manifests from release, deployment and reproducibility claims.
- The `Problem → Public Solution` intake gate requires both existing-solution search and a safety review before a new build is authorized, preserving the roadmap's contribute-before-duplicate rule.

## Evidence interoperability direction

DAIS Universal Evidence should remain a domain-neutral envelope that can reference stronger domain standards rather than replacing them: in-toto/SLSA for software provenance, OpenTelemetry for operational signals, W3C PROV-style lineage where appropriate, SPDX/CycloneDX for software composition, and specialist hardware probes for device facts. Each external evidence type retains its own verification semantics.

## Completion gaps

No mapped item is COMPLETE. Required gates include dedicated distribution, stable schemas/version negotiation, signed/verified evidence profiles, privacy/redaction acceptance, cross-platform fleet tests, community moderation/provenance policy, compatibility corpus quality controls, knowledge-graph validation, reproducible starter-kit acceptance, accessibility/multilingual UX, tagged releases and canonical completion records.
