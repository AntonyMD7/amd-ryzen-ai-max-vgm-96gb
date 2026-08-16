# DAIS Governed Release Toolkit

**Roadmap:** P-051 Release Automation Action + P-057 Release Governance Tool  
**Product state:** IN PROGRESS pending a dedicated versioned release and final completion records.

## What problem this solves

GitHub already owns tags and releases, and mature tools such as Release Please and Changesets already automate common version/changelog workflows. DAIS does not replace those systems. This toolkit covers a narrower public-good gap: **fail-closed publication of an already-reviewed exact source revision, with draft verification, immutable intent, post-publication tag verification, recovery evidence, and a hard rule that publishing never equals project completion by itself.**

Use Release Please or Changesets for version/changelog orchestration when they fit your project. Use this toolkit when you also need an independently reviewable safety/evidence boundary around the final GitHub release operation.

## Beginner path

1. Prepare your project normally and get tests/CI green.
2. Choose the exact commit you intend to release.
3. Add a small JSON manifest that names the tag, title, source commit, release notes and reviewed files.
4. Run the action with `publish: false` first. It validates intent and performs no repository mutation.
5. Only from a trusted push workflow on your protected release branch, grant `contents: write` and set `publish: true`.
6. The action refuses an existing tag/release, creates a draft, verifies the draft identity, publishes it, and then verifies the public tag still resolves to the exact reviewed commit.
7. Keep the emitted evidence file. Publication does **not** automatically mark any DAIS roadmap item complete.

If something fails after the draft is created but before publication, the draft is intentionally left unpublished. Inspect or delete that draft manually after reviewing the retained evidence; do not silently retry over unknown state.

## Components

- `.github/actions/governed-release/action.yml` — reusable composite GitHub Action.
- `scripts/governed_release_manifest.py` — dependency-free, read-only manifest validator.
- `scripts/governed_release_publish.py` — plan-only by default; write capability requires `--execute` plus a trusted GitHub Actions push context.
- `tests/test_governed_release_toolkit.py` — adversarial contract tests including untrusted-event refusal, traversal rejection, draft mismatch stop, exact tag verification and secret non-retention.

## Manifest contract

```json
{
  "schema_version": "1.0",
  "release_id": "MY-PROJECT-V1.2.3",
  "roadmap_ids": ["P-051"],
  "tag": "v1.2.3",
  "title": "My Project v1.2.3",
  "source_commit": "0123456789abcdef0123456789abcdef01234567",
  "notes_file": "RELEASE-NOTES-v1.2.3.md",
  "required_files": [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "START-HERE.md",
    "RELEASE-NOTES-v1.2.3.md"
  ],
  "publication_mode": "DRAFT_THEN_PUBLISH",
  "post_publish_exact_tag_verification_required": true,
  "roadmap_completion_on_publish": false,
  "make_latest": true
}
```

The manifest rejects path traversal, duplicate/invalid roadmap IDs, non-semantic tags, non-exact commit identities, missing reviewed files, alternate publication modes, and any attempt to equate release publication with roadmap completion.

## Reusable action example

After this toolkit itself has a stable released tag, a consumer workflow can pin that exact version:

```yaml
name: Governed release
on:
  push:
    branches: [main]
    paths:
      - 'release/my-project-v1.2.3.json'
      - 'RELEASE-NOTES-v1.2.3.md'

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/governed-release@<PINNED_RELEASE_TAG>
        with:
          manifest: release/my-project-v1.2.3.json
          publish: 'false'

  publish:
    needs: validate
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    permissions:
      contents: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false
      - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/governed-release@<PINNED_RELEASE_TAG>
        with:
          manifest: release/my-project-v1.2.3.json
          publish: 'true'
          allowed-ref: refs/heads/main
          evidence-file: governed-release-evidence.json
```

Consumers should pin a release tag or commit appropriate to their supply-chain policy. Do not execute a mutable branch reference for a write-capable release action.

## Security model

The write path requires all of the following:

- explicit `--execute` / `publish: true`;
- `GITHUB_ACTIONS=true`;
- exact `GITHUB_EVENT_NAME=push`;
- exact configured trusted ref;
- a well-formed `owner/repo` repository identity;
- `GH_TOKEN` present in the environment;
- reviewed source commit retained in Git history and an ancestor of the release-control `HEAD`;
- no pre-existing release or tag with the requested name.

The publisher uses fixed argument arrays with `shell=False`; it has no generic shell executor. Token values are never copied into evidence. Pull-request execution is refused even if a token is accidentally present. This deliberately avoids the elevated/untrusted-code hazards associated with write-capable pull-request contexts.

## Recovery and idempotency

The action is deliberately **non-idempotent across an already-created tag/release**: it fails closed rather than overwriting or moving release identity.

State transitions are:

```text
MANIFEST_VALID
    ↓
TRUSTED_PUSH_VERIFIED
    ↓
NO_EXISTING_TAG_OR_RELEASE
    ↓
DRAFT_CREATED_RECOVERY_AVAILABLE
    ↓
DRAFT_IDENTITY_VERIFIED
    ↓
PUBLISHED
    ↓
EXACT_PUBLIC_TAG_VERIFIED
```

If failure occurs before draft creation, repository release state should remain unchanged. If failure occurs after draft creation and before publication, leave the draft unpublished and inspect it. If post-publication verification fails, treat the release as an incident requiring operator review; never move the tag automatically to make evidence pass.

## Accessibility and multilingual review

The primary interface is text/JSON/YAML and is keyboard-operable through GitHub and the command line. Error messages are explicit and machine-readable evidence is plain JSON. The beginner instructions avoid requiring knowledge of the implementation internals. No WCAG conformance or assistive-technology user acceptance is claimed for GitHub's own interface.

The manifest and evidence formats are language-neutral. Human documentation is currently English-first; localized operator documentation can be layered without changing the safety contract. This is a considered multilingual path, not multilingual acceptance.

## Threat review

The main threats and controls are:

| Threat | Control |
|---|---|
| Fork/PR obtains write token | publisher refuses non-`push` event; caller keeps PR permissions read-only |
| Tag moved to different source | pre-existing tag refused; exact post-publish remote tag SHA required |
| Unreviewed file/path injection | bounded repository-relative paths; traversal/dot segments refused |
| Manifest says publication means COMPLETE | hard-schema refusal; evidence always records `roadmap_completion_promoted=false` |
| Draft identity drift | draft tag/title/target commit verified before publish |
| Secret leakage | token read only from environment and omitted from evidence |
| Partial failure | evidence written after draft creation; unpublished draft retained for recovery |
| Silent overwrite/retry | existing tag/release is a hard refusal |

## Search-before-build position

GitHub release APIs/CLI remain the release system of record. Release Please remains a strong choice for conventional-commit-driven release PRs and multi-language repositories. Changesets remains a strong choice for package/monorepo versioning and changelog workflows. The DAIS toolkit composes with those systems; it is not a competing package-versioning engine.

## Known limitations

- Requires GitHub CLI and Git in the execution environment.
- The write path currently targets GitHub releases only.
- It does not build artifacts, decide semantic-version impact, generate changelogs, sign binaries, or prove artifact semantic quality.
- It does not configure branch protection or immutable-release repository settings.
- `contents: write` is still consequential authority and should exist only in the trusted publish job.
- Human review of release notes/product scope remains outside the tool.
- Publication success does not satisfy the DAIS completion contract by itself.

## Completion evidence still required

Before P-051/P-057 can move to `COMPLETE`, the reusable action/toolkit must be released from an exact attested source, exercised in a real public release using its generic path, independently verify that publication, retain evidence, and bind final completion records/handover to the released toolkit version.
