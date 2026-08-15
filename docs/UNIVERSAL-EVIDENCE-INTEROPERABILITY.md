# Universal Evidence Interoperability

**Foundation:** F-05 Universal Evidence Standard — **IN PROGRESS**.

DAIS Universal Evidence is an envelope for operational evidence, not a replacement for domain standards. This tranche adds fail-honest mapping plans to established ecosystems while preserving each standard's stronger verification semantics.

## Search-before-build direction

- **in-toto Attestation Framework** defines a reusable Statement/attestation model. DAIS may emit an unsigned Statement-shaped interchange plan but must not call it signed or verified until a real signing/verifier path is used.
- **SLSA 1.2** defines current build/source supply-chain levels and recommends build provenance using the in-toto predicate model. Universal Evidence v0.1 does not contain all SLSA builder/build-definition/dependency semantics, so automatic SLSA provenance conversion correctly reports `ready: false` rather than manufacturing missing fields.
- **OpenTelemetry** standardizes traces, metrics and logs. DAIS can map selected non-sensitive operational attributes into a log/event plan, but must not export prompt/message/secret values or claim stable semantic-convention compliance for custom `dais.*` attributes.
- **W3C PROV** models entities, activities and agents. DAIS can expose a conceptual mapping without claiming that a serialized PROV document has been generated or validated against PROV constraints.
- **SPDX/CycloneDX** remain specialist software-composition formats. DAIS links externally by name/hash/evidence ID; it does not pretend that linking a BOM proves the BOM parses, validates, is current or is signed.

## Trust rules

1. Schema-valid is not signed.
2. Signed is not automatically trusted.
3. Provenance is not proof of correctness or fitness.
4. A SHA-256 digest binds bytes, not the truth of a claim about those bytes.
5. Mapping fields between standards is not semantic conformance.
6. Operational observability must not expose credentials, private infrastructure, user messages, prompts or private model reasoning.
7. Interoperability adapters fail closed when required source semantics are absent.

## Current adapter surfaces

`scripts/evidence_interoperability.py` provides:

- `interoperability_manifest()` — records candidate standard mappings and explicit non-claims;
- `in_toto_statement_plan()` — creates an unsigned Statement-shaped object with artifact subjects and a DAIS predicate reference;
- `slsa_build_provenance_readiness()` — intentionally refuses conversion while required SLSA build semantics are absent;
- `otel_log_event_plan()` — maps a minimal non-sensitive operational event without exporting it;
- `w3c_prov_plan()` — maps subject/activity/producer concepts without claiming PROV validation;
- `external_composition_reference()` — hash-links SPDX/CycloneDX documents without parsing/validation/signature claims.

## Completion gaps

F-05 remains IN PROGRESS. Completion still requires a stable versioned specification, independent review, signed in-toto/SLSA fixture generation and verification, normative schema/version negotiation, OpenTelemetry convention review, W3C PROV serialization/validation where claimed, SPDX/CycloneDX real parser/validator fixtures, cross-language reference implementations, accessibility/documentation acceptance, tagged release and canonical completion evidence.
