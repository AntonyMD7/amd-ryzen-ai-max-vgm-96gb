# P-054 Contributor Onboarding Assistant — Engineering and Safety Model

Roadmap ID: **P-054**  
Patch candidate: **0.9.1**  
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

## v0.9.0 release finding and v0.9.1 permanent fix

The first released-ref acceptance for `v0.9.0` intentionally ran English twice and Spanish once in a single job. Publication and exact tag verification passed, but the consumer verification failed. The failure exposed two independent acceptance defects rather than being waived:

1. the composite Action used one runner-temporary output directory for every language in a run, so a later language invocation overwrote the earlier language's report/guide path;
2. the release-consumer assertion looked for `missing_required_count` inside the JSON report, while that count is an Action output derived from the report's `missing_required` array.

`v0.9.1` fixes the product-side collision by including language in the Action output directory and strengthens source acceptance to require distinct EN/ES paths in the same job. The release-consumer verifier for the patch must compare the Action outputs for counts and compare `missing_required` arrays inside the reports. `v0.9.0` remains a published historical release but is not accepted as the completion release.

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
        +--> language-isolated output directory outside repository
```

The reusable composite Action writes only under a language-specific `RUNNER_TEMP` directory and may append the generated guide to `GITHUB_STEP_SUMMARY`. It requires no token input and makes no GitHub API request.

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
- Action output is language-isolated and runner-temporary;
- local CLI refuses an output directory inside the audited repository;
- English/Spanish text is fixed product-owned copy rather than repository-controlled shell content.

## Why there is no privileged PR bot

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

The product has no graphical UI. It uses structured JSON and plain Markdown with explicit headings/list semantics; GitHub Action results can be surfaced in the job summary without color-only status. English and Spanish guide text share the same evidence sources and status semantics. Language-specific output paths prevent one localized view from destroying another view's evidence.

This is an accessibility-oriented design review, not WCAG conformance or assistive-technology user acceptance.

## Recovery and rollback

The auditor does not mutate the repository. Delete its external/runner-temporary outputs and rerun. Any later maintainer changes to community-health files are governed independently through normal Git review/revert.

## Acceptance strategy

The patch gate requires:

- all existing adversarial tests;
- a GitHub-hosted composite-Action integration test;
- a pinned real-public `learning-git` checkout audited as read-only data;
- pre/post consumer README SHA-256 identity and clean Git status;
- repeated English runs with identical report SHA-256;
- English and Spanish runs in the same job with distinct report/guide paths;
- EN/ES technical status and `missing_required` truth equivalence;
- sanitized artifact retention;
- no completion promotion.

## Remaining product gates

The failed `v0.9.0` consumer acceptance is retained as evidence rather than hidden. P-054 can become COMPLETE only after the `v0.9.1` patch source passes, an exact-source patch release is published, the released patch ref passes the same multilingual real-public test, release evidence is retained, the final 19-gate audit/handover passes, fresh exact-main verification succeeds, and canonical DAIS is synchronized.
