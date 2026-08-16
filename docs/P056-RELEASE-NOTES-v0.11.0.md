# DAIS License Compliance Checker v0.11.0

Roadmap ID: **P-056 — License Compliance Checker**

## Release scope

v0.11.0 is the first product release candidate for the DAIS License Compliance Checker. It turns the earlier supply-chain planning reference into a reusable GitHub composite Action and local Python evidence wrapper around the established REUSE ecosystem.

The released scope is deliberately narrow and testable:

- GitHub-hosted Ubuntu/Linux composite Action;
- exact top-level package `reuse==6.2.0`;
- upstream REUSE Specification **3.3**;
- fixed `reuse lint --json` audit only;
- `REUSE_COMPLIANT` / `REUSE_NONCOMPLIANT` truth-preserving status;
- deterministic privacy-minimized JSON evidence;
- separate runner-temporary raw REUSE report for local remediation;
- English and Spanish beginner guidance over the same technical state;
- no repository mutation, GitHub API mutation, arbitrary tool arguments, shell-command injection, legal verdict or license-compatibility verdict.

## Search-before-build and upstream choice

This product does **not** implement another license parser. REUSE remains the specialist compliance authority and SPDX remains the license-expression vocabulary.

Fresh review before productization confirmed:

- official REUSE 6.2.0 documentation defines `reuse lint --json` for project compliance evidence;
- REUSE 6.2.0 reports against REUSE Specification 3.3;
- official `fsfe/reuse-action` tag `v6.0.0` resolves to commit `676e2d560c9a403aa252096d99fcab3e1132b0f5`;
- that upstream Action's Dockerfile uses moving image reference `fsfe/reuse:6`, so P-056 does not describe it as a completely immutable execution dependency.

The DAIS Action instead creates an ephemeral Python environment, installs exact `reuse==6.2.0`, verifies the observed tool version and records the SHA-256 of sorted `pip freeze --all`. This improves runtime evidence while **not claiming a fully hash-locked transitive dependency closure**.

## Source acceptance already passed

Productization PR #124 exercised the candidate at exact head `fc3a22a98d431401ab8386fafd943298ee5240df` and merged to canonical public main `cdad72cffafe5772e6456207991dd33cc7bb5d06`.

Acceptance workflow run `31944118421` passed both jobs:

- adversarial P-056 contract tests;
- real REUSE 6.2.0 acceptance on a compliant disposable fixture;
- real REUSE 6.2.0 acceptance on an intentionally noncompliant disposable fixture;
- pinned real-public `AntonyMD7/learning-git@01723a1825113de08810193f37e8047d978433c2` classification;
- consumer README and Git worktree immutability;
- sanitized-evidence checks preventing upstream filename/copyright leakage.

Sanitized source-acceptance artifact:

- artifact ID `9262815302`;
- digest `sha256:74e4ac6e5ef192514b58b885418f75de17fc783cbbd1fb8f694ffd6097e86390`.

## Security and privacy

The composite Action requires only `contents: read` in ordinary consumer workflows. It accepts no token and uploads nothing itself.

The wrapper fails closed on tool/spec version mismatch, malformed JSON, unsafe root/output paths, symlink targets, malformed evidence identities, oversized raw output and timeout. The subprocess command is fixed and uses `shell=False`.

The sanitized report excludes repository-relative file paths, copyright identities, upstream recommendation text and literal used-license identifiers. The raw upstream JSON remains separately available in runner-temporary storage and **must not be blindly uploaded from private repositories**.

## Legal and semantic boundary

A P-056 `REUSE_COMPLIANT` result means the pinned upstream REUSE tool reported the exact audited snapshot compliant with REUSE Specification 3.3 under the recorded run environment.

It does **not** establish:

- legal advice or permission to redistribute;
- compatibility among licenses or organizational policies;
- dependency-license safety;
- completeness of third-party notices;
- repository security;
- production/distribution approval.

A `REUSE_NONCOMPLIANT` result is a successful audit with findings, not a tool malfunction.

## Accessibility and localization

The product emits text-first Markdown guidance in English and Spanish. Localization never changes the underlying technical JSON state. This release does not claim WCAG conformance or human multilingual acceptance.

## Recovery

The audit itself is read-only. Failed execution can be recovered by discarding the temporary environment/output, correcting the input/tool condition and rerunning. Any repository metadata fix remains a separate reviewed Git change and can be reverted normally.

## Completion boundary

Publishing `v0.11.0` will not by itself mark P-056 COMPLETE. Completion still requires successful governed exact-source publication, fresh released-ref public-consumer acceptance, retained evidence, an independent canonical 19-gate completion audit, final handover/build record, post-merge verification and canonical DAIS status synchronization.
