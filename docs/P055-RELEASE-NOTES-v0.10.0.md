# DAIS CODEOWNERS Assistant v0.10.0

Roadmap ID: **P-055 — CODEOWNERS Assistant**

## Release purpose

`v0.10.0` is the first governed release candidate for the bounded P-055 CODEOWNERS Assistant. The product is intentionally a local preflight, explanation and evidence layer around GitHub's established CODEOWNERS, branch-protection and ruleset surfaces rather than a replacement authorization engine.

## Product capabilities

- Finds the effective local CODEOWNERS file using GitHub-documented precedence: `.github/CODEOWNERS`, repository-root `CODEOWNERS`, then `docs/CODEOWNERS`.
- Fails closed on repository-root escape, symlinks, non-regular files and files above the product's bounded size limit.
- Detects a conservative set of locally recognizable hazards including unsupported negation, bracket character ranges, escaped-leading `#`, missing or malformed owner tokens, duplicate patterns/order ambiguity and missing explicit protection of the CODEOWNERS file itself.
- Emits deterministic privacy-minimized JSON evidence: owner tokens are not retained and rule patterns are represented by SHA-256 fingerprints rather than raw patterns.
- Produces beginner-facing English and Spanish guidance from the same underlying technical state.
- Ships as a reusable composite GitHub Action with runner-temporary outputs and no token input.
- Includes adversarial tests plus hosted valid/invalid fixtures and pinned real-public read-only acceptance.

## Security and privacy boundary

The product performs no GitHub API call, network request, subprocess execution, repository-code execution, CODEOWNERS write, review request, branch-protection mutation, permission change or other repository mutation. It retains no owner tokens in its report.

## Truth boundary

`CODEOWNERS_LOCAL_BASELINE_READY` means only that this bounded local preflight found no condition that it is designed to reject. It does **not** prove that GitHub accepts every pattern, that named users/teams exist or have write access, that branch protection or rulesets require code-owner review, that every repository path has intended ownership, or that repository policy/security is correct. GitHub's server-side behavior remains authoritative.

## Exact-source release requirement

This notes file is merged before publication. The governed release manifest must subsequently bind `v0.10.0` to the exact canonical-main commit that contains the reviewed product implementation, tests, documentation and these release notes. The public tag must resolve exactly to that retained commit.

## Completion boundary

Publishing `v0.10.0` alone does not complete P-055. The released `@v0.10.0` Action must independently pass real-public consumer acceptance with deterministic sanitized evidence and zero consumer mutation. A 19-gate completion record, final handover, fresh post-merge verification and canonical private DAIS synchronization remain separate mandatory gates before P-055 may be promoted to COMPLETE.
