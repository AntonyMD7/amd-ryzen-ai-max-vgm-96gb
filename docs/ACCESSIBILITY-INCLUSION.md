# Accessibility & Inclusion Reference Layer

Status: **IN PROGRESS reference implementation** strengthening existing `P-087`, `P-091`, `P-093` work and advancing:

- `P-088 Voice-First AI Interface`
- `P-089 Screen-Reader Optimized AI Interface`
- `P-090 Large-Text / Elder-Friendly Interface Framework`
- `P-092 Reading-Level Transformation Tool`
- `P-094 Community Translation Validation Network`
- `P-095 WCAG Scanner`
- `P-096 Contrast/Color Accessibility Checker`
- `P-097 Keyboard Navigation Auditor`
- `P-098 Caption/Transcript Workflow Toolkit`
- `P-099 Accessibility-by-Default Repository Templates`
- `P-100 Assistive Communication Toolkit`

## Search before build

W3C standards remain the authority for web accessibility semantics and conformance. This project targets WCAG 2.2 concepts, uses the WAI-ARIA Authoring Practices Guide as implementation guidance, and treats WebVTT as a standard exchange format where appropriate for web text tracks. Automated engines such as **axe-core** already provide mature rule execution; the reference scanner therefore plans integration instead of rebuilding a DOM accessibility engine.

Automated findings are never equated with WCAG conformance. Manual keyboard, assistive-technology and user acceptance remain necessary.

## Reference capabilities

### Voice-first / screen-reader / elder-friendly / AAC checklists

Structured booleans make missing accessibility features visible without claiming that a checklist can replace user testing. Voice-first design requires text fallback and clear recording/retention state. Screen-reader design requires semantic structure, names, focus/status behavior and image alternatives. Elder-friendly design prioritizes resize/reflow, target usability, plain language, timeout control and explicit confirmation. Assistive communication preserves non-voice access, offline core messages and visible caregiver/override semantics.

### Reading-level transformation

The reference planner does not transform user text. It defines what a future transformation must preserve: names, dates, numbers, warnings, obligations, uncertainty and citations. Simpler language must not erase material meaning or risk.

### Community translation validation

Translation quality is a social and linguistic review problem, not just a model score. The reference records target language, reviewer count, community review and safety-critical terminology review while generating no translation and storing no reviewer identity.

### WCAG scanner integration

The plan recommends a pinned axe-core or equivalently reviewed engine, retaining rule IDs and combining automated output with keyboard and screen-reader sampling. Zero automated findings never means conformance.

### Contrast

The color helper implements the WCAG 2 relative-luminance/contrast-ratio calculation for `#RRGGBB` colors and reports AA/AAA **text-threshold checks only** for caller-declared normal/large text. It does not evaluate the rest of the page, non-text contrast, font-size eligibility for 'large text', state changes, images/gradients or overall WCAG conformance.

### Keyboard navigation

The reference consumes caller-supplied component facts for reachability, visible focus and keyboard operability. It does not open a browser or prove ARIA pattern correctness. Future browser automation should be paired with WAI-ARIA APG pattern expectations and manual assistive-technology testing.

### Captions/transcripts

The manifest requires caption availability, transcript availability and human review and recommends WebVTT where appropriate for web tracks. It does not transcribe media or generate caption files.

### Accessibility-by-default templates

A repository template should make accessibility statements, keyboard/screen-reader/contrast testing, caption policy and issue intake normal project artifacts rather than post-release additions.

## Privacy and safety

- no microphone/audio capture;
- no source text or translation content required by the reference planner;
- no user identity/reviewer identity stored;
- no browser/scanner execution;
- no medical/clinical communication claim for the AAC checklist;
- no WCAG/accessibility/translation certification.

## Completion gaps

All mapped projects remain IN PROGRESS. Completion requires real browser and assistive-technology acceptance, people with disabilities in usability review, voice/privacy testing, multilingual/community validation, automated scanner integration, robust color/non-text/state testing, caption-generation/QA workflows, accessible public distribution, releases, contribution paths, security/privacy review and canonical completion records.
