# Accessible AI manual assistive-technology session evidence

Status: **IN PROGRESS** — reproducible manual-session evidence contract only  
Canonical roadmap: **F-06 Accessible AI**

## Purpose

F-06 already has semantic HTML, automated accessibility supporting checks, browser keyboard/reflow supporting checks, and a privacy-safe summary evidence schema. The next missing layer is a reproducible record for a **real manual assistive-technology session** that preserves failures, blocked tasks, exact environment identity, consent boundaries, and artifact identity without publishing participant identity or private content.

This tranche adds that record and a deterministic mapping into the existing F-06 supporting-evidence validator. It does **not** run a screen reader or browser and does **not** claim WCAG conformance, universal accessibility, production readiness, or roadmap completion.

## Search before build

DAIS should not create another accessibility standard, screen reader, or automated scanner.

- W3C WCAG 2.2 remains the normative web-content accessibility standard target.
- W3C evaluation guidance makes human evaluation part of accessibility assessment because automated tools cannot determine every accessibility requirement.
- WCAG-EM provides a methodology for evaluating website accessibility conformance.
- ACT Rules and EARL provide established concepts for repeatable accessibility testing and machine-readable evaluation results.
- Existing automated engines such as axe-core remain specialist supporting tools rather than being reimplemented here.

DAIS therefore owns only the **privacy, evidence, provenance, reproducibility, task-result, and claim-integrity boundary** around a manual session.

## Exact session identity

A manual record identifies the exact subject by:

- artifact kind;
- bounded artifact reference;
- SHA-256 of the tested artifact.

The environment records:

- operating-system family and version;
- browser family and version;
- assistive-technology name and version;
- reviewed input method.

A real manual session fails closed if those versions are `unknown`, `not-run`, `n/a`, or otherwise unspecified. A synthetic fixture cannot be promoted into manual evidence by changing one status field; a real manual record requires a non-synthetic subject identity, people involvement, and an externally satisfied consent prerequisite.

## Canonical manual tasks

Every manual session must retain each task exactly once:

1. `skip_navigation`
2. `landmark_and_heading_navigation`
3. `interactive_control_operation`
4. `status_and_safety_announcement`
5. `logical_reading_order`
6. `focus_visibility_and_location`
7. `zoom_reflow_400`
8. `reduced_motion`
9. `language_semantics`
10. `error_and_issue_discoverability`

Each result is one of `PASS`, `FAIL`, `BLOCKED`, `NOT_RUN`, or `NOT_APPLICABLE`.

The validator never converts a failure to a pass. `BLOCKED` and `NOT_RUN` remain incomplete evidence. `NOT_APPLICABLE` is retained explicitly rather than being treated as success.

## Privacy and consent

Public manual-session evidence is intentionally minimized. It must not retain:

- participant names or identifiers;
- participant contact details;
- email addresses in notes;
- credentials, tokens, API keys, or secret-bearing values;
- private user content;
- identity-bearing home-directory/profile paths;
- raw audio or screen recordings.

When people are involved, consent must have been handled outside the public artifact. The public record stores only `consent_prerequisite_satisfied: true`; it never stores the consent document or participant identity.

## Deterministic evidence mapping

The detailed session is canonicalized and SHA-256 hashed. Its digest becomes the evidence reference for a mapped record in the existing `accessible-ai-acceptance-v0.1` format.

Mapping is deliberately conservative:

- keyboard evidence combines skip navigation, interactive controls, and focus visibility/location;
- screen-reader evidence combines landmark/heading navigation, safety/status announcement, logical reading order, and issue discoverability;
- zoom/reflow, reduced motion, and language semantics map directly;
- any failed constituent makes the mapped dimension `FAIL`;
- any blocked/not-run constituent makes the mapped dimension `NOT_RUN`;
- the manual session never claims that automated rules were run, so `automated_rules` remains `NOT_RUN` unless a separate automated-tool record exists.

This lets manual and automated evidence coexist without laundering one evidence class into another.

## Result semantics

`SYNTHETIC_ONLY_NOT_ACCEPTANCE` means only that the schema and validator contract were exercised.

`MANUAL_SESSION_HAS_FAILURES` means at least one retained task failed.

`MANUAL_SESSION_INCOMPLETE` means no task failed but at least one task was blocked or not run.

`MANUAL_SUPPORTING_ACCEPTANCE_NOT_CONFORMANCE` means the applicable tasks in that exact manual session passed, under that exact artifact/environment identity. It still does not establish WCAG conformance, support for every disability or assistive technology, cross-browser compatibility, production readiness, or F-06 completion.

## Beginner view

A manual PASS means: **someone actually exercised this exact check with the recorded setup and it worked in that session.**

It does not mean: **this product is accessible to everyone.**

A FAIL or BLOCKED result is useful evidence and must remain visible.

## Engineer view

The implementation performs:

- Draft 2020-12 schema validation;
- exact canonical task-set validation;
- reproducible environment/version checks for real manual sessions;
- public-evidence sensitive/contact/path prefiltering;
- external-consent prerequisite enforcement;
- deterministic session hashing;
- conservative mapping into the existing F-06 acceptance evidence contract;
- immutable-input tests.

It contains no browser driver, screen-reader controller, microphone capture, telemetry, network client, uploader, credential provider, device mutation, or production executor.

## Remaining F-06 completion gates

F-06 remains **IN PROGRESS** after this tranche. Completion still requires, as applicable:

- actual manual sessions on representative OS/browser/assistive-technology combinations;
- multiple assistive technologies rather than one implementation;
- disability-inclusive usability evidence with appropriate consent/privacy governance;
- broader supported-language evaluation;
- formal accessibility review across intended public surfaces;
- reconciliation of manual and automated findings with unresolved issues retained;
- dedicated public distribution/versioning;
- release/tag evidence;
- community/real-user acceptance appropriate to the scope;
- canonical handover/completion record satisfying the master roadmap.

No source file or CI pass in this tranche changes F-06 to COMPLETE.
