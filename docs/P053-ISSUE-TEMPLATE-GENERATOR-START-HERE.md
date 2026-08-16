# P-053 — Issue Template Generator: START HERE

Status: **IN PROGRESS product candidate v0.8.0**

P-053 generates a small, privacy-conscious GitHub Issue Form bundle from a simple JSON description. It does **not** edit your repository, enable Issues, create issues, assign people, add projects, or claim that a generated form is automatically valid forever.

GitHub Issue Forms are currently documented by GitHub as a public-preview feature, so P-053 deliberately generates a narrow subset instead of exposing every evolving schema option.

## What it generates

- `dais-support.yml` — a GitHub Issue Form with actionable fields and mandatory privacy/scope confirmations.
- `config.yml` — disables contributor-facing blank issues and contains no external contact links by default.

Maintainers with write access can still see a maintainer-only blank issue option when GitHub's `blank_issues_enabled` is false; that behavior belongs to GitHub, not this generator.

## Local use

```bash
python scripts/issue_template_generator.py \
  examples/p053-issue-form-spec.json \
  --output /tmp/dais-issue-template
```

Review the generated files. If appropriate for your repository, copy them into:

```text
.github/ISSUE_TEMPLATE/
```

Templates become available through GitHub only when valid templates are present on the repository's default branch.

## GitHub Action use

```yaml
permissions:
  contents: read

steps:
  - id: generate
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/issue-template-generator@YOUR_REVIEWED_REF
    with:
      spec-json: >-
        {"name":"Bug report","description":"Report a reproducible public bug","kind":"bug","title_prefix":"[BUG]","project_context":"this public open-source project","include_environment":true}

  - run: |
      echo "Generated at: ${{ steps.generate.outputs.output-directory }}"
      echo "Bundle SHA-256: ${{ steps.generate.outputs.bundle-sha256 }}"
```

The Action writes only to runner-temporary storage. Choosing to commit the generated files is a separate human/governed repository change.

## Presets

- `bug` asks what happened, reproduction steps, expected and actual behavior.
- `feature` asks for the problem, desired outcome and existing alternatives.
- `support` asks what help is needed and what has already been tried.

An environment field can be included for bug/support forms. Its generated guidance explicitly asks users not to include usernames, hostnames, IP addresses, serial numbers, credentials or private paths.

## Privacy and safety

P-053 adds a required privacy confirmation telling reporters to remove credentials, private repository content, personal/medical data and private network details. The generator also refuses several obvious secret-like values in its own specification.

That is not a guarantee that future issue reporters will comply, and it is not a DLP system. Repositories should still maintain a `SECURITY.md` path for vulnerability reporting and review issue content according to their own governance.

## Recovery

The generator does not mutate the repository. Delete the generated temporary/output files if you do not want them. If you later commit a generated template and decide it is unsuitable, revert that repository commit through normal Git governance.

## Current completion boundary

v0.8.0 remains **IN PROGRESS** until source CI passes, a versioned release exists, the released ref is exercised against a real public repository input with retained evidence, known limitations and release handover are complete, the canonical 19-gate audit passes, and DAIS canonical status is synchronized.
