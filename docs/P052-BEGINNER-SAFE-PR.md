# P-052 — Beginner-Safe PR Creator v0.7.0

Status: **IN PROGRESS product candidate**

## Public-good problem

Opening a pull request is mechanically easy, but beginners can accidentally publish secrets, target the wrong branch, bypass expected checks, or confuse PR creation with review/merge approval. P-052 narrows the operation to a reviewable draft-PR boundary and makes the safety state machine-visible.

## Search-before-build / upstream boundary

GitHub already owns branches, pull requests, draft state, repository permissions, notifications, branch protection and review. The REST `Create a pull request` endpoint is therefore the mutation authority; P-052 does not implement another forge or PR database.

GitHub's current security guidance treats privileged workflow contexts and untrusted pull-request code as a repository-compromise risk. Fork PRs normally receive read-only `GITHUB_TOKEN` permissions and do not receive ordinary secrets. P-052 therefore does not try to defeat those controls: v0.7.0 create mode accepts only same-repository branches and only trusted `push` or `workflow_dispatch` event contexts.

## Architecture

```text
public inputs + five safety assertions
            |
            v
 network-free validation
            |
            v
 canonical plan ---- SHA-256 lease
            |              |
            | review       | exact equality required
            v              v
 explicit CREATE_DRAFT_PR confirmation
            |
            v
 same-repository/event/token preflight
            |
            v
 GET base ref -> GET head ref -> GET matching open PR
            |
      +-----+------+
      |            |
 existing draft   none
      |            |
 return/reuse     POST /pulls with draft=true
                   |
                   v
             verify returned base/head/draft
```

The mutation path is intentionally one API endpoint after read-only preflight. There is no branch push, file write, reviewer request, ready-for-review transition, approval, merge, close, label, milestone or collaborator capability.

## Plan-hash lease

The SHA-256 covers canonical JSON containing:

- tool/schema version;
- exact repository;
- exact base/head branches;
- public title/summary;
- all five safety assertions;
- the computed readiness decision and draft-only invariant.

Create mode recomputes the plan from the same invocation inputs and requires exact equality with `expected-plan-sha256`. A changed title, branch, summary or check state invalidates the lease. The hash is an anti-TOCTOU binding for reviewed plan data; it is not a cryptographic signature or human identity proof.

## Five required safety assertions

1. `tests_run`
2. `ci_expected`
3. `secrets_reviewed`
4. `scope_reviewed`
5. `rollback_considered`

They are explicit operator assertions, not independent proof. A true flag never causes P-052 to claim that tests actually passed, that no secret exists, or that rollback is guaranteed.

## Threat model and controls

### Privileged untrusted workflow execution

Risk: a write-capable token combined with attacker-controlled workflow content can mutate the repository.

Control: create mode permits only `push` and `workflow_dispatch` and explicitly refuses `pull_request_target` and every other event. The documented caller uses only `pull-requests: write` plus read-only contents. No untrusted code checkout is required by the mutation engine.

### Cross-repository/fork confusion

Risk: a token or branch expression could be used against an unintended repository/fork.

Control: `repository` must exactly equal runtime `GITHUB_REPOSITORY`; base/head use a narrow branch grammar; fork-qualified `owner:branch` heads are refused; both refs must exist in the same repository before POST.

### Review bypass

Risk: automation could create something merge-ready or approve/merge it.

Control: POST payload hard-codes `draft=true` and `maintainer_can_modify=false`; the response must confirm the exact reviewed base/head and draft state. No ready/review/merge endpoint exists.

### Duplicate/replay

Risk: retries create duplicate PRs.

Control: exact base/head open-PR discovery occurs first. One matching draft is reused idempotently; multiple matches or one non-draft match fail closed.

### Accidental public secret disclosure

Risk: title/summary are public GitHub content.

Control: several high-signal token/private-key/password patterns are refused without echoing the value. This is a narrow preflight, not DLP. P-049 remains the dedicated repository secret-exposure product.

### API error leakage

Risk: GitHub error bodies can contain caller-controlled or sensitive material.

Control: API failures expose only bounded operation/status context; response bodies and token values are never propagated into P-052 output.

## Permissions

Plan mode needs no GitHub API authority.

Create mode needs a caller-supplied repository-scoped token with **pull requests: write**. Repository/organization Actions policy can additionally prohibit Actions-created PRs; P-052 treats that as an authority refusal rather than trying to bypass it.

## Accessibility and language

The product has no pointer-only or color-only UI. Human-facing output uses plain status names and stable machine outputs. The beginner guide separates planning from mutation and explains recovery. Human documentation is English-first; stable decision/hash/status keys support localization, but multilingual human acceptance is not yet claimed.

## Recovery / rollback

P-052 never changes the source branch. The only write is draft PR creation. The current product deliberately does not auto-close a newly-created PR because that would add a second mutation authority and could erase review context unexpectedly. An unwanted draft can be closed through standard GitHub governance. Retries reuse an existing matching draft.

## Real-world acceptance required before completion

Completion requires a released ref to run in a controlled public repository with the documented narrow permissions, create an actual disposable draft PR from an existing same-repository branch, independently verify:

- exact released source identity;
- draft state;
- exact base/head/title boundary;
- no file/branch mutation;
- no reviewer/merge/ready transition;
- idempotent second invocation;
- retained privacy-safe evidence;

and then close the disposable draft through an explicitly separate cleanup step. Source-only mock tests do not satisfy this gate.

## Known limitations

- GitHub.com repository PRs only in v0.7.0; no GitLab/Bitbucket/GHES compatibility claim.
- Same-repository branches only; forks are deliberately out of scope.
- Create mode depends on GitHub repository/organization permission settings.
- It does not push branches or determine whether source code is correct.
- Safety assertions are attestations from the caller, not independent test/secret/rollback verification.
- Obvious sensitive-pattern refusal is not comprehensive secret detection.
- No WCAG conformance or multilingual-user acceptance claim.
- No roadmap completion claim until release and real draft-PR acceptance gates are independently satisfied.
