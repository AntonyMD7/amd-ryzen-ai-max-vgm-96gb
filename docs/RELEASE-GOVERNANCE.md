# Release Governance v0.3

Status: **IN PROGRESS — reusable implementation built; dedicated release acceptance pending**

Roadmap mapping: `P-051 Release Automation Action` and `P-057 Release Governance Tool`.

## Search-before-build decision

GitHub remains the tag/release system of record. Release Please already automates conventional-commit-driven release PRs, changelogs, tags and GitHub releases across many project types; Changesets already handles package/monorepo versioning and changelog intent. DAIS therefore does not build another package-versioning or changelog engine.

The public-good gap here is a **fail-closed final-publication evidence boundary**: bind an already-reviewed release to an exact commit, refuse untrusted execution contexts and existing identities, create a draft first, verify that draft, publish only after identity checks, verify the public tag target, retain sanitized evidence, and never infer project completion merely from publication.

## Implemented layers

### 1. Plan-only candidate gate

`scripts/release_governance.py` is the original pure planner. It never creates a tag/release and remains useful for early release planning.

### 2. Completion-contract readiness

`scripts/release_readiness_verify.py` and `.github/workflows/governed-release-readiness.yml` bind a proposed release to the canonical 19-gate completion contract and exact checked-out source. Passing means only:

```text
READY_FOR_GOVERNED_RELEASE_CREATION_REVIEW
```

### 3. Reusable generic manifest

`scripts/governed_release_manifest.py` validates a project-agnostic reviewed release manifest. It requires an exact 40-character source commit, semantic tag, bounded DAIS roadmap IDs, safe repository-relative paths, reviewed-file presence, draft-then-publish mode, post-publish exact tag verification, and the permanent rule `roadmap_completion_on_publish=false`.

### 4. Reusable write-capable publisher

`scripts/governed_release_publish.py` is plan-only unless `--execute` is explicitly supplied. Mutation additionally requires a GitHub Actions `push` event on the exact allowed ref and a token supplied only through `GH_TOKEN`.

The publisher:

1. revalidates the manifest;
2. proves the reviewed source is retained and ancestral to release-control `HEAD`;
3. refuses an existing release or tag;
4. creates a draft at the exact source commit;
5. verifies draft tag/title/target identity;
6. publishes the reviewed draft;
7. queries the public release;
8. requires the public tag to resolve exactly to the reviewed commit;
9. writes sanitized evidence with `roadmap_completion_promoted=false`.

If draft verification fails, the draft is deliberately left unpublished as a recovery point. The tool never moves/overwrites a tag to force success.

### 5. Reusable GitHub composite Action

`.github/actions/governed-release/action.yml` exposes the same contract for other repositories. `publish: false` is non-mutating. `publish: true` is intended only for a separately permissioned trusted push job with `contents: write`.

Full operator, security, recovery, accessibility, multilingual and integration guidance is in `docs/GOVERNED-RELEASE-TOOLKIT.md`.

## Real-world evidence already retained

The earlier P-025 lane proved the core draft → verify → publish → exact-tag-verify lifecycle on a real public GitHub release (`v0.1.0`) without automatically promoting completion. That lane was intentionally project-specific. The current tranche generalizes the pattern and adds explicit untrusted-event refusal, reusable manifest semantics and recovery-state tests.

That P-025 release is supporting evidence, not sufficient by itself to declare P-051/P-057 complete. The new generic action/toolkit must itself receive a versioned release and a real generic-path publication acceptance before final completion promotion.

## Security boundary

- no `pull_request_target` write lane;
- PR validation remains read-only;
- write capability requires exact trusted push context;
- no generic shell executor;
- no token is accepted in manifest/CLI arguments or retained evidence;
- no existing release/tag overwrite;
- no automatic roadmap-completion mutation;
- path traversal/dot segments are rejected;
- source commit must be exact, retained and ancestral;
- draft identity is verified before publication;
- public tag SHA is verified after publication.

## Accessibility and multilingual boundary

The product interface is text/JSON/YAML, supports keyboard/CLI operation, emits explicit machine-readable status, and includes a plain-language beginner path. GitHub UI conformance is not claimed. The contract is language-neutral; current operator documentation is English-first, so multilingual support is considered but not claimed as accepted.

## Completion gaps

P-051 and P-057 remain **IN PROGRESS** until the generic path has:

1. green exact-head CI on the reusable implementation;
2. a dedicated exact-source version/tag/release;
3. a real public release executed through the generic action/publisher path;
4. independent post-publication verification and retained sanitized evidence;
5. final release-bound completion records and handover audited against all 19 canonical gates.
