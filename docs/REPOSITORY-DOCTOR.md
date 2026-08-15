# Repository Doctor v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-039 GitHub Repo Doctor`, `P-040 Explain This Repository`, `P-041 Repository Health Auditor`, `P-044 Documentation Quality Assistant`, `P-045 Repository Accessibility Reviewer`, `P-058 Dangerous-Script Detector`, and `P-059 Read-Only vs Mutation Classifier`.

The doctor is intentionally a shallow, read-only preflight. It must not become an inferior reimplementation of mature specialist security/documentation tooling.

## Search-before-build / adopt existing tools

Current open-source tools already cover important parts of this problem well:

- **OpenSSF Scorecard** provides open-source security-health checks and an official GitHub Action;
- **Gitleaks** scans repositories for hard-coded secrets;
- **markdownlint / markdownlint-cli2** provide mature Markdown/CommonMark linting;
- **lychee** provides fast live link checking across Markdown/HTML/text.

Therefore this project does **not** claim to implement `P-046 Security Hygiene Reviewer`, `P-047 README Linting Action`, `P-048 Broken-Link Scanner Action`, or `P-049 Secret-Exposure Detection Action` merely because it can notice adjacent structure. Those items should integrate/adopt the mature tools above rather than duplicate them.

## What v0.1 does

`scripts/repo_doctor.py` reads a local working tree while explicitly skipping `.git`, common dependency/build directories, binary/large files and unsupported extensions. It does not execute repository code.

It reports:

- presence of README, LICENSE, SECURITY, CONTRIBUTING and START-HERE;
- tests/docs/workflows/issue-template presence;
- README title/section headings as a deterministic explainability skeleton;
- Markdown heading-level jumps and empty image alt text as **review signals**;
- a narrow high-risk command-pattern preflight;
- a separate set of potentially mutating command-pattern findings;
- specialist-tool recommendations and explicit limitations.

## Dangerous-script and mutation boundary

Pattern matching is deliberately conservative and incomplete. A flagged `rm -rf`, pipe-to-shell, execution-policy bypass or disk-format token means **review required**, not "malware." Conversely, the absence of a match does not prove a script safe.

Potential filesystem/package/service/network mutation patterns are classified separately. Classification does not authorize execution and the doctor never runs the script to "find out."

## Explain-this-repository boundary

The first explainability layer is deterministic: README title and headings plus public structure. It does not send source code to a language model and does not invent a purpose when the README lacks context. Future P-040 work can add optional local/approved-model summarization over explicitly selected files while preserving provenance and data boundaries.

## Accessibility boundary

Markdown heading-order and alt-text heuristics are useful early checks but do not establish WCAG conformance. Future work should integrate rendered-page auditing and assistive-technology acceptance.

## Privacy/security

The doctor deliberately does not inspect Git history or implement secret scanning. That is an important boundary: public-health reporting must not accidentally print a discovered credential. Gitleaks or another specialist scanner should handle secret detection with redacted/fingerprint-safe reporting.

## Beginner view

> "I can check whether this project has the basic files people need, point out documentation/accessibility concerns, and warn about scripts that deserve careful review. I will not run the project's code."

## Completion gaps

All mapped items remain **IN PROGRESS**. Completion requires, as applicable:

- GitHub API adapter and safe public-repository URL mode;
- richer language/package-manager discovery without executing repository hooks;
- adoption integrations for Scorecard, Gitleaks, markdownlint and lychee;
- rendered accessibility testing and human/assistive acceptance;
- structured explainability with source citations;
- dangerous-script fixtures across PowerShell/Bash/Python/package scripts while controlling false positives;
- signed/versioned distribution, accessibility/multilingual validation and canonical completion evidence.
