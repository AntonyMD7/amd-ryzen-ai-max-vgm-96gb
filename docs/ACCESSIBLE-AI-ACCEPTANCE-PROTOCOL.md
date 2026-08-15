# Accessible AI supporting acceptance protocol

Status: **IN PROGRESS** — supporting evidence contract only  
Canonical roadmap: **F-06 Accessible AI**, with reusable evidence for accessibility-related public-build entries.

## Why this tranche exists

The existing Accessible AI reference renderer has semantic HTML, keyboard-focus styling, reduced-motion handling, escaped machine data, English/Spanish views, hosted static checks, and a strict no-conformance claim. The next gap is a reusable way to retain accessibility acceptance evidence without turning a single automated scan, synthetic fixture, or one assistive-technology session into a false certification.

This tranche adds that evidence boundary. It does **not** claim WCAG conformance and does not mark F-06 COMPLETE.

## Search before build

We should not create a competing accessibility scanner.

- W3C WCAG 2.2 remains the normative accessibility target for web content: https://www.w3.org/TR/WCAG22/
- W3C evaluation guidance explains that automated testing is only part of evaluation and that some success criteria require human testing: https://www.w3.org/WAI/test-evaluate/
- W3C guidance on selecting evaluation tools emphasizes that tools differ in scope and should be combined with the checks they cannot automate: https://www.w3.org/WAI/test-evaluate/tools/selecting/
- axe-core is a mature open-source automated Web UI accessibility engine: https://github.com/dequelabs/axe-core
- the open-source axe CLI provides CI-oriented automated checks: https://github.com/dequelabs/axe-core-npm/tree/develop/packages/cli
- Pa11y is another mature open-source automated accessibility testing ecosystem: https://github.com/pa11y/pa11y

DAIS therefore owns the **evidence, privacy, provenance, claim-integrity and acceptance orchestration contract**, while specialist engines remain specialist engines.

## Evidence classes

The schema deliberately separates four classes:

1. `SYNTHETIC_CONFORMANCE` — proves only that the evidence format and validator behave as designed.
2. `AUTOMATED_TOOL` — records a specialist-tool run. It is supporting evidence, never WCAG conformance.
3. `MANUAL_ASSISTIVE_TECH` — records sanitized evidence from a manual assistive-technology session.
4. `AGGREGATED_REAL_USER_USABILITY` — records privacy-minimized aggregate usability evidence without participant identity/contact data.

No class is a conformance certificate.

## Core acceptance dimensions

Every record explicitly accounts for:

- keyboard-only operation;
- screen-reader operation;
- 400% zoom/reflow;
- reduced-motion behavior;
- document/interface language semantics;
- automated rules from a specialist accessibility engine.

A `NOT_RUN` result remains visible. A failed check remains failed. The validator never fills gaps with optimistic inference.

## Suggested manual task protocol

For a user-facing diagnostic report, a future acceptance session should test at least:

1. Reach the report content using only the keyboard and activate the skip link.
2. Traverse headings, lists and disclosure content in a logical order.
3. Read the safety/read-only status and each check using a screen reader without relying on color.
4. Increase browser zoom to 400% and verify information remains readable and operable without two-dimensional scrolling for ordinary text flow, where the applicable WCAG criterion requires reflow.
5. Enable reduced-motion preference and verify motion is removed or reduced as designed.
6. Switch each supported language and confirm the document language, labels and status meanings remain coherent.
7. Run a reviewed automated accessibility engine against the exact artifact digest.
8. Record unresolved issues instead of suppressing them to obtain a pass.

This protocol is a starting minimum, not a substitute for a comprehensive WCAG evaluation methodology or disability-inclusive usability study.

## Privacy boundary

Public evidence must not store:

- participant names, usernames, email addresses, phone numbers or contact details;
- credentials, API keys, tokens or secret-bearing URLs;
- private user content;
- home-directory/user-profile paths that reveal identity.

When people are involved, consent must have been recorded outside the public evidence artifact. Public evidence stores only the boolean that the consent prerequisite was satisfied, not the participant identity or consent document.

## Claim boundary

The public schema forces these fields to `false`:

- `wcag_conformance`;
- `all_accessibility_issues_found`;
- `real_user_acceptance`;
- `production_ready`.

This is intentional. Those claims require a broader governance/review process than this validator can establish.

## Beginner view

A PASS in one check means: **we have evidence for that check in that environment**.

It does not mean: **the whole product is accessible to everyone**.

If a check says `NOT_RUN`, that is useful information. The next step is to run it, not hide it.

## Engineer view

The validator performs:

- Draft 2020-12 schema validation;
- public-evidence sensitive-pattern prefiltering;
- people-involved consent gating;
- explicit failed/not-run preservation;
- evidence-class-specific output status;
- immutable input handling.

It has no browser, screen reader, scanner, microphone, telemetry, uploader, credential provider or production mutation capability.

## Remaining F-06 completion gates

Before F-06 can be considered COMPLETE under the canonical roadmap, work still includes at least:

- dedicated public distribution/versioning rather than only a proving-ground implementation;
- reviewed specialist-tool integration on representative exact artifacts;
- real keyboard and multiple assistive-technology acceptance across relevant operating systems/browsers;
- disability-inclusive usability evidence with privacy/consent governance;
- broader language evaluation where supported;
- explicit accessibility review against the intended product surfaces;
- release/tag/version and retained completion evidence;
- canonical handover/completion record.

Therefore this tranche advances F-06 but preserves **IN PROGRESS** truthfully.
