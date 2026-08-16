# DAIS Secret Exposure Detection Action v0.6.0 — Release Candidate Notes

Roadmap ID: **P-049**

Release status: **NOT YET PUBLISHED**. These notes describe the candidate source only. P-049 remains IN PROGRESS until the governed exact-source release and final completion audit are satisfied.

## What ships

- reusable composite Action at `.github/actions/secret-exposure-scan`;
- Gitleaks `v8.30.0` Linux x64 pinned by exact GitHub-published SHA-256;
- mandatory live positive and clean detector canaries on every invocation;
- working-tree-only `dir` scanning—no Git history traversal;
- action-owned fixed default-rules configuration;
- repository `.gitleaksignore`, repository config and inline `gitleaks:allow` bypasses disabled;
- bounded staging copy with traversal/symlink/resource protections;
- 100% scanner redaction and privacy-minimized public JSON evidence;
- no raw scanner result/stdout/stderr retention;
- GitHub-hosted Linux x64 only;
- no credential/token/action-secret input;
- no repository mutation;
- adversarial tests, dedicated hosted acceptance, beginner guide, architecture/threat model and privacy-safe support path.

## Supply-chain identity

Engine: `gitleaks/gitleaks v8.30.0`

Official Linux x64 release asset SHA-256:

`79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e`

The Action refuses an artifact that does not match that digest and refuses a runtime whose reported version is not exactly `8.30.0`.

## Important non-claims

A clean P-049 run is not proof that every secret is absent, that Git history is clean, that a credential is valid/revoked, or that the repository is secure. False negatives and false positives remain possible.

A finding must be handled privately. Do not copy it into a public issue or CI artifact.

## Upgrade model

Upstream engine updates are reviewed product changes, not automatic moving-version adoption. An upgrade must repeat supply-chain review, live detector canary acceptance, privacy/bypass tests and exact artifact verification before promotion.
