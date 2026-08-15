# Universal System Doctor + Accessible AI — Reference v0.1

Roadmap mapping:

- `F-02 Universal System Doctor` — **IN PROGRESS**
- `F-06 Accessible AI` — **IN PROGRESS**
- `P-002 Universal PC Diagnostic Assistant` — **IN PROGRESS** baseline
- `P-016 One-Button Safe System Diagnostics` — **IN PROGRESS** baseline
- `P-087 Universal Accessibility Layer` — **IN PROGRESS** presentation contract
- `P-091 Plain-Language Transformation Engine` — **IN PROGRESS** fixed diagnostic vocabulary only
- `P-093 Multilingual UI Translation Framework` — **IN PROGRESS** English/Spanish reference path only
- `P-215 Universal Troubleshooting Framework` — **IN PROGRESS** diagnostic lifecycle baseline

This is a reference implementation in an existing hardware project, not a claim that these roadmap items are complete or that the HTML renderer is WCAG-conformant.

## Search-before-build decision

Existing open-source systems already solve important portions of this landscape. **osquery** provides rich operating-system instrumentation, while accessibility ecosystems such as **Pa11y** provide dedicated automated web accessibility testing. Future DAIS work should consume or interoperate with mature tools where appropriate rather than reimplement their full capabilities.

The gap being explored here is the contract between safe diagnostics and understandable presentation:

```text
DETECT -> INSPECT -> EXPLAIN -> RECOMMEND -> VERIFY
```

with two additional invariants:

1. the default diagnostic lane is read-only and privacy-minimizing;
2. beginner, intermediate, engineer, multilingual and assistive presentations are views of the **same evidence record**, not different truth sources.

## Read-only System Doctor

`scripts/system_doctor.py` collects a deliberately small baseline:

- operating system, release and architecture;
- Python version and total physical memory when safely available;
- filesystem capacity/headroom for the checked root;
- bounded Git/Python availability signals;
- structured checks with `OK`, `NOTICE`, `REVIEW` or `UNKNOWN` states;
- explicit privacy and mutation declarations;
- known limitations.

It intentionally does **not** collect usernames, hostnames, network addresses, environment values, credentials, user file contents or process command lines.

It intentionally does **not** repair storage, install software, restart services, change configuration or reboot.

A notice or review state is evidence that more investigation may be useful. It is not authorization to mutate the system.

## Three-level presentation

The same report can be rendered as:

### Beginner

A short plain-language answer stating what was checked and whether anything changed.

### Intermediate

Check states, observations and the explicit read-only boundary.

### Engineer

The complete machine-readable JSON record for inspection, reproducibility and downstream evidence handling.

No tier is allowed to hide a material risk that exists in the underlying record.

## Accessible HTML renderer

`scripts/accessible_report.py` generates dependency-free semantic HTML from the diagnostic record. The v0.1 contract includes:

- document language declaration;
- skip-to-content link;
- semantic headings, sections and lists;
- explicit safety-mode block before diagnostic details;
- visible keyboard focus styles;
- focusable engineering output;
- reduced-motion preference handling;
- no color-only status semantics;
- HTML escaping of machine-supplied text;
- optional engineering detail disclosure;
- English and Spanish presentation dictionaries.

This is an **accessibility-by-design baseline**, not evidence of WCAG conformance. A completion-grade Accessible AI project still needs automated and manual accessibility testing, screen-reader validation, keyboard-only acceptance, zoom/reflow testing, contrast testing, additional languages, voice interfaces where appropriate, low-bandwidth validation and testing with people who use assistive technology.

## Security/privacy review

The renderer accepts already-produced JSON and escapes all displayed machine-supplied values. It contains no remote script dependencies, analytics, trackers, network requests or form submission.

The diagnostic collector executes only bounded version checks and local capacity APIs. Its subprocess environment forwards only `PATH`, and the value itself is never included in output.

## Recovery model

There is nothing to roll back in the default lane because the collector and renderer are non-mutating. Any future repair adapter must be separated from these components and governed by SafeFix recovery/approval/attestation gates.

## Acceptance available in CI

Tests currently verify:

- read-only/non-mutation declarations;
- privacy-minimization declarations;
- all three audience views derive from one report;
- semantic/focus/reduced-motion HTML features;
- Spanish presentation path;
- HTML escaping against markup/script injection.

These tests validate the reference contract only. They are not a substitute for real cross-platform or assistive-technology acceptance testing.

## Extraction and reuse

A dedicated public repository should eventually host the generic System Doctor and Accessible AI layers. Until repository-creation tooling is available, this project serves as a public proving ground. Extraction should preserve commit provenance and consume the previously promoted SafeFix/evidence schemas rather than duplicating them.
