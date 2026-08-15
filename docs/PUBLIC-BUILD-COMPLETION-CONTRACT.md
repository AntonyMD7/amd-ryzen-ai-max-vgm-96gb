# DAIS Public-Build Completion Contract Auditor

Status: **IN PROGRESS infrastructure — completion auditor, not a completion claim**

This utility makes the canonical `DAIS_PUBLIC_BUILD_OPPORTUNITY_MASTER_ROADMAP_v1.0.md` completion contract machine-checkable without weakening it.

The roadmap deliberately distinguishes **source exists** from **project complete**. The auditor preserves that distinction. It cannot turn a merged PR, green CI run, schema-valid evidence file, automated accessibility scan, or public repository into a completion claim by itself.

## Why this exists

The 227-opportunity program has reached public source/reference coverage across the canonical IDs. The next risk is administrative drift: as projects mature, different agents could interpret “done” differently or accidentally promote source/CI evidence into a stronger claim.

`scripts/public_build_completion_contract.py` gives every `P-001..P-227` and `F-01..F-06` the same fail-closed vocabulary.

It checks:

- all 19 canonical completion gates are present;
- `PASS` always names evidence;
- `NOT_APPLICABLE` is an explicit reviewed decision with rationale;
- canonical roadmap IDs are preserved;
- all Project Completion Record fields exist;
- `COMPLETE` is rejected when any applicable gate is unresolved;
- a fully evidenced `IN_PROGRESS` record becomes `READY_FOR_CANONICAL_COMPLETION_REVIEW`, **not automatically COMPLETE**;
- obvious token/private-key/secret patterns are rejected from public evidence.

The auditor is dependency-free and does not access the network, execute project code, alter repositories, create releases, or mutate a device.

## Search-before-build / upstream boundary

DAIS should not replace specialist ecosystems that already define narrower project-health concerns.

- **GitHub community profiles** already identify common public-repository health files such as README, LICENSE, CONTRIBUTING and CODE_OF_CONDUCT. DAIS records completion evidence but does not recreate GitHub's community-profile feature.
- **REUSE** provides a machine-readable licensing specification at file/project level. DAIS records whether the canonical open-source-license gate is evidenced; it does not make legal conclusions or replace REUSE/SPDX tooling.
- **W3C/WAI** defines WCAG conformance and evaluation methods. Automated accessibility results are supporting evidence only; WAI explicitly expects appropriate human evaluation and recommends involvement of users with disabilities. DAIS therefore cannot convert an axe/Pa11y/static result into WCAG conformance or real-user acceptance.

These boundaries are intentional: the completion record is an evidence index and governance gate, not another license scanner, accessibility scanner, security scanner, package registry or release service.

## Record model

A record contains:

```text
schema_version
subject_id: P-001..P-227 or F-01..F-06
status: IN_PROGRESS | BLOCKED | DEFERRED | COMPLETE
gates:
  <all 19 canonical gates>:
    state: PASS | FAIL | UNKNOWN | NOT_APPLICABLE
    evidence: [public/sanitized evidence references]
    rationale: explanation
    applicability_reviewed: true|false
completion_record:
  <all canonical Project Completion Record fields>
```

### Gate semantics

**PASS** means the gate has explicit evidence. It does not mean the referenced evidence is beyond challenge; review can still invalidate it.

**FAIL** means the gate was evaluated and failed.

**UNKNOWN** means insufficient evidence exists to decide. Unknown remains visible rather than being smoothed into success.

**NOT_APPLICABLE** requires an explicit applicability review and rationale. For example, a purely read-only information viewer may have no mutation rollback path, but that decision must be recorded rather than silently omitted.

## Completion semantics

The following are separate states:

```text
SOURCE/REFERENCE COVERAGE
        !=
ALL GATES EVIDENCED
        !=
CANONICAL COMPLETION REVIEW
        !=
COMPLETE
```

If every applicable gate is `PASS` (or explicitly reviewed `NOT_APPLICABLE`) and every Project Completion Record field is populated while the subject remains `IN_PROGRESS`, the auditor returns:

```text
READY_FOR_CANONICAL_COMPLETION_REVIEW
```

It does not edit the roadmap.

A record declared `COMPLETE` is accepted only when the entire contract is satisfied and `completion_record.final_status` is also `COMPLETE`.

## Example: P-025

`examples/public-build-completion-p025-in-progress.json` intentionally demonstrates a near-but-not-complete record for the AMD Ryzen AI Max VGM proving ground.

It preserves unresolved gates for project-specific accessibility acceptance, multilingual acceptance, real-world completion-grade acceptance, a completion-grade release/tag, and canonical completion handover. Those gaps remain blockers even though the repository already contains substantial public documentation, tests, safety material and evidence-oriented tooling.

Run:

```bash
python scripts/public_build_completion_contract.py \
  examples/public-build-completion-p025-in-progress.json
```

Expected result: process exit `0` with `readiness=INCOMPLETE` and the unresolved gates listed. Exit `0` means the **record is internally valid**, not that the project is complete.

## Privacy and public evidence

Public completion records must contain references and sanitized summaries, not raw private evidence. Do not include:

- credentials, tokens, private keys or session material;
- private infrastructure addresses or internal-only topology where disclosure is unnecessary;
- patient/customer/donor/learner/personnel personal data;
- private prompts/messages or proprietary corpus content;
- raw logs that may contain identifiers or secrets.

The built-in sensitive-pattern check is a prefilter, not a comprehensive secret scanner. Specialist scanners and human review remain appropriate before publication.

## Accessibility and multilingual truth boundary

An automated accessibility pass is not WCAG conformance. A translated string is not multilingual acceptance. Completion-grade evidence should state the tested scope, tools, manual methods, assistive technologies, languages, participants/roles where privacy permits, and unresolved limitations.

## What this tranche advances

This is reusable infrastructure for:

- `P-227 Problem → Public Solution Framework`;
- `P-132 Claim/Evidence Verification Pipeline`;
- `P-224 Open Technical Evidence Standard`;
- `F-05 Universal Evidence Standard`;
- every roadmap project's future completion record.

It does **not** mark any roadmap item COMPLETE.

## Remaining program gates

- populate completion records from independent evidence rather than documentation presence alone;
- retain exact CI/release/acceptance evidence where applicable;
- perform representative real-world and domain-specific acceptance;
- perform appropriate manual/accessibility/user review;
- publish versioned releases/tags;
- update canonical handovers and the master roadmap only after completion review.
