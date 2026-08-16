# Start Here — DAIS Governed Release Toolkit

**Roadmap:** P-051 Release Automation Action + P-057 Release Governance Tool  
**Audience:** maintainers who need to publish an already-reviewed GitHub release from an exact source revision without silently moving tags, overwriting releases, or treating publication as proof that a project is complete.

## The shortest safe path

If you only need conventional version calculation, changelog generation, or release PRs, use a mature upstream tool such as Release Please or Changesets. The DAIS toolkit is for the narrower final-publication boundary where you want the release intent, source commit, trusted execution context, draft identity, public tag, and retained evidence to agree exactly.

1. Get the product's normal tests and review green first.
2. Choose the exact 40-character Git commit that is the product source you intend to publish.
3. Create a governed-release JSON manifest using the example in `docs/GOVERNED-RELEASE-TOOLKIT.md`.
4. Include the public files a reviewer must see: at minimum the relevant README/documentation, license, security/contribution paths and release notes.
5. Run the composite action with `publish: 'false'` in a read-only job. A successful result must remain `READY_FOR_TRUSTED_PUSH`; it creates no draft, release or tag.
6. Review the manifest, notes and plan evidence.
7. In a separate job that runs only on a trusted `push` ref, grant `contents: write` and set `publish: 'true'`.
8. Preserve the sanitized evidence file and independently verify the public release/tag after publication.
9. Run your project's own completion/release audit. **Publication is not product completion.**

## What you need

- GitHub Actions;
- Git and GitHub CLI (`gh`) on the runner for the write-capable path;
- Python 3;
- a reviewed repository-relative release manifest and notes file;
- `contents: read` for planning;
- `contents: write` only for the trusted publication job.

No persistent release credential is required by the action itself when it is used inside GitHub Actions; the workflow supplies the job-scoped GitHub token. Do not copy that token into manifests, logs, issues or retained evidence.

## Minimal plan-only workflow step

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@<PINNED_COMMIT>
    with:
      fetch-depth: 0
      persist-credentials: false
  - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/governed-release@<PINNED_RELEASE_OR_COMMIT>
    with:
      manifest: release/my-project-v1.2.3.json
      publish: 'false'
      evidence-file: governed-release-plan.json
```

Do not use a mutable branch reference for a write-capable third-party action. Pin the released toolkit version or an exact commit according to your supply-chain policy.

## What happens when publication is enabled

The publisher fails closed unless it is running inside GitHub Actions on the exact configured `push` ref with a valid repository identity and a job token. It then requires the reviewed source commit to exist in retained history and be an ancestor of the release-control checkout.

The lifecycle is:

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

Existing tags/releases are not moved or overwritten to make a run pass.

## If something fails

- **Before draft creation:** no release should have been created. Correct the reviewed source/configuration and make a new reviewed attempt.
- **After draft creation but before publication:** leave the draft unpublished. Inspect its tag, title, target commit and retained evidence. Delete it only after an operator has established what happened.
- **After publication but before exact-tag verification:** treat this as a release incident. Do not move the tag automatically. Compare the public release, remote tag and intended source and preserve the discrepancy as evidence.
- **Tag/release already exists:** the toolkit refuses the operation. Choose a new reviewed version; do not overwrite published identity.

Full recovery semantics are in `docs/GOVERNED-RELEASE-TOOLKIT.md` and `docs/RELEASE-GOVERNANCE.md`.

## Privacy and security checklist

- Use `pull_request`, never `pull_request_target`, for untrusted contribution validation.
- Keep PR jobs `contents: read`.
- Give `contents: write` only to the trusted publish job.
- Never place credentials or private URLs in the manifest or issue reports.
- Treat release notes, manifest fields and repository content from forks as untrusted until reviewed.
- Keep `persist-credentials: false` on checkout unless a separate reviewed operation specifically requires Git credentials.
- Never infer product correctness or roadmap completion from a successful release operation.

## Accessibility and language

The toolkit is text-first and keyboard-operable through the GitHub/CLI surfaces. Its evidence is plain JSON and its errors are intended to state the refusal condition directly. The safety contract is language-neutral; this guide is currently English-first. That is a multilingual path, not a claim of translated-user acceptance or WCAG conformance.

## Need help or found a bug?

Use the **Governed Release Toolkit** issue form in `.github/ISSUE_TEMPLATE/governed-release-toolkit.yml`. Submit sanitized reproduction details only. Never paste tokens, private repository contents, internal hostnames, private URLs or other secrets.
