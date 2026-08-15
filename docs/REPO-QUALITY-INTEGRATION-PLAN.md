# Repository Quality Integration Plan v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-046 Security Hygiene Reviewer`, `P-047 README Linting Action`, `P-048 Broken-Link Scanner Action`, and `P-049 Secret-Exposure Detection Action`.

## Decision: integrate, do not reimplement

These opportunity entries overlap mature open-source projects. The DAIS public-good value should be a safer beginner/engineer integration layer rather than another scanner:

- `P-046` adopts **OpenSSF Scorecard** for broad open-source security-health signals;
- `P-047` adopts **markdownlint/markdownlint-cli2** for Markdown and README linting;
- `P-048` adopts **lychee** for live link validation;
- `P-049` adopts **Gitleaks** (or an equivalent specialist scanner selected through review) for hard-coded secret detection.

`scripts/repo_quality_integration_plan.py` is deliberately non-executing. It only checks a bounded working tree for lexical signs that these integrations/configurations may already exist. A detected string is not proof that a workflow is enabled, current or secure.

## Safety gates before installing an integration

Every integration proposal carries the same baseline gates:

1. re-read current upstream installation/action documentation at implementation time;
2. pin GitHub Actions by immutable commit SHA or another verifiable lock strategy;
3. grant the least `GITHUB_TOKEN` permissions needed;
4. never expose raw secret findings or private values in public logs/artifacts;
5. retain rollback for workflow/configuration changes;
6. treat scanner output as a signal requiring context, not an automatic security verdict.

The planner never installs the tools, changes workflows, executes repository code, reads `.git` history, performs network requests or collects secret values.

## Why no automatic Gitleaks result ingestion yet

A secret scanner can discover exactly the information a public automation must not leak. The first integration layer therefore stops before collecting raw findings. A later adapter must use redaction/fingerprints and protected evidence channels before public CI annotations are considered.

## Beginner view

> "You do not need four home-made scanners. This project tells you which proven open-source checks fit each job, whether the repository appears to have them already, and what safety checks to apply before adding them."

## Engineer view

The report is a deterministic adoption plan over a bounded file set. Future mutating integration PRs should pin reviewed upstream revisions, record permissions, run in isolated branches, and preserve exact CI evidence.

## Completion gaps

`P-046`–`P-049` remain **IN PROGRESS**. Completion still requires reviewed/pinned working integrations in representative repositories, fixtures for pass/fail/false-positive behavior, permission and fork-PR threat-model review, redacted secret-reporting acceptance, documented recovery, accessibility/multilingual UX, versioned releases and canonical completion records.
