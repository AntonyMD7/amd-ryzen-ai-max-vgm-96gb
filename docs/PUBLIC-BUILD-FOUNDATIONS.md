# Public-Build Foundations — Reference Implementation v0.1

This hardware-specific repository is being used as a proving ground for four reusable patterns from the DAIS public-build roadmap: **SafeFix** (`F-01` / `P-211`), **Universal Evidence Standard** (`F-05` / `P-212`), **Local AI Doctor** (`F-03` / `P-027`), and **Hardware Compatibility Commons** (`F-04` / `P-220`).

This document records **reference implementations**, not a claim that any flagship foundation is complete or externally standardized.

## Why build here first?

The VGM workflow is a real, consequential configuration problem with a useful safety test surface: discovery can be read-only, mutation requires an explicit gate, restart may interrupt connectivity, and success cannot be trusted until post-reboot state is independently attested. The repository also concerns AI-capable hardware and community compatibility evidence, making it a suitable place to test generic contracts before extraction into dedicated public repositories.

## Existing open-source landscape reviewed

The public-build rule is to search before building. Adjacent projects include:

- **in-toto Attestation Framework** — general attestation envelopes and predicates;
- **SLSA provenance ecosystem** — software supply-chain provenance and verifiable build lineage;
- **OpenTelemetry** — vendor-neutral traces, metrics and logs for operational observability;
- **SPDX** — standardized software package and licensing metadata;
- **hw-probe / Linux Hardware Database** — hardware probing and community compatibility evidence on Linux.

These should be adopted or interoperated with where their scope fits. The DAIS drafts are narrower in a different direction: they represent the safety lifecycle of troubleshooting/configuration operations, evidence required to justify success, privacy-safe capability discovery, and portable compatibility reports.

The intent is **not** to replace established standards. Future work should provide mappings/exporters instead of inventing parallel representations for provenance, SBOMs or telemetry.

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

It captures schema/evidence identity, roadmap IDs, subject identity, evidence type, operation classification, intended change and authorization, timestamps, pre/post-state, results/exit codes, hashes, rollback state, acceptance results, redaction declarations, provenance and limitations.

For a `MUTATING` record, the schema fails closed unless recovery is established, required human approval is present, and a non-empty authorization reference is recorded.

A sanitized non-live example is in `examples/universal-evidence-readonly-example.json`.

## Local AI Doctor v0.1 discovery lane

`scripts/local_ai_readiness.py` is a cross-platform, read-only readiness collector. It deliberately stops at capability signals rather than making unsupported model-fit claims.

It reports:

- OS, release and machine architecture;
- total physical memory when the platform exposes it safely;
- presence/version signals for Python, Ollama, NVIDIA tooling and ROCm tooling;
- explicit privacy declarations showing that usernames, hostnames, network addresses, environment values and credentials are not collected;
- explicit mutation declarations showing no installs, model downloads, driver changes or configuration changes occurred;
- required next checks before model/backend recommendations are allowed.

It does **not** install an inference backend, download a model, change a driver, enumerate private network state, or claim that a model will run because a machine merely has enough RAM.

## Hardware Compatibility Commons v0.1

`schemas/hardware-compatibility-report-v0.1.schema.json` defines a portable, privacy-sanitized compatibility report covering hardware, OS/driver/runtime/firmware context, configuration, observation state, evidence method/hashes, privacy declarations and limitations.

The status vocabulary distinguishes `VERIFIED`, `DISCOVERY_ONLY`, `COMMUNITY_REPORTED`, `UNSUPPORTED` and `UNKNOWN` so community reports cannot silently become verified facts.

## Beginner view

A beginner should be able to see:

> **What are we checking?** Whether this machine supports the requested capability or change.  
> **Will this step change anything?** No — the discovery lane is read-only.  
> **What happens before a risky change?** Recovery and approval must be ready first.  
> **How do we know it worked?** We check the machine again afterward and retain evidence.

## Engineer view

An engineer should be able to inspect the exact state machine, JSON Schemas, collector source, source commit, tests, hashes, exit codes, safety flags, compatibility status and retained evidence references.

## Security and privacy review

The generic records intentionally do not require usernames, addresses, tokens, environment variables, command-line secrets, SSH material, message content or private infrastructure identifiers. Producers must sanitize evidence before public release.

Public schema records require affirmative redaction declarations. These declarations are not a substitute for secret scanning; CI and human review remain required.

The Local AI collector runs only bounded version/presence checks and does not read model prompts, user files, network addresses or credentials.

## Accessibility review

Machine-readable evidence is separated from presentation. Front ends can therefore expose the same record as plain language, large text, screen-reader-friendly semantic HTML, multilingual explanations or raw engineering JSON without weakening the underlying safety gates.

## Current maturity

| Roadmap item | State | Evidence in this branch |
|---|---|---|
| F-01 SafeFix | IN PROGRESS | state contract + tests + real VGM workflow mapping |
| F-05 Universal Evidence Standard | IN PROGRESS | JSON Schema + sanitized example + validation tests |
| F-03 Local AI Doctor | IN PROGRESS | read-only cross-platform readiness collector + privacy/mutation tests |
| F-04 Hardware Compatibility Commons | IN PROGRESS | portable compatibility-report schema + existing VGM issue/evidence workflow |
| P-021 AI Hardware Readiness Tester | IN PROGRESS | readiness collector baseline |
| P-027 Local AI Doctor | IN PROGRESS | discovery lane baseline; recommendation/verification lanes remain |
| P-211 SafeFix Framework | IN PROGRESS | reference state contract; extraction still required |
| P-212 Universal Evidence Schema | IN PROGRESS | draft schema; external interoperability review still required |
| P-220 Hardware Compatibility Commons | IN PROGRESS | report schema + VGM-specific community proving ground |

## What remains before COMPLETE

None of these items should be marked complete yet. Outstanding gates include dedicated public distribution surfaces, versioned releases/tags, broader cross-platform reference implementations, independent real-world acceptance outside this VGM use case, explicit mappings to adjacent standards, stronger accelerator/runtime adapters, accessibility validation in an actual UI, multilingual validation, community review and canonical completion records.

## Extraction rule

When repository-creation tooling is available, extract generic contracts into dedicated public repositories while preserving history/provenance. The hardware-specific project should then consume pinned versions rather than becoming the permanent home of universal standards.
