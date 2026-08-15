# Defensive Cybersecurity, Privacy & Trust Reference Layer

Status: **IN PROGRESS reference implementation** for `P-121` through `P-133`.

## Search before build

The portfolio should use established specialist engines rather than invent scanners. **Lynis** is an established security-auditing tool for Unix-like hosts; **OSV-Scanner** and GitHub Dependency Review already cover dependency vulnerability workflows; **ExifTool** is a mature metadata tool; **Presidio** is an established PII/redaction ecosystem. This tranche adds bounded orchestration/evidence semantics only.

## Hard safety boundary

This public layer is defensive and metadata-only. It performs no network scan, exploit, password/credential test, message retrieval, file redaction, metadata mutation, payment action or agent execution. Home-network work begins with owner-authorized passive inventory and vendor/router documentation; it explicitly rejects Internet-wide scanning as a default path.

`P-122` preserves raw logs locally and separates observation from attribution. `P-123` delegates actual dependency scanning to reviewed upstream tools. `P-124` requires backup/copy workflows before metadata removal and recommends ExifTool or format-specific tools rather than silently rewriting originals. `P-125` requires local processing/human review and never treats a redaction engine as proof every sensitive item was found.

`P-126` identifies sensitive or unnecessary permissions but does not revoke them. `P-127` accepts only boolean message cues, never opens links/attachments, and never certifies a message safe merely because no cue was supplied. `P-128` similarly treats store signals as warning evidence, not proof of legitimacy.

`P-129` uses transparent invoice flags (for example, changed bank details) and a clearly labeled reference amount-deviation threshold; it never auto-pays, auto-blocks or claims fraud. `P-130` provides a conservative local/cloud policy prefilter without sending data or claiming legal compliance.

`P-131` records source/artifact identity requirements but does not treat self-reported provenance as external attestation. `P-132` counts supporting/independent evidence while keeping `claim_proven: false` pending domain review. `P-133` denies any requested agent action outside the allowlist and still requires runtime identity/scope/expiry/approval/audit before an allowed action can execute.

## Privacy

The reference code is intentionally structured around booleans, identifiers, counts and hashes instead of raw private content. Production adapters must define separate redaction/data-class contracts and must not publish private infrastructure evidence into public repositories.

## Accessibility

Security guidance must remain understandable without hiding risk: plain-language warning plus optional raw evidence, non-color-only severity, keyboard/screen-reader support, and actionable recovery/reporting paths. Fraud/scam/phishing warnings should avoid certainty language unless independently proven.

## Completion gaps

Every mapped item remains IN PROGRESS. Completion requires safe real adapters, representative sanitized fixtures, upstream-engine/version pinning, false-positive/false-negative acceptance, owner-authorized network test policy, redaction/metadata output verification, accessibility/multilingual review, security/privacy threat review, releases, contribution paths and canonical completion records. High-impact decisions such as payments, account changes, blocking or agent mutations must remain separately governed.
