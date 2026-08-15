# Accessible AI hosted automated supporting acceptance

Status: **IN PROGRESS supporting evidence — not WCAG conformance**

This lane deepens F-06 Accessible AI by running a pinned specialist accessibility engine against exact generated English and Spanish System Doctor HTML artifacts on a disposable GitHub-hosted Ubuntu environment.

## Search-before-build decision

DAIS does not implement another web accessibility rules engine. The workflow adopts `@axe-core/cli` from the Deque axe ecosystem and pins version `4.11.3`, the latest published `axe-core-npm` release identified during this tranche. The upstream CLI supports headless Chrome, selected WCAG rule tags, JSON output, an explicit ChromeDriver path, custom Chrome options and `--exit` for CI failure on violations.

GitHub's hosted Ubuntu 24.04 image publishes Chrome and ChromeDriver as included browser tooling and exposes the `CHROMEWEBDRIVER` path. The workflow uses the hosted runner only; it does not touch user devices or production systems.

## What the workflow proves

For the exact generated artifact digests retained in the workflow evidence, it can prove that:

- the System Doctor collector remained read-only and privacy-minimized;
- English and Spanish HTML artifacts were generated from the same report truth;
- pinned axe CLI executed successfully against those exact local artifacts;
- the selected automated WCAG-tag rules reported no violation when the `--exit` gate passed;
- the resulting public evidence records passed the DAIS Accessible AI schema/privacy/claim validator.

## What it does not prove

The workflow explicitly does **not** prove:

- WCAG 2.2 AA conformance;
- absence of all accessibility defects;
- keyboard-only usability;
- screen-reader usability;
- 400% zoom/reflow usability;
- disability-inclusive real-user acceptance;
- production readiness.

W3C accessibility evaluation guidance treats automated tools as supporting components of evaluation; human evaluation remains necessary for criteria and usability aspects that automation cannot establish. The DAIS acceptance schema therefore forces all conformance/completeness/real-user/production claims to `false`.

## Evidence retention

The workflow retains, for a short bounded period:

- exact generated English and Spanish HTML;
- the sanitized System Doctor report;
- axe JSON output per language;
- DAIS supporting-acceptance evidence records containing exact HTML SHA-256 digests;
- validator outputs showing `AUTOMATED_SUPPORTING_EVIDENCE_NOT_CONFORMANCE`.

No participant data or credentials are collected because no human participant or connected account is used in this lane.

## Remaining F-06 gates

The next evidence class is manual assistive-technology acceptance across representative browser/OS combinations, followed by privacy-governed disability-inclusive usability evidence. Those gates remain separate from automated CI and must not be inferred from this workflow.
