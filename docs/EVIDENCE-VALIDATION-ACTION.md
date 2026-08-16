# Universal Evidence Validation Action v0.2

Status: **IN PROGRESS — productized validation tranche**

Roadmap mapping: `P-050 Evidence Validation Action`; reusable by `F-05 Universal Evidence Standard`, `P-212 Universal Evidence Schema`, `P-213 Evidence-First Automation Library`, and `P-214 Recovery-First Mutation Framework`.

## What this product does

P-050 gives a GitHub workflow a small, fail-closed validation boundary for DAIS Universal Evidence. It validates the evidence JSON against the repository's Draft 2020-12 schema and can independently hash explicitly referenced local artifacts without executing them.

The reusable composite Action now returns machine-readable outputs for downstream gates:

- `status` — `PASS` or `FAIL`;
- `schema-error-count`;
- `artifact-failure-count`;
- `verified-artifact-count`;
- `report-path`;
- `report-sha256`.

The Python validator can also atomically write the complete report with `--result-file`.

## Search-before-build decision

Generic JSON Schema validation is already mature. `python-jsonschema` provides the Draft 2020-12 implementation used here, while `check-jsonschema` already provides a general-purpose CLI/pre-commit validation experience. P-050 therefore remains deliberately narrow rather than competing with those tools.

GitHub artifact attestations and the in-toto Attestation Framework cover producer/build provenance and signed predicates. GitHub's current artifact-attestation workflow uses its `actions/attest` family and supports verification through GitHub tooling. P-050 does **not** create another signing system, transparency log, OIDC identity system or attestation format. A future released P-050 can consume separately verified attestation observations, but schema/hash validation and producer authentication remain distinct claims.

## Components

- `scripts/evidence_validate.py` — schema, bounded artifact and digest validator;
- `.github/actions/evidence-validate/action.yml` — reusable composite GitHub Action wrapper;
- `tests/test_evidence_validate.py` — schema, mutation, digest, traversal, symlink, ambiguity, resource-bound and immutability tests;
- `.github/workflows/p050-evidence-validation-action.yml` — dedicated real composite-action acceptance with positive exact-hash evidence and a traversal negative control.

## v0.2 hardening

The v0.2 tranche adds controls that a generic happy-path schema check would miss:

1. **Ambiguity refusal.** Duplicate artifact names fail closed rather than allowing two evidence entries to identify one path ambiguously.
2. **Path containment.** Absolute paths, `..` traversal and symlink escapes outside the configured artifact root are rejected.
3. **Bounded work.** Callers can cap the number of artifacts and per-artifact bytes hashed. Defaults are 256 artifacts and 1 GiB per artifact.
4. **Input immutability.** Validation does not rewrite the evidence record or artifact bytes.
5. **Deterministic identity.** The result includes canonical JSON SHA-256 values for the input record and schema.
6. **Atomic report output.** `--result-file` uses write/fsync/replace semantics so consumers do not mistake a partially written report for a completed validation result.
7. **CI-native outputs.** The composite Action publishes bounded outputs and GitHub annotations while retaining a complete JSON report.
8. **Negative-control acceptance.** Dedicated hosted CI requires a real exact-hash fixture to pass and a traversal fixture to fail.

## Beginner view

> **What does PASS mean?** The evidence file follows the expected DAIS structure. If artifact checking was enabled, the local files we checked have the SHA-256 values written in the evidence.
>
> **What does PASS not mean?** It does not prove that the event really happened, that the person/system producing the evidence was authorized, or that the artifact itself is safe or correct.

## Engineer usage

```yaml
- name: Validate DAIS evidence
  id: evidence
  uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/evidence-validate@<reviewed-ref>
  with:
    evidence: evidence/result.json
    artifact-root: evidence/artifacts
    max-artifacts: '64'
    max-artifact-bytes: '104857600'

- name: Gate on machine-readable result
  if: ${{ steps.evidence.outputs.status == 'PASS' }}
  run: echo "Validated report ${{ steps.evidence.outputs.report-sha256 }}"
```

Until a dedicated P-050 release ref is published, callers should pin a reviewed immutable commit rather than `main`.

## Security and privacy review

The validator makes no network request, launches no artifact, imports no artifact and modifies no evidence/artifact input. The wrapper currently contacts the Python package index to install exact top-level `jsonschema==4.26.0`; transitive dependency locking/verification remains an explicit release blocker.

Evidence content can itself contain sensitive information. P-050 validates shape and hashes; it is **not a redaction or data-classification engine**. Public workflows must supply sanitized evidence appropriate for public retention.

GitHub workflow commands are emitted only from validator-generated summaries. The Action bounds annotation count to the first 20 schema and artifact failures to avoid unbounded log/annotation amplification.

## Accessibility review

The product is primarily a machine/CLI Action, so its accessibility obligation is to make failures understandable without requiring a visual dashboard. PASS/FAIL is represented in text, counts are machine-readable, failure annotations include both a category and plain-language reason, and the complete JSON report remains available to assistive tooling.

This is not a WCAG conformance claim. A future web UI would require its own keyboard, screen-reader, reflow, contrast and real-user acceptance.

## Multilingual path

The canonical machine representation and output keys remain stable English identifiers for interoperability. Beginner-facing documentation can be translated without changing evidence semantics. Error strings are currently English; multilingual human-facing rendering is therefore considered architecturally supported but not yet multilingual user acceptance.

## Recovery and failure behavior

P-050 is read-only with respect to evidence and artifacts, so rollback of input data is not required. If validation is interrupted, discard the result report and rerun against the same evidence/artifact bytes. Consumers must never promote a missing, partial or `FAIL` result to success.

If dependency installation fails, the Action fails before validation. If `--result-file` cannot be written atomically, the CLI exits non-zero. No fallback silently disables schema or hash checks.

## Trust boundary and interoperability

A valid record is **not proof that the claimed event happened**. It proves only the checks explicitly represented by the report:

- schema conformance;
- bounded local artifact presence/type;
- SHA-256 equality when artifact hashing is requested;
- the validator's own non-execution/non-network/non-input-mutation contract.

Producer identity, authorization, signed provenance, transparency, trusted timestamps, semantic correctness, artifact goodness and real-world acceptance require separate evidence. F-05 already contains Sigstore/Cosign/TUF and signed in-toto/SLSA-style evidence tranches; P-050 should compose those verified observations rather than conflate them with JSON/hash validation.

## Completion gaps after v0.2

`P-050` remains **IN PROGRESS**. This tranche deliberately does not manufacture completion. Remaining gates are:

- publish a versioned immutable P-050 Action release surface;
- lock/verify the full runtime dependency graph or ship an equivalently reproducible runtime, with retained supply-chain evidence;
- exercise the released immutable Action ref from at least two independent public-project fixtures;
- add explicit signed-attestation interoperability acceptance rather than documentation-only mapping;
- decide whether recursive/nested evidence bundles are part of P-050 scope and, if so, specify cycle/depth/size rules;
- publish final contribution/support surfaces and release notes specific to P-050;
- produce the canonical 19-gate completion record, final handover and fresh post-release verification.

Those are release/completion gates, not reasons to weaken the v0.2 validator.