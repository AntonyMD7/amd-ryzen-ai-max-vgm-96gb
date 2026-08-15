# GitHub Agentic Safety Plans v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-042 Issue Triage GitHub App`, `P-043 PR Explainer/Reviewer App`, and `P-061 Self-Healing Documentation CI`.

## Search-before-build decision

GitHub's open-source **Agentic Workflows (`gh-aw`)** already provides a security-oriented pattern for AI automations: analysis can remain read-only while validated safe outputs perform controlled GitHub writes. GitHub also publishes issue-triage and continuous-documentation workflow patterns. DAIS should integrate with those guardrails rather than create an unconstrained autonomous GitHub bot.

`scripts/github_agentic_safety_plans.py` is a deterministic prefilter/reference contract that can sit before a future `gh-aw` or equivalent governed write path.

## Issue triage

The issue mode classifies only coarse transparent categories. Potential security reports are routed away from public automation and never automatically commented/labelled. Bug/documentation/feature keywords produce suggestions only; unfamiliar issues remain `NEEDS_HUMAN_TRIAGE`.

No severity score is invented. Before a GitHub write, a future adapter must search duplicates/context and use a safe-output/approval boundary.

## PR review/explanation

The PR mode consumes only changed-file metadata and CI state. It flags review focus for workflow/action changes, security-sensitive paths, migrations/schema, dependency lockfiles, deployment/infra, and unusually large changes. It does not read diff content and therefore explicitly requires the actual diff to be reviewed before any approval.

It can never auto-approve or auto-merge. GitHub's workflow-security guidance on untrusted input and risky triggers such as `pull_request_target` must be part of any future agentic execution path.

## Self-healing documentation

The docs mode checks basic public-file/navigation presence and emits proposed repairs. "Self-healing" is defined as **branch + reviewable PR + CI**, not silently rewriting protected main.

Automated documentation must not invent commands, compatibility, support claims, versions or URLs. Link health should be delegated to the mature link checker selected under P-048; Markdown linting to P-047.

## Beginner view

> "The automation can suggest how to triage an issue, what parts of a PR deserve extra attention, or what documentation is missing. It does not secretly label, approve, merge or rewrite the project."

## Completion gaps

All mapped items remain **IN PROGRESS**. Completion requires hardened `gh-aw`/GitHub App integration, safe-output write acceptance, permission/fork/untrusted-input tests, semantic issue/PR analysis with evaluation datasets, security-report private-routing acceptance, automatic documentation patch generation with source grounding, accessible/multilingual UX, public release/distribution and canonical completion evidence.
