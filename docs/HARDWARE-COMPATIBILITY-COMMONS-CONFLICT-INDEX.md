# Hardware Compatibility Commons conflict-preserving index v0.3

Status: **IN PROGRESS — public evidence indexing, not certification**  
Canonical foundation: **F-04 Hardware Compatibility Commons**.

## Purpose

The v0.2 intake validator can decide whether one submitted report is structurally valid, privacy-safe and semantically eligible for public review. A commons also needs to combine many reports without turning popularity into truth or hiding contradictory outcomes.

This tranche adds that aggregation boundary.

## Exact-context grouping

Reports are grouped only when the following sanitized context is exactly equivalent after canonical JSON normalization:

- hardware vendor/model/architecture/memory/accelerator/device class;
- OS/version/kernel/driver/runtime/firmware fields;
- configuration key/value pairs.

A SHA-256-derived context identifier is used for grouping. This is not a unique-device identifier; the public schema already prohibits serial numbers, UUIDs, MAC addresses, usernames, hostnames, private addresses and user paths.

## Intake is mandatory

Every report is passed through the existing `hardware_compatibility_intake.py` validator before indexing. An unsafe or semantically invalid report causes the index operation to fail closed rather than silently omit or auto-redact it.

Exact duplicate report digests are deduplicated so reposting the same bytes cannot inflate evidence counts.

## Conflict semantics

The index never resolves contradictory verified evidence by majority vote.

If the same exact context contains both `VERIFIED_WORKING` and `VERIFIED_FAILING`, its aggregate state is:

`CONFLICT_REQUIRES_REVIEW`

Working-only evidence is labeled `WORKING_EVIDENCE_PRESENT_NO_UNIVERSAL_CLAIM`; failing-only evidence is similarly bounded. Synthetic schema-conformance fixtures are counted separately and are never treated as real hardware observations.

## What the index never claims

Every aggregate explicitly keeps these claims false:

- universal compatibility guarantee;
- future-version guarantee;
- safe-to-auto-apply;
- compatibility certification;
- conflict auto-resolution;
- majority-vote-as-truth;
- synthetic-evidence-as-real-hardware.

## Why this matters

Compatibility is conditional on versions, firmware, drivers, runtimes, configuration and workload. A public commons becomes dangerous if it compresses conflicting evidence into a green badge with no provenance. This index instead preserves the disagreement so maintainers and users can inspect the evidence and reproduce the condition.

## Remaining F-04 gates

F-04 remains **IN PROGRESS**. The canonical completion path still needs a dedicated commons/distribution, community ingestion and moderation, independent real-device reports, reviewed taxonomy/versioning, search/browse UX, accessibility and multilingual validation, abuse/spam handling, public release/versioning and retained completion evidence.
