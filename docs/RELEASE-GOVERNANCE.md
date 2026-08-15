# Release Governance v0.2

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-051 Release Automation Action` and `P-057 Release Governance Tool`.

## Search-before-build decision

GitHub already provides releases/tags, release APIs, artifact attestations and an immutable-release model. Established ecosystems such as Release Please and Changesets already address version/changelog/release workflows for common project/package patterns. DAIS should not build another generic release service.

The public-good gap addressed here is a **fail-closed release evidence contract** that refuses progression when trustworthy public-build completion evidence is missing and independently binds the candidate to the exact checked-out source revision.

## Layer 1 — plan-only candidate gate

`scripts/release_governance.py` remains a pure planner. It accepts an explicit candidate record with:

- semantic-version release tag;
- exact 40-character source commit SHA;
- public-project file presence;
- CI/test/evidence/security/accessibility/recovery/release-note assertions;
- artifact names and SHA-256 values;
- optional request for GitHub artifact attestation.

It emits `BLOCKED` or `READY_FOR_GOVERNED_RELEASE_WORKFLOW`. It never creates the tag or release. Caller-supplied booleans remain assertions and therefore are not sufficient by themselves for release admission.

## Layer 2 — independently verified release readiness

`scripts/release_readiness_verify.py` and `.github/workflows/governed-release-readiness.yml` add a stronger read-only lane.

The verifier:

1. runs the canonical 19-gate completion-contract audit;
2. requires the subject to remain `IN_PROGRESS` before release publication;
3. requires all non-release completion gates to be satisfied;
4. permits only the release-publication gate and final release-bound handover gate to remain blocking;
5. binds the candidate tag to exact semantic-version syntax;
6. binds the requested exact source commit to the actual checked-out Git `HEAD`;
7. independently verifies the required public project files exist.

A passing result is only:

```text
READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW
```

It is never treated as `RELEASED` or `COMPLETE`.

The hosted readiness workflow runs with only:

```yaml
permissions:
  contents: read
```

It runs the release/completion contract tests and retains sanitized readiness evidence. It has no tag/release creation step and no write permission.

## Release creation remains a separate capability

The write-capable release step is intentionally not bundled into readiness. A future admitted implementation should:

1. consume a successful exact-commit readiness record;
2. re-verify that the candidate commit is still the intended source;
3. use least-privilege `contents: write` only for release creation, adding `id-token: write` / `attestations: write` only when the selected attestation path requires them;
4. create a draft first when release immutability/assets sequencing makes that appropriate;
5. build/attach assets from the exact source and retain digests/provenance;
6. publish only after release notes/assets/evidence are complete;
7. independently verify the published tag resolves to the intended commit and verify release assets/attestations where applicable;
8. retain post-publication evidence and then update the release-bound canonical handover.

## Beginner view

> "Before publishing a release, DAIS checks that the project has the required documentation, tests, evidence, safety reviews and exact source version. If anything important is missing, it stops instead of publishing anyway. Passing the check still does not publish the release."

## Security boundary

The read-only readiness path:

- never creates or moves a Git tag;
- never creates/edits/publishes a release;
- never uploads release assets;
- never changes repository settings;
- never changes roadmap completion state;
- permits completion-record input only from a constrained public `examples/` basename;
- retains no credential or private infrastructure data.

The future write-capable path must receive a separate fork/untrusted-input threat review and failed-draft/retry/recovery acceptance before it is eligible for reuse.

## Completion gaps

Both roadmap items remain **IN PROGRESS**. Completion still requires a reviewed reusable release-creation implementation or upstream integration, immutable-release/attestation acceptance on an appropriate public test release, independent post-publication verification, project-specific versioning adapters, fork/untrusted-input threat review for the write path, recovery from failed draft releases, accessibility/multilingual operator review, versioned release evidence and canonical completion records.
