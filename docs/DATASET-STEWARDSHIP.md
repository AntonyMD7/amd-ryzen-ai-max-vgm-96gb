# Privacy-First Dataset Stewardship

Status: **IN PROGRESS reference implementation** for:

- `P-069 Dataset Quality Checker`
- `P-070 Dataset Cleaning Pipeline`
- `P-071 Dataset PII Scanner`
- `P-072 Dataset Duplicate Detector`
- `P-073 Dataset License/Provenance Checker`
- `P-075 Low-Resource-Language Dataset Program`

## Search before build

The project deliberately does not build replacement dataset/PII engines.

- **Hugging Face Datasets** remains an established dataset loading/processing foundation.
- **Presidio** is an established open-source privacy/PII analysis and anonymization ecosystem. A future PII adapter should evaluate and pin an appropriate local engine rather than growing a home-made regex list into a security claim.
- SPDX/REUSE and dataset-source licensing/provenance records remain relevant upstream standards/tooling for rights metadata.

The reference layer adds governance/evidence primitives that can wrap those systems without ingesting raw private data into the public proving ground.

## P-069 — quality profile

Consumes only row count plus per-field missing/invalid counts. It computes transparent fractions but never reads dataset rows or certifies quality.

## P-070 — cleaning plan

A source SHA-256 identifies the immutable input. Only a small allowlist of plan operations is accepted. The tool writes no output and changes no dataset. A later executor must preserve the original, version the derivative and produce row-count/semantic-loss evidence.

## P-071 — PII scan plan

The reference accepts only boolean field-classification hints and recommends a reviewed local PII engine such as Presidio. It **does not run a PII scan**. No flags does not mean no PII; false positives and false negatives require measured acceptance testing.

## P-072 — duplicate summary

Exact duplicate detection operates only on caller-supplied SHA-256 record digests. Raw records are not ingested. Matching hashes can identify exact-equality candidates; semantic/near-duplicate detection is explicitly out of scope for this layer.

## P-073 — license/provenance preflight

Requires bounded dataset/source identifiers, source SHA-256 and explicit collection-basis/consent documentation state. Missing license or collection-basis evidence forces review. Metadata presence is not a legal conclusion and does not prove data rights.

## P-075 — low-resource-language program planning

The planner orders language records by governance readiness and validated-example scarcity without collecting data. Collection readiness requires provenance, collection-basis/consent and license review. Future work must include community participation, cultural review and protection against extracting private communications by default.

## Privacy/security boundary

This reference module:

- reads no dataset row content;
- accepts no arbitrary free-text samples;
- uploads no data;
- performs no PII scan/redaction;
- modifies/cleans no dataset;
- publishes no dataset;
- retains hashes/counts/booleans/identifiers only;
- makes no rights, privacy-completeness or data-quality certification.

## Beginner experience

A future UI should explain evidence gaps directly, for example:

> **Do not publish this dataset yet.** The source is identified, but its license and collection basis still need review. Nothing was uploaded or changed.

## Accessibility / multilingual design

Dataset-governance status should be available as plain language, semantic tables and non-color-only status labels. Low-resource-language work must involve speakers/communities rather than treating a language identifier and example count as cultural adequacy.

## Completion gaps

All mapped IDs remain IN PROGRESS. Completion requires real dataset adapters and sanitized fixtures, measured PII-engine behavior, provenance/data-rights workflows, reversible/versioned cleaning execution, exact + near-duplicate strategy where justified, accessibility/multilingual review, community acceptance for low-resource-language collection, public release/version evidence, contribution paths and canonical completion records.
