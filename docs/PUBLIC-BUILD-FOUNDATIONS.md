# Public-Build Foundations — Reference Implementation v0.1

This repository is a hardware-specific project, but its safety and evidence work exposes two patterns that are intentionally reusable across the DAIS public-build roadmap: **SafeFix** (`F-01` / `P-211`) and the **Universal Evidence Standard** (`F-05` / `P-212`).

This document records a **reference implementation**, not a claim that either flagship foundation is complete or externally standardized.

## Why build here first?

The VGM workflow is a real, consequential configuration problem with an unusually useful test surface: discovery can be read-only, mutation requires an explicit gate, restart may interrupt connectivity, and success cannot be trusted until post-reboot state is independently attested. That makes it a strong proving ground before extracting the generic contracts into a dedicated repository.

## Existing open-source landscape reviewed

The public-build rule is to search before building. The following projects cover important adjacent areas:

- **in-toto Attestation Framework** — a general envelope and predicate model for attestations.
- **SLSA provenance ecosystem** — software supply-chain provenance and verifiable build lineage.
- **OpenTelemetry** — vendor-neutral telemetry/traces/metrics/logs, useful for operational observability.
- **SPDX** — standardized software package and licensing metadata.
- **hw-probe / Linux Hardware Database** — hardware probing and community compatibility evidence on Linux.

These should be adopted or interoperated with where their scope fits. The DAIS draft is narrower in a different direction: it records the safety lifecycle of a troubleshooting or configuration operation, including explicit read-only-versus-mutation classification, authorization, recovery readiness, post-state verification, and user-facing acceptance evidence.

The intent is **not** to replace those standards. Future work should provide mappings/exporters rather than inventing parallel representations for provenance, SBOMs, or telemetry.

## SafeFix v0.1 contract

Canonical lifecycle:

```text
DISCOVER
  -> VERIFY
  -> PREFLIGHT
  -> APPROVE
  -> MUTATE
  -> RESTART (only when required)
  -> ATTEST
  -> PUBLISH_EVIDENCE
```

The reference implementation is `scripts/safefix_contract.py`.

### Non-negotiable invariants

1. Discovery and verification do not imply permission to mutate.
2. Mutation is blocked unless recovery is established.
3. If approval is required, mutation is blocked without recorded approval.
4. A restart cannot be treated as evidence of success.
5. Success cannot be published before post-change attestation.
6. A tool described as read-only must not hide a mutating adapter.
7. Retry semantics for mutating operations must be explicit; a lost connection is not evidence that a write failed.

The current module only validates state transitions. It deliberately contains **no command executor**.

## Universal Evidence Standard v0.1

The draft JSON Schema is `schemas/universal-evidence-v0.1.schema.json`.

It captures:

- schema and evidence identity;
- roadmap/project IDs;
- subject identity and optional version;
- evidence type;
- operation classification (`READ_ONLY`, `MUTATING`, `VERIFY`);
- intended change and authorization reference;
- observation timestamp;
- pre-state and post-state;
- result and exit code;
- content hashes for retained artifacts;
- rollback/recovery state;
- acceptance-test results;
- mandatory redaction declarations;
- source/provenance metadata;
- known limitations.

For a `MUTATING` record, the schema fails closed unless the record declares recovery established, human approval required/present, and a non-empty authorization reference.

A sanitized non-live example is in `examples/universal-evidence-readonly-example.json`.

## Beginner view

A beginner should be able to see:

> **What are we checking?** Whether this machine supports the requested change.  
> **Will this step change anything?** No — this is read-only discovery.  
> **What happens before a risky change?** Recovery and approval must be ready first.  
> **How do we know it worked?** We check the machine again after the change/restart and retain evidence.

## Engineer view

An engineer should be able to inspect the exact state machine, JSON Schema, source commit, tests, hashes, exit codes, safety flags, and retained evidence references.

## Security and privacy review

The generic evidence schema intentionally does not require usernames, addresses, tokens, environment variables, command-line secrets, SSH material, message content, or private infrastructure identifiers. Producers must sanitize evidence before public release.

`secrets_redacted` and `private_infrastructure_redacted` are hard-coded to `true` in schema-valid public records. This is a declaration and not a substitute for secret scanning; CI and human review remain required.

## Accessibility review

The contract separates machine-readable evidence from presentation. Front ends can therefore expose the same record as plain language, large text, screen-reader-friendly semantic HTML, multilingual explanations, or raw engineering JSON without weakening the underlying safety gates.

## Current maturity

| Roadmap item | State | Evidence in this branch |
|---|---|---|
| F-01 SafeFix | IN PROGRESS | state contract + tests + real VGM workflow mapping |
| F-05 Universal Evidence Standard | IN PROGRESS | JSON Schema + sanitized example + validation tests |
| P-211 SafeFix Framework | IN PROGRESS | same reference implementation; extraction still required |
| P-212 Universal Evidence Schema | IN PROGRESS | same draft schema; external interoperability review still required |

## What remains before COMPLETE

Neither foundation should be marked complete yet. Outstanding gates include a dedicated public distribution surface, versioned release/tag, broader cross-platform reference implementations, independent real-world acceptance outside this VGM use case, explicit mappings to adjacent standards, accessibility validation in an actual UI, multilingual validation, community review, and a canonical completion record.

## Extraction rule

When repository-creation tooling is available, extract the generic contracts into dedicated public repositories while preserving history/provenance. The hardware-specific project should then consume pinned versions rather than becoming the permanent home of universal standards.
