# Universal System Doctor + Accessible AI Hosted Acceptance v0.2

Status: **IN PROGRESS — one hosted Linux acceptance lane**

Canonical roadmap mapping: **F-02 Universal System Doctor**, **F-06 Accessible AI**, and supporting evidence for P-002/P-016/P-087/P-091/P-093/P-215.

## Purpose

The first System Doctor/Accessible AI tranche established a privacy-minimizing read-only collector and English/Spanish semantic HTML rendering. This tranche adds a strict machine-readable report contract and a repeatable GitHub-hosted Ubuntu acceptance lane that retains sanitized evidence artifacts.

It does **not** claim Windows/macOS acceptance, assistive-technology usability, WCAG conformance, hardware-failure diagnosis, or production readiness.

## Search-before-build / upstream boundary

- osquery already provides a mature cross-platform SQL-style instrumentation ecosystem for Linux, Windows and macOS. Future deeper diagnostic adapters should prefer bounded osquery/vendor queries when appropriate rather than expanding a bespoke system-inventory engine: https://osquery.io/
- Pa11y is an established automated web-accessibility testing ecosystem. A future browser acceptance layer can integrate it or another reviewed specialist tool rather than inventing a competing automated scanner: https://pa11y.org/
- W3C explicitly notes that accessibility evaluation requires a combination of automated and human evaluation, and that no tool alone can determine conformance. The hosted static checks in this repository therefore remain implementation signals only: https://www.w3.org/WAI/test-evaluate/ and https://www.w3.org/WAI/WCAG22/Understanding/conformance.html

## New evidence contract

`schemas/system-doctor-report-v0.1.schema.json` freezes the currently public, privacy-minimizing output surface. It requires:

- collector mode `READ_ONLY`;
- bounded OS/release/architecture/Python/memory fields;
- bounded storage totals;
- explicit check states: `OK`, `NOTICE`, `REVIEW`, or `UNKNOWN`;
- every declared privacy collection flag to be `false`;
- every declared mutation flag to be `false`;
- known limitations;
- rejection of unreviewed extra fields, including accidental hostname-style expansion.

This is intentional: new collection fields must be reviewed rather than silently appearing in a public diagnostic artifact.

## Hosted Ubuntu acceptance

`.github/workflows/system-doctor-acceptance.yml` executes on a GitHub-hosted Ubuntu runner and:

1. runs the real read-only collector;
2. validates the report against the JSON Schema;
3. verifies every privacy and mutation flag remains false;
4. renders English and Spanish views from the same validated record;
5. verifies semantic landmarks, skip navigation, keyboard-focus target, and reduced-motion CSS are present;
6. hashes the JSON and both HTML representations;
7. emits an explicit acceptance envelope;
8. uploads only the sanitized report/render/evidence files as a short-retention Actions artifact.

The acceptance envelope explicitly records:

- `wcag_conformance_claimed: false`;
- `real_user_assistive_technology_acceptance_claimed: false`;
- `windows_acceptance_claimed: false`;
- `macos_acceptance_claimed: false`;
- `production_safe_to_infer: false`.

## Beginner view

> The System Doctor is now repeatedly checked on a disposable Linux computer in GitHub. It proves the basic checker can run without changing the computer or collecting the private categories it promises not to collect. The web report is checked for important accessibility building blocks in English and Spanish. This still does not prove it works for every computer or every disability.

## Engineer view

This lane improves evidence quality from unit-only tests to an independent hosted execution environment with schema validation and retained digests. It remains a shallow system-health baseline. The collector invokes only bounded version discovery for Git and standard-library platform/memory/storage APIs; it does not ingest process command lines, network addresses, user documents, environment values, credentials, or hostname.

The accessible HTML checks are structural regressions, not standards certification. Human/assistive-technology evaluation remains necessary per the roadmap completion contract and W3C guidance.

## Remaining completion gates

F-02 and F-06 remain **IN PROGRESS**. Material unresolved gates include:

- Windows acceptance on a non-production test system;
- macOS acceptance on a non-production test system;
- broader bounded diagnostic adapters and clear escalation semantics;
- offline/low-bandwidth browser packaging;
- keyboard-only human acceptance;
- screen-reader acceptance with representative users/AT;
- zoom/large-text and reflow acceptance;
- automated specialist accessibility scan integrated with reviewed/pinned tooling;
- additional languages and translation review;
- project-specific distribution/release/version record;
- community feedback and canonical completion record.

No device or production mutation is authorized by this tranche.
