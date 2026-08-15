# Contributor Safety Tools v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-052 Beginner-Safe PR Creator`, `P-054 Contributor Onboarding Bot`, and `P-055 CODEOWNERS Assistant`.

## Design boundary

GitHub already owns pull requests, review requests and CODEOWNERS evaluation. The DAIS layer should make those workflows easier and safer without bypassing review or mutating repositories from unreviewed input.

`scripts/contributor_safety_tools.py` therefore provides three plan-only modes:

- `pr` — generate a bounded PR title/body/base/head payload and recommend draft/blocking when tests, CI expectation, secret review, scope review or rollback consideration are missing;
- `onboarding` — turn explicit project-file presence into a beginner contributor checklist and maintainer-gap list;
- `codeowners` — generate proposed CODEOWNERS text from explicit path/owner mappings and require GitHub-side syntax/access verification before write.

## CODEOWNERS authority

GitHub evaluates CODEOWNERS patterns and can automatically request reviewers for matching changes. GitHub's current documentation also exposes CODEOWNERS syntax/error checks and recommends protecting the ownership rules themselves. This tool does not duplicate GitHub's final parser; it validates only a narrow proposal grammar and tells the caller to use GitHub's authoritative error surface after a proposed change.

## Beginner-safe PR behavior

A generated PR payload is not automatically submitted. Missing safety checks cause `DRAFT_OR_BLOCKED_UNTIL_CHECKS_COMPLETE`, and the payload marks the missing checklist items. The creator never pushes branches, opens a PR or requests reviewers.

## Onboarding behavior

The onboarding layer points contributors to README, START-HERE, CONTRIBUTING, SECURITY and LICENSE and encourages issue/discussion scoping for non-trivial work. Missing public guidance is surfaced as a **maintainer gap**, not blamed on a beginner contributor.

## Security/privacy

No GitHub API call, collaborator change, review request, branch mutation or CODEOWNERS write occurs. Inputs should contain public project metadata only; do not place credentials, private repository content or personal data into generated public PR text.

## Completion gaps

All mapped items remain **IN PROGRESS**. Completion requires GitHub API adapters with explicit confirmation/lease gates, real public-repository acceptance, fork-permission and untrusted-input threat testing, GitHub-authoritative CODEOWNERS error integration, accessible/multilingual onboarding, dedicated releases/distribution and canonical completion evidence.
