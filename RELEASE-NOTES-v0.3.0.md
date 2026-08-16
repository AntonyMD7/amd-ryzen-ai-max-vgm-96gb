# DAIS Evidence Validation Action v0.3.0

Roadmap ID: `P-050 Evidence Validation Action`

This release packages the DAIS Universal Evidence schema/hash validator as a bounded GitHub composite Action with an immutable, reproducible runtime contract and explicit provenance interoperability.

## Highlights

- Draft 2020-12 DAIS Universal Evidence validation using `jsonschema`;
- optional exact local artifact SHA-256 verification without executing artifacts;
- traversal, absolute-path and symlink-escape refusal;
- duplicate artifact-name refusal;
- bounded artifact count and per-artifact size;
- deterministic record/schema identity;
- atomic machine-readable validation report;
- CI outputs for status, failure counts, verified count, report path and report SHA-256;
- Linux x64 / CPython 3.12 runtime gate;
- complete hash-locked binary-wheel dependency graph;
- positive exact-hash and required traversal negative-control CI;
- real GitHub signed-attestation interoperability for the exact validator report with independent `gh attestation verify`;
- beginner, engineer, privacy, recovery, accessibility and multilingual-path documentation;
- dedicated privacy-safe public support issue form.

## What PASS means

A P-050 `PASS` means the evidence record conforms to the supported DAIS schema and, when artifact checking is enabled, each directly referenced local artifact has the declared SHA-256 value.

It does **not** prove that the described event occurred, authenticate the producer, establish authorization, prove artifact safety/correctness, or make a semantic claim true. Signed provenance/attestation remains a separate verification layer.

## Runtime scope

The v0.3.0 Action intentionally supports Linux x64 with CPython 3.12. The dependency graph is exact-version and wheel-SHA-256 locked. Unsupported runtime/platform combinations fail rather than silently falling back.

## Bundle scope

Recursive/nested evidence bundles are not part of v0.3.0. One invocation validates one evidence record and its directly declared artifacts. This avoids hidden recursion, cycle and resource semantics.

## Safety and privacy

The validator is read-only with respect to evidence/artifacts, performs no network request itself, and never executes referenced artifacts. Validation does not redact sensitive content; callers remain responsible for supplying sanitized evidence appropriate to its retention/publication context.

## Recovery

If execution is interrupted, dependency installation fails, or report publication fails, discard the incomplete result and rerun against unchanged inputs. A missing/partial/FAIL result must never be promoted to success.

## Completion boundary

Publishing v0.3.0 is a release gate, not by itself a roadmap-completion claim. `P-050` can be promoted to COMPLETE only after the immutable released ref is consumed from independent public-project fixtures, release/tag identity is independently verified, the canonical 19-gate completion record passes, final handover is published, and fresh post-release verification succeeds.
