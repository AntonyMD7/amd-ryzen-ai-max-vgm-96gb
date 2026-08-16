# P-052 — Beginner-Safe PR Creator: START HERE

Status: **IN PROGRESS product candidate v0.7.0**

This Action helps a contributor turn an already-pushed, reviewed branch into a **draft pull request** without silently skipping tests, scope review, secret review, or rollback thinking.

It has two deliberately separate modes:

1. **plan** — network-free and non-mutating; validates the intended PR and returns an exact `plan-sha256`.
2. **create** — requires the same inputs, the exact reviewed plan hash, the literal confirmation `CREATE_DRAFT_PR`, and repository-scoped PR write authority. It can create only a same-repository **draft** PR.

The product never pushes a branch, requests reviewers, marks a PR ready, approves, merges, closes, or changes an existing non-draft PR.

## Safest first use: plan only

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
    with:
      persist-credentials: false

  - id: pr-plan
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/beginner-safe-pr@YOUR_REVIEWED_REF
    with:
      mode: plan
      repository: ${{ github.repository }}
      title: Improve beginner documentation
      summary: Adds a clearer START-HERE path.
      base: main
      head: docs/beginner-path
      tests-run: 'true'
      ci-expected: 'true'
      secrets-reviewed: 'true'
      scope-reviewed: 'true'
      rollback-considered: 'true'
```

Review `steps.pr-plan.outputs.plan-sha256` and the inputs before granting write authority.

## Create the reviewed plan as a draft

Use a separate trusted `workflow_dispatch` or same-repository `push` job with the narrow permission GitHub's API requires:

```yaml
permissions:
  contents: read
  pull-requests: write

steps:
  - id: plan
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/beginner-safe-pr@YOUR_REVIEWED_REF
    with:
      mode: plan
      repository: ${{ github.repository }}
      title: Improve beginner documentation
      summary: Adds a clearer START-HERE path.
      base: main
      head: docs/beginner-path
      tests-run: 'true'
      ci-expected: 'true'
      secrets-reviewed: 'true'
      scope-reviewed: 'true'
      rollback-considered: 'true'

  - id: create
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/beginner-safe-pr@YOUR_REVIEWED_REF
    with:
      mode: create
      repository: ${{ github.repository }}
      title: Improve beginner documentation
      summary: Adds a clearer START-HERE path.
      base: main
      head: docs/beginner-path
      tests-run: 'true'
      ci-expected: 'true'
      secrets-reviewed: 'true'
      scope-reviewed: 'true'
      rollback-considered: 'true'
      expected-plan-sha256: ${{ steps.plan.outputs.plan-sha256 }}
      confirmation: CREATE_DRAFT_PR
      github-token: ${{ secrets.GITHUB_TOKEN }}
```

A repository can separately disable GitHub Actions from creating pull requests. If so, the Action fails rather than weakening repository policy.

## What the outputs mean

- `decision=READY_FOR_DRAFT_CREATE` means the bounded plan checks passed. It does **not** mean the code is correct or merge-ready.
- `plan-sha256` identifies the exact reviewed plan inputs and safety-check state.
- `created=true` means this invocation created a new draft PR.
- `created=false` with `EXISTING_DRAFT_REUSED` means an already-open matching draft was found and reused idempotently.

## Important safety rules

- Never paste credentials, tokens, private keys, private repository content, medical/personal data, or other secrets into PR title/summary inputs.
- P-052 refuses several obvious secret-like patterns, but it is **not** a complete DLP scanner. Use P-049 for repository secret-exposure scanning.
- Create mode is intentionally refused on `pull_request_target`, `workflow_run`, issue/comment events, fork-qualified heads, and cross-repository targets.
- The tool will not change a matching PR that is already non-draft.
- Normal review, branch protection, CI and maintainer governance still apply.

## Recovery

P-052 does not modify files or branches. If a newly-created draft PR is unwanted, close it through normal GitHub controls; the source branch remains unchanged. If an existing matching draft is detected, P-052 returns it instead of creating a duplicate.

## Current completion boundary

v0.7.0 source still remains **IN PROGRESS** until hosted source CI is green, a governed versioned release exists, the released ref creates and verifies a disposable real draft PR under the documented narrow permission boundary, evidence is retained, the final completion record passes all canonical gates, and DAIS canonical status is synchronized.
