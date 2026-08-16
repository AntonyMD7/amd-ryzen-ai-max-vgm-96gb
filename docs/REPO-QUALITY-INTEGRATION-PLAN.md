# Repository Quality Integration Plan v0.2

Status: **ACTIVE integration portfolio**

Roadmap mapping: `P-046 Security Hygiene Reviewer`, `P-047 README Linting Action`, `P-048 Broken-Link Scanner Action`, and `P-049 Secret-Exposure Detection Action`.

## Decision: integrate, do not reimplement

These opportunity entries overlap mature open-source projects. The DAIS public-good value is a safer beginner/engineer integration layer rather than another scanner:

- `P-046` adopts **OpenSSF Scorecard** for broad open-source security-health signals;
- `P-047` adopts **markdownlint/markdownlint-cli2** and is now a separately completed/released DAIS product;
- `P-048` adopts **Lychee** and is now a separately completed/released DAIS product;
- `P-049` adopts **Gitleaks** and now has a fixed-policy v0.6.0 release candidate with a privacy-minimized evidence boundary.

`scripts/repo_quality_integration_plan.py` remains deliberately non-executing. It only checks a bounded working tree for lexical signs that integrations/configurations may exist. A detected string is not proof that a workflow is enabled, current or secure.

## Baseline safety gates

Every integration proposal carries the same baseline gates:

1. re-read current upstream installation/action documentation at implementation time;
2. pin GitHub Actions or downloaded tools by immutable commit/digest or another verifiable lock strategy;
3. grant the least `GITHUB_TOKEN` permissions needed;
4. never expose raw secret findings or private values in public logs/artifacts;
5. retain rollback for workflow/configuration changes;
6. treat scanner output as a signal requiring context, not an automatic security verdict.

## P-049 privacy boundary is now implemented

The earlier v0.1 plan intentionally stopped before Gitleaks result ingestion because a secret scanner can discover exactly the information that public automation must not leak.

The v0.6.0 candidate closes that design gap without weakening privacy:

- GitHub-hosted Linux x64 only;
- bounded working-tree staging with `.git` excluded;
- Gitleaks v8.30.0 exact official release artifact SHA-256;
- live detector and clean canaries before repository scanning;
- action-owned default-rules config and action-owned empty ignore file;
- repository `.gitleaks.toml`, `.gitleaksignore` and inline `gitleaks:allow` bypass paths disabled;
- `--redact=100` with raw report/stdout/stderr deleted after sanitization;
- public evidence retains counts, rule IDs and metadata-only hashes—not secret values, matching text, source paths or identity/history metadata;
- no Git history scanning and no credential/provider validity checks;
- no arbitrary scanner args, token inputs, repository code execution or repository mutation.

A red-team pass caught a subtle test-design problem before PR: the first synthetic GitHub-PAT-shaped canary contained Gitleaks' intentional sequential-alphabet stopword and would have been correctly suppressed. Upstream issue discussion made that explicit; the canary was replaced with a non-sequential runtime-only value. The product therefore tests the actual detector on every run instead of trusting a nominal process exit.

## Beginner view

> "Use proven scanners, but put a safety layer around them. The DAIS Actions explain what a pass means, fail closed when their safety contract is violated, and avoid leaking the evidence they are trying to protect."

## Engineer view

The repository-quality portfolio composes specialist engines with fixed DAIS policy, immutable supply-chain identity, bounded execution, privacy-minimized evidence and explicit claim limits. Scanner output is never silently promoted to a stronger security/accessibility/correctness claim.

## Current product state

- `P-047` — COMPLETE under its own completion record/release evidence.
- `P-048` — COMPLETE under its own completion record/release evidence.
- `P-049` — IN PROGRESS; v0.6.0 source/CI productization tranche underway; exact-source release, released-ref consumer acceptance and final completion record remain separate gates.
- `P-046` — IN PROGRESS; broader security-hygiene review remains a separate product and must not inherit P-049 completion.
