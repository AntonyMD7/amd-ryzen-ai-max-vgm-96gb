# P-053 — Issue Template Generator v0.8.0

Status: **IN PROGRESS product candidate**

## Problem

Open-source maintainers need actionable issue reports, while contributors—especially beginners—should not have to understand GitHub Issue Form YAML or remember every privacy warning. Hand-authored templates are easy to make inconsistent, over-collect data, or bind to repository-specific labels/projects that do not exist elsewhere.

## Search-before-build / upstream boundary

GitHub remains the authority for Issue Forms and their schema. GitHub documents Issue Forms as a public-preview feature, stores form YAML under `.github/ISSUE_TEMPLATE`, requires top-level `name`, `description`, and `body`, and supports form elements such as markdown, inputs, textareas, dropdowns and checkboxes. GitHub also documents `config.yml` as the template-chooser configuration and `blank_issues_enabled: false` as a way to encourage contributors to use templates.

P-053 therefore does **not** invent another issue tracker or generic YAML form language. It generates a deliberately small GitHub-compatible subset and keeps `github_schema_officially_validated=false` until GitHub itself has rendered/accepted a deployed default-branch template.

## Architecture

```text
bounded JSON support spec
        |
        v
strict key/type/text validation
        |
        +--> secret-like spec refusal
        |
        v
fixed preset renderer
        |
        +--> dais-support.yml
        +--> config.yml
        |
        v
deterministic bundle SHA-256
```

There is no network client, GitHub API client, label/project lookup, assignee lookup, issue creation, repository commit or permission mutation.

The reusable GitHub Action writes generated files only into `$RUNNER_TEMP`; the caller must separately decide whether and how to commit them.

## Deliberate schema subset

P-053 v0.8.0 accepts only:

- `name`
- `description`
- `kind`: `bug`, `feature`, or `support`
- `title_prefix`
- `project_context`
- `include_environment`

Unknown keys fail closed. The product deliberately does not accept arbitrary YAML fragments, labels, assignees, organization issue types, projects or external contact links. This avoids silently creating dependencies on repository/org objects that may not exist or that require extra permissions.

## YAML-injection resistance

Human strings are rendered as JSON double-quoted strings, which are valid YAML scalars. Newline/control-character bounds and a strict fixed structure prevent callers from injecting new YAML keys through values.

## Privacy model

Generated forms start with a privacy warning and end with required confirmations that the reporter removed credentials, private repository content, personal/medical data, private network details and other sensitive information. Environment guidance asks for OS/runtime/tool versions only and explicitly excludes identities and infrastructure identifiers.

P-053 also refuses several high-signal credential/private-key/password-like patterns in the generation spec without echoing the value. This is defense in depth, not comprehensive secret detection. P-049 remains the dedicated secret-exposure detector.

## Accessibility and beginner usability

The generated experience uses GitHub's native form controls rather than a custom frontend. Labels and descriptions are plain-language; no meaning depends on color, pointer interaction, animation or a custom visual layer. This supports accessibility by composition but does not establish WCAG conformance for GitHub itself or the final repository experience.

Generated prose is currently English. The small canonical JSON input and fixed semantic field IDs are designed for future localized renderers; multilingual human acceptance remains unclaimed.

## Determinism and evidence

The bundle digest is SHA-256 over exact generated filenames and contents in fixed order. The generator reports claims explicitly as false for official GitHub-schema validation, guaranteed issue quality, guaranteed privacy and repository mutation.

## Recovery

CLI output is limited to two fixed filenames in an explicit output directory. Existing symlink/non-file output targets fail closed. The Action writes only to a fresh runner-temporary directory. No Git repository mutation occurs; rollback is deletion of the generated files or reverting a later separately-authorized commit.

## Known limitations

- GitHub Issue Forms remain public preview and their schema may change.
- v0.8.0 generates one form plus chooser config, not arbitrary multi-form suites.
- labels, assignees, projects, organization issue types and contact links are intentionally unsupported.
- no official GitHub form-render validation API is claimed or emulated.
- disabling blank contributor issues does not remove the maintainer-only blank option documented by GitHub.
- privacy prompts do not guarantee reporter behavior.
- no automatic repository commit, issue creation or repository-settings mutation.
- no WCAG-conformance or multilingual-user-acceptance claim.

## Completion gates still open

Source tests/CI, governed release, released-ref use against a real public repository context, retained evidence, final completion record/handover, fresh post-merge verification and canonical DAIS synchronization are required before P-053 may be `COMPLETE`.
