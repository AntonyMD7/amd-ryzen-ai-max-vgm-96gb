# P-047 README Lint Action — Start Here

`P-047` is a small, safe GitHub Action that checks `README.md` files with the established `markdownlint-cli2-action` ecosystem instead of inventing another Markdown parser.

## What it does

- finds bounded `README.md` files below one relative workspace directory;
- refuses parent traversal, root symlinks, README symlinks, excessive file counts, and oversized inputs;
- runs upstream `DavidAnson/markdownlint-cli2-action` at immutable commit `21c1be1b93ad9ed58fa840aacc3f279cde2a72ff` (release `v24.2.0`);
- uses a fixed DAIS README profile with no repository-supplied custom rules or plugins;
- disables auto-fix, so the Action never edits your README;
- gives a text summary and machine-readable `status`, `readme-count`, and `upstream-commit` outputs.

## Minimal use

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
  - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/readme-lint@v0.4.0
```

To lint a subdirectory only:

```yaml
  - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/readme-lint@v0.4.0
    with:
      root: docs/example-project
```

## How to interpret the result

`PASS` means the selected README files satisfy the fixed Markdown style/structure profile in this release. It does **not** prove that documentation is correct, complete, accessible to every user, secure, current, or free of broken links.

A failure is intentionally non-mutating. Review the reported markdownlint rule, edit the README yourself, and rerun CI. If the Action is interrupted or the result is missing, discard that run and rerun it against unchanged source.

## Safety and privacy

The Action reads README text because linting requires it. Do not put secrets, credentials, personal records, PHI, private infrastructure details, or other sensitive material in a public README. The Action does not upload a separate README-content artifact and does not enable markdownlint auto-fix.

The fixed profile deliberately disallows repository-controlled `customRules`, Markdown-it plugins, and output formatter modules in this v0.4.0 scope. That avoids turning a documentation linter into an implicit repository-code execution surface.

## Accessibility and language

The interface is text-first and keyboard/CI friendly, with explicit PASS/FAIL states and machine outputs. Rule identifiers are stable technical identifiers that can be explained in localized documentation. Human documentation in v0.4.0 is English-first; this is not a WCAG-conformance or multilingual-user-acceptance claim.

## Support

Use the dedicated **P-047 README Lint** issue form. Share a minimal public reproduction and rule identifier, not sensitive README content.
