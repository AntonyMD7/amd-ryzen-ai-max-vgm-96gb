# DAIS README Lint Action v0.4.0

Roadmap: **P-047 — README Linting Action**

## Purpose

v0.4.0 is the first governed product release candidate for P-047. It provides a beginner-safe README-only integration around the established markdownlint ecosystem rather than a new Markdown parser.

## Included

- reusable composite Action at `.github/actions/readme-lint`;
- immutable upstream `markdownlint-cli2-action` commit `21c1be1b93ad9ed58fa840aacc3f279cde2a72ff` (upstream release v24.2.0);
- fixed DAIS README profile with repository-controlled custom rules/plugins intentionally unavailable;
- explicit `root`, `status`, `readme-count`, and `upstream-commit` contract;
- non-mutating operation with upstream auto-fix hard-disabled;
- traversal, symlink, count, single-file-size, combined-size, no-README, and malformed-root refusal;
- hosted positive/negative acceptance and input-immutability proof;
- beginner, engineering/security, recovery, accessibility, multilingual-path, and support documentation.

## Truth boundary

A PASS means only that selected bounded `README.md` files satisfy the fixed Markdown style/structure profile. It does not prove factual correctness, completeness, accessibility conformance, link health, security hygiene, freshness, or overall repository quality.

## Runtime scope

v0.4.0 targets GitHub Actions Linux runners capable of running the upstream Node 24 action and Python 3 preflight. The product does not claim GitHub Enterprise Server, local `act`, Windows-hosted, or macOS-hosted runner acceptance in this release.

## Security and privacy

The release uses a fixed configuration specifically to avoid repository-controlled `customRules`, Markdown-it plugins, or custom formatters becoming implicit code-execution surfaces. README content is read for linting and may influence diagnostics; do not use public CI on sensitive documentation.

## Completion status

Publishing v0.4.0 is necessary but not sufficient for P-047 COMPLETE. Completion requires exact release verification, released-ref acceptance against representative public repositories, retained evidence, the canonical 19-gate record, final handover, and independent completion audit.
