# Governed Release Readiness

Status: **IN PROGRESS — read-only release-candidate acceptance**

Roadmap mapping: **P-051 Release Automation Action**, **P-057 Release Governance Tool**, and completion support for **P-025 Unified/Variable Memory Configuration Assistant**.

## Search-before-build decision

GitHub already owns tags, releases, release assets, release attestations and release immutability. Mature projects such as Release Please and Changesets already automate version/changelog/release workflows for common repository/package patterns. DAIS therefore should not invent another generic release service.

The remaining public-good gap is narrower: a reusable, fail-closed **pre-release evidence boundary** that can prove an exact public-build candidate is ready to enter a separately governed release-creation step without treating CI, source coverage or a planner assertion as release completion.

## What this tranche adds

`release_readiness_verify.py` independently evaluates:

1. the canonical 19-gate public-build completion record with the existing completion-contract auditor;
2. the exact candidate semantic-version tag syntax;
3. the exact expected source commit against the checked-out Git `HEAD`;
4. required public repository health files;
5. the declared project still being `IN_PROGRESS` before publication;
6. every non-release completion gate being satisfied;
7. the **only** remaining completion blockers being:
   - `version_tag_or_release_published`; and
   - `canonical_handover_or_build_record_updated`.

A passing result is:

```text
READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW
```

It is deliberately **not**:

```text
RELEASED
COMPLETE
PRODUCTION_READY
```

## Workflow

`.github/workflows/governed-release-readiness.yml` provides a GitHub-hosted, read-only acceptance lane.

Its repository permission is only:

```yaml
permissions:
  contents: read
```

The workflow:

- checks out the exact requested source commit;
- runs the release-governance/completion-contract tests;
- evaluates the candidate record;
- retains a sanitized JSON readiness artifact for 14 days;
- asserts that no tag, release, release asset, repository setting or roadmap-completion mutation occurred.

Pull requests exercise the workflow using the P-025 completion fixture and a non-published release-candidate tag. A manual dispatch can later bind an exact candidate commit/tag without creating either one.

## P-025 effect

P-025 currently has 17 of 19 canonical completion gates satisfied. Its only retained blockers are the actual published version/tag/release identity and the final release-bound canonical handover.

This workflow converts that state into a reproducible pre-release test instead of relying on a prose statement that P-025 is nearly ready. It does **not** remove either blocker.

## Release-creation boundary

A future release-creation workflow remains a separate consequential capability. Before it is admitted it must, at minimum:

- run only against an exact reviewed commit;
- use least-privilege `contents: write` only for the release step, with attestation permissions added only when required;
- create a draft release before publication when immutable-release/assets sequencing requires it;
- produce/verify release assets from the exact source revision;
- verify the published tag resolves to the intended commit;
- retain post-publication evidence;
- handle failed draft release/retry/recovery states without silently publishing a partial release;
- treat fork/untrusted-input paths as hostile;
- never infer project completion from publication alone.

## Upstream adoption boundary

For projects already well-served by Release Please, Changesets or ecosystem-specific release tooling, DAIS should wrap/adopt those tools and enforce the evidence contract around them rather than replace their version/changelog engines.

For documentation/toolkit repositories such as the current P-025 proving ground, a small GitHub-native release workflow may be more appropriate than introducing package-oriented version machinery. That choice remains project-specific.

## Safety and privacy

This tranche:

- has no release/tag mutation code;
- performs no network request from the verifier;
- reads only public repository files and Git metadata;
- does not collect credentials, private infrastructure, user/device state or production data;
- does not change repository visibility, licensing or settings;
- does not promote any roadmap subject to COMPLETE.

## Remaining P-051 / P-057 completion gates

These roadmap items remain **IN PROGRESS**. Remaining work includes:

- a separately reviewed release-creation implementation or upstream integration;
- immutable-release/attestation acceptance on an appropriate public test release;
- post-publication tag/asset verification;
- failed-draft/retry recovery acceptance;
- fork/untrusted-input threat review of the write-capable path;
- accessibility/multilingual review of the release operator experience;
- versioned release evidence and canonical handover records.
