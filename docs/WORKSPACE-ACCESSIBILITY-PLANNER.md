# Least-Privilege Workspace & API Accessibility Planner

Status: **IN PROGRESS reference implementation** for:

- `P-077 Google Drive Organization Assistant`
- `P-078 Google Docs Knowledge Assistant`
- `P-079 Google Sheets Workflow Automation Toolkit`
- `P-080 Gmail Workflow Helper`
- `P-081 Google Calendar Coordination Assistant`
- `P-082 Google Workspace Plain-Language Layer`
- `P-083 Google Forms Low-Literacy Accessibility Toolkit`
- `P-084 Browser/Chrome Productivity Extension`
- `P-085 Workspace Add-on Starter Framework`
- `P-086 General API Democratization Toolkit`

## Search before build

Current Google Workspace APIs and extension surfaces already provide the underlying capabilities. The public project should wrap official APIs rather than create private scraping or parallel storage protocols.

The reference architecture therefore treats official Google Drive, Gmail and Calendar APIs as platform authorities, and Google Workspace Add-ons as the supported in-product extension surface. OAuth scopes and platform restrictions must be checked against current Google documentation at implementation time rather than copied into a permanent hard-coded table here.

## Core rule: planning is not permission

Every mode in `workspace_accessibility_planner.py` emits a **plan** only. It never contacts Google, reads content, writes a file/sheet, sends a message, changes a calendar event, grants a browser permission or deploys an add-on.

Read and mutation intent are classified separately so a future adapter can request the smallest appropriate permission and can put writes behind explicit approval/idempotency gates.

## Roadmap modes

### P-077 — Drive organization

Supports inventory and propose-only folder/move/rename intents. Stable file IDs, shared-drive semantics and dry-run evidence are required before mutation.

### P-078 — Docs knowledge

Requires an explicit authorized-document allowlist and per-chunk provenance. Write-back is off by default and insufficient evidence must remain a valid outcome.

### P-079 — Sheets workflow

Requires explicit spreadsheet/range contracts, schema validation and idempotency for writes. Append/update remain proposals until a separate action boundary.

### P-080 — Gmail helper

Separates search/read from draft/send/label proposals. Sending requires recipient resolution and exact-message review; generated text is never auto-sent by this layer.

### P-081 — Calendar coordination

Separates availability/listing from create/update/delete proposals. Timezone, attendee identity, local start/end and conflict checks are explicit preconditions.

### P-082 — plain-language layer

A transformation contract must preserve dates, numbers, names, material risk and uncertainty and offer access to original wording. Simplification is not permission to erase obligations or caveats.

### P-083 — Forms accessibility

Checks plain labels, one-idea-per-question structure, required-field explanations, error recovery, keyboard path and declared language. Passing a small checklist is not a WCAG certification.

### P-084 — browser extension

Surfaces broad/sensitive permissions for security review. Every permission needs justification, data-flow documentation and an uninstall/recovery path.

### P-085 — Workspace add-on

Creates a host/requirements plan only. Cloud project changes, add-on deployment and Marketplace publication remain false. Current Google card/iframe and host restrictions must be followed at implementation time.

### P-086 — API democratization

Classifies auth and read/write capability before generating a friendly wrapper. Official schemas, least privilege, pagination, bounded retries, rate-limit handling, redacted logs and version provenance remain required.

## Privacy / security

- no connected-account data is read by the public reference tool;
- no OAuth token, API key or service-account credential is accepted;
- no message/document/event content is stored;
- no mutation is performed;
- broad browser permissions trigger review rather than automatic acceptance;
- exact platform scopes remain an adapter-time decision based on current official documentation.

## Accessibility

All eventual interfaces should preserve keyboard navigation, semantic labels, visible focus, plain-language status, large-text/reflow support, non-color-only state, screen-reader compatibility and explicit error recovery. The canonical machine plan is separate from user-language rendering so localization does not change permission truth.

## Completion gaps

All mapped IDs remain IN PROGRESS. Completion requires real least-privilege adapters and test accounts, scope verification against current official documentation, replay/idempotency tests, accessible UI acceptance, multilingual validation, security/privacy review, public distribution/release evidence, known limitations, contribution paths and canonical completion records.
