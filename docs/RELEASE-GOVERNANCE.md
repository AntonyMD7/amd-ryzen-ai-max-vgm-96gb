# Release Governance v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-051 Release Automation Action` and `P-057 Release Governance Tool`.

## Search-before-build decision

GitHub already provides releases/tags, release APIs, artifact attestations and an immutable-release model. Established ecosystems such as Changesets already address version/changelog workflows for package projects. DAIS should not build another generic release service.

The gap addressed by `scripts/release_governance.py` is a **fail-closed pre-release contract** that refuses automation when the public-build completion evidence needed for a trustworthy release is missing.

## Plan-only gate

The planner accepts an explicit candidate record with:

- semantic-version release tag;
- exact 40-character source commit SHA;
- public-project file presence;
- CI/test/evidence/security/accessibility/recovery/release-note assertions;
- artifact names and SHA-256 values;
- optional request for GitHub artifact attestation.

It emits `BLOCKED` or `READY_FOR_GOVERNED_RELEASE_WORKFLOW`. It never creates the tag or release.

A ready result proposes only the release permissions implied by the requested path. Base release creation needs `contents: write`; an attestation path additionally proposes `id-token: write` and `attestations: write`. A real workflow must independently validate the caller assertions rather than trust this planner output.

## Release sequence

1. re-verify the exact source commit and all release gates in CI;
2. create a draft release where appropriate, especially when immutable-release workflows require assets to be complete before publication;
3. build assets from the exact source revision and retain hashes/provenance;
4. generate/verify attestations when configured;
5. publish only after assets, release notes and evidence are complete;
6. independently verify the published tag/commit/assets and retain that evidence.

GitHub's immutable-release capability can make published release assets/tags resistant to later changes and can generate release attestation evidence. That platform capability should be used rather than approximated in custom DAIS code.

## Beginner view

> "Before publishing a release, this check makes sure the project has the required documentation, tests, evidence and exact source version. If anything important is missing, it says BLOCKED instead of publishing anyway."

## Completion gaps

Both roadmap items remain **IN PROGRESS**. Completion requires a reviewed reusable release workflow/action, independent verification of each candidate assertion, immutable-release/attestation acceptance on a public test project, project-specific versioning adapters, fork/untrusted-input threat review, recovery from failed draft releases, accessibility/multilingual docs, versioned release evidence and canonical completion records.
