# Universal Evidence Validation Action v0.3.0 release candidate

Status: **IN PROGRESS — release candidate; completion requires released-ref acceptance and final completion evidence**

Roadmap mapping: `P-050 Evidence Validation Action`; reusable by `F-05 Universal Evidence Standard`, `P-212 Universal Evidence Schema`, `P-213 Evidence-First Automation Library`, and `P-214 Recovery-First Mutation Framework`.

## What this product does

P-050 gives GitHub workflows a small, fail-closed validation boundary for DAIS Universal Evidence. It validates evidence JSON against the repository's Draft 2020-12 schema and can independently hash explicitly referenced local artifacts without executing them.

The reusable composite Action returns machine-readable outputs:

- `status` — `PASS` or `FAIL`;
- `schema-error-count`;
- `artifact-failure-count`;
- `verified-artifact-count`;
- `report-path`;
- `report-sha256`.

The Python validator can also atomically write the complete report with `--result-file`.

## Search-before-build decision

Generic JSON Schema validation is already mature. `python-jsonschema` provides the Draft 2020-12 implementation used here, and `check-jsonschema` provides a general-purpose CLI/pre-commit validation experience. P-050 therefore stays deliberately narrow instead of recreating general JSON Schema tooling.

The in-toto Attestation Framework and GitHub artifact attestations cover authenticated provenance. P-050 does not create another signer, OIDC provider, transparency system or attestation format. Its canonical-main interoperability lane signs the exact P-050 validator report with GitHub's attestation system and then independently verifies it with `gh attestation verify`, while keeping validation and provenance as separate claims.

## Components

- `scripts/evidence_validate.py` — schema, bounded artifact and digest validator;
- `.github/actions/evidence-validate/action.yml` — reusable composite GitHub Action wrapper;
- `.github/actions/evidence-validate/requirements-linux-x64-py312.lock` — exact hash-locked runtime dependency graph;
- `tests/test_evidence_validate.py` — schema, mutation, digest, traversal, symlink, ambiguity, resource-bound and immutability tests;
- `.github/workflows/p050-evidence-validation-action.yml` — dedicated hosted positive/negative Action acceptance plus signed-attestation interoperability;
- `docs/P050-EVIDENCE-VALIDATION-START-HERE.md` — beginner/operator path;
- `.github/ISSUE_TEMPLATE/p050-evidence-validation.yml` — privacy-safe public support path;
- `RELEASE-NOTES-v0.3.0.md` — release scope and limitations.

## Hardening and reproducibility

The release candidate includes controls a generic happy-path schema check would miss:

1. **Ambiguity refusal.** Duplicate artifact names fail closed.
2. **Path containment.** Absolute paths, `..` traversal and symlink escapes outside the artifact root are rejected.
3. **Bounded work.** Callers can cap artifact count and bytes hashed per artifact.
4. **Input immutability.** Validation never rewrites evidence or artifact bytes.
5. **Deterministic identity.** Reports include canonical record/schema SHA-256 identities.
6. **Atomic report output.** Result files use write/fsync/replace semantics.
7. **CI-native outputs.** Bounded outputs and annotations are emitted while retaining full JSON detail.
8. **Negative-control acceptance.** CI requires a real exact-hash PASS and traversal FAIL.
9. **Fail-closed runtime scope.** Released use is Linux x64 / CPython 3.12 only.
10. **Hash-locked dependencies.** `jsonschema`, `attrs`, `jsonschema-specifications`, `referencing` and `rpds-py` are exact-version and wheel-SHA-256 locked, installed with `--require-hashes --only-binary=:all:`.
11. **Signed provenance interoperability.** Canonical-main CI attests the exact validator report through GitHub artifact attestations and independently verifies it.

## Beginner view

> **What does PASS mean?** The evidence file follows the expected DAIS structure. If artifact checking was enabled, the local files checked have the SHA-256 values written in the evidence.
>
> **What does PASS not mean?** It does not prove the event really happened, the producer was authorized, or the artifact is safe/correct.

See `docs/P050-EVIDENCE-VALIDATION-START-HERE.md` for the shortest safe usage path.

## Engineer usage

```yaml
- uses: actions/checkout@v4

- uses: actions/setup-python@v5
  with:
    python-version: '3.12'

- name: Validate DAIS evidence
  id: evidence
  uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/evidence-validate@v0.3.0
  with:
    evidence: evidence/result.json
    artifact-root: evidence/artifacts
    max-artifacts: '64'
    max-artifact-bytes: '104857600'

- name: Gate on result
  if: ${{ steps.evidence.outputs.status != 'PASS' }}
  run: exit 1
```

After release, high-assurance consumers can independently resolve `v0.3.0` and pin the exact commit.

## Runtime and supply-chain boundary

The Action fails unless `runner.os == Linux`, `runner.arch == X64`, and the active interpreter is CPython 3.12. It then installs the checked-in exact hash-locked binary-wheel dependency graph. This establishes reproducible dependency selection for the declared runtime; it does not prove those dependencies are vulnerability-free or semantically trustworthy.

## Security and privacy review

The validator performs no network request, launches/imports no artifact, and modifies no evidence/artifact input. The wrapper's only external dependency activity is installation of the hash-locked runtime packages required for the declared release environment.

Evidence content may itself contain sensitive information. P-050 validates shape and hashes; it is **not** a redaction/data-classification engine. Public workflows must supply sanitized evidence suitable for public retention.

GitHub annotations are emitted only from validator-generated summaries and are bounded to the first 20 schema/artifact failures.

## Accessibility review

P-050 is primarily a machine/CLI Action. Failures are text-first and do not require a visual dashboard: PASS/FAIL is textual, counts are machine-readable, annotations include categories plus plain-language reasons, and the complete JSON report remains accessible to assistive tooling.

This is not a WCAG conformance or human assistive-technology acceptance claim. Any future web interface requires its own accessibility acceptance.

## Multilingual path

Canonical keys stay stable English identifiers for interoperability. Human-facing documentation can be localized independently. Current released documentation is English-first; multilingual user acceptance is not claimed.

## Recovery and failure behavior

P-050 is read-only with respect to evidence/artifacts, so input rollback is unnecessary. If validation is interrupted, dependency installation fails, or atomic report publication fails, discard the result and rerun against unchanged inputs. Consumers must never promote a missing, partial or `FAIL` result.

## Trust boundary and interoperability

A valid record is not proof that a claimed event happened. A P-050 report can establish only the represented checks:

- schema conformance;
- bounded local artifact presence/type;
- SHA-256 equality when artifact hashing is requested;
- the validator's non-execution/non-input-mutation contract.

Producer identity, authorization, signed provenance, semantic correctness, artifact goodness and real-world event truth require separate evidence. The GitHub signed-attestation acceptance lane demonstrates this composition without merging the claims.

## Nested evidence bundles

Recursive/nested evidence-bundle traversal is explicitly **not part of v0.3.0**. Each invocation validates one evidence record and directly declared artifacts only. This avoids underspecified cycle, depth and aggregate-resource behavior and keeps P-050 a validator rather than a workflow engine. Any future nested protocol must be separately versioned and bounded.

## Completion gates remaining

The source, runtime reproducibility, hosted validation acceptance, signed-attestation interoperability, beginner/engineer documentation and support surface are now built. `P-050` remains **IN PROGRESS** until all of the following are evidenced:

- publish the immutable `v0.3.0` P-050 release surface bound to exact reviewed source;
- exercise that released Action ref from at least two independent public-project fixtures;
- independently verify public release/tag identity and retain the released-ref acceptance evidence;
- produce and pass the canonical 19-gate P-050 completion record;
- publish the final P-050 handover/build record and perform fresh post-release verification.

No source/CI result alone promotes roadmap completion.