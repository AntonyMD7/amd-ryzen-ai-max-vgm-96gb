# P-054 Contributor Onboarding Assistant — Engineering and Safety Model

Roadmap ID: **P-054**  
Candidate version: **0.9.0**  
State: **IN PROGRESS**

## Product decision

Search-before-build found that GitHub already owns the platform-level onboarding primitives: Community Standards/community profiles, `CONTRIBUTING.md`, security policies, issue/PR templates, the repository `contribute` page, and `good first issue` / `help wanted` discovery. P-054 therefore does not create a competing community-management system.

Official upstream references reviewed for this tranche:

- GitHub Community Profiles: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories
- Contributor guidelines: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors
- Healthy contribution setup: https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions
- Secure `pull_request_target` guidance: https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target
- GitHub Actions secure-use reference: https://docs.github.com/en/actions/reference/security/secure-use

The DAIS value is a portable, network-free, privacy-minimized **local audit + guide contract** around those established surfaces.

## Architecture

```text
trusted Python/Action source
        |
        v
explicit repository root
        |
        +--> containment + symlink + size guards
        |
        +--> bounded known community-health paths only
        |
        +--> metadata + SHA-256 fingerprints
        |
        +--> deterministic status/gap model
        |       |
        |       +--> JSON evidence
        |       +--> EN/ES Markdown onboarding guide
        |
        +--> output directory must be outside repository
```

The reusable composite Action writes only under `RUNNER_TEMP` and may append the generated guide to `GITHUB_STEP_SUMMARY`. It requires no token input and makes no GitHub API request.

## Required vs recommended surfaces

P-054's required local baseline is intentionally small:

1. root `README.md`;
2. contribution guidelines in root, `.github`, or `docs`;
3. security policy in root, `.github`, or `docs`;
4. a recognizable root license file.

Recommended surfaces add a code of conduct, support guidance, pull-request template, issue template/form, and optional DAIS `START-HERE.md`.

These categories are a **DAIS onboarding baseline**, not a reimplementation or claimed equivalent of GitHub's server-side Community Standards score. GitHub can also supply organization/account default community-health files that are not present in a clone, so a local gap is never relabeled as proof that GitHub has no effective default.

## Threat model

### Assets

- repository source and contributor guidance;
- workflow token/secrets;
- runner filesystem;
- public contributor privacy;
- maintainer trust.

### Untrusted inputs

- repository paths and files being audited;
- issue-template filenames;
- caller-provided root/language values.

### Controls

- no repository code execution;
- no shelling out from the Python auditor;
- no network/API client;
- no secret/token input;
- candidate and issue-template symlinks fail closed;
- audited bounded files must be regular, non-empty, <= 1 MiB;
- no absolute local path is emitted in JSON evidence;
- Action output is runner-temporary;
- local CLI refuses an output directory inside the audited repository;
- English/Spanish text is fixed product-owned copy rather than repository-controlled shell content.

## Why there is no privileged PR bot in v0.9.0

GitHub documents `pull_request_target` as an elevated-trust event. Combining it with untrusted PR checkout/execution can produce a supply-chain compromise. P-054 therefore does not need or use `pull_request_target`, does not fetch fork code with privileged credentials, and does not post authenticated comments.

A future optional posting layer, if justified, must be a separately reviewed capability with least-privilege write permission, trusted-base code only, no execution of contributor-controlled content, idempotency, abuse/rate controls, and explicit evidence. It is not smuggled into this read-only product.

## Evidence semantics

`ONBOARDING_BASELINE_READY` means every P-054 required **local** surface exists as a bounded regular file.

It does not prove:

- GitHub's current Community Standards server-side result;
- validity/correctness of the policies' prose;
- availability of suitable `good first issue` work;
- contributor identity/trustworthiness;
- maintainer responsiveness;
- accessibility conformance;
- project safety/security;
- license compatibility for a specific contribution.

The JSON report has hard-false claims for these stronger statements.

## Accessibility and localization

The product has no graphical UI. It uses structured JSON and plain Markdown with explicit headings/list semantics; GitHub Action results can be surfaced in the job summary without color-only status. English and Spanish guide text share the same underlying evidence object so localization cannot alter technical truth.

This is an accessibility-oriented design review, not WCAG conformance or assistive-technology user acceptance.

## Recovery and rollback

The auditor does not mutate the repository. Delete its external/runner-temporary outputs and rerun. Any later maintainer changes to community-health files are governed independently through normal Git review/revert.

## Acceptance strategy

The productization gate requires:

- pure adversarial tests for missing states, deterministic hashing, symlink refusal, no internal output, localization and source-level no-network/no-subprocess boundaries;
- a GitHub-hosted composite-Action integration test;
- a pinned real-public `learning-git` checkout audited as read-only data;
- pre/post consumer README SHA-256 identity;
- repeated runs with identical report SHA-256;
- sanitized artifact retention;
- no completion promotion.

## Remaining product gates

Source/CI success is not completion. A versioned exact-source release, released-ref public acceptance, final 19-gate audit/handover, fresh exact-main verification and canonical DAIS synchronization remain mandatory.
