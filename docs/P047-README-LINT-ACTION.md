# P-047 README Lint Action — Engineering and Security Guide

Status: **release candidate / IN PROGRESS until governed v0.4.0 release and completion audit**

Roadmap: `P-047 — README Linting Action`

## Product decision

DAIS does not implement another Markdown parser or rule engine. The product is a safety-oriented integration boundary around `DavidAnson/markdownlint-cli2-action`, whose current reviewed release is `v24.2.0` and whose annotated tag resolves to signed commit `21c1be1b93ad9ed58fa840aacc3f279cde2a72ff`. That release bundles `markdownlint-cli2 v0.23.2` and `markdownlint v0.41.1` according to upstream release metadata reviewed on 2026-08-16.

The public-good gap is safer adoption for beginners and maintainers: immutable upstream identity, least-privilege examples, a non-mutating default, bounded inputs, a fixed no-plugin profile, explicit outputs, fail-honest negative controls, and clear claim boundaries.

## Architecture

```text
relative root input
      |
      v
DAIS preflight.py
  - containment
  - symlink refusal
  - README count/size bounds
  - exclusions
      |
      v
fixed DAIS markdownlint-cli2 config
  - no custom rules/plugins
  - no auto-fix
      |
      v
pinned upstream markdownlint-cli2-action
      |
      +--> PASS/FAIL
      +--> readme-count
      +--> human step summary
```

The action requires no `GITHUB_TOKEN` write permission. The documented workflow baseline is `contents: read` only.

## Threat and privacy review

### Repository-code execution

`markdownlint-cli2` can support custom rules, Markdown-it plugins, and custom output formatters. Accepting arbitrary repository-controlled configuration would therefore expand the trust boundary from Markdown parsing into module execution. v0.4.0 intentionally ships one fixed configuration and exposes no custom-config input.

### Path escape and symlinks

The root must be a relative POSIX-style path under the current checkout. Parent traversal, absolute paths, glob metacharacters, root symlinks, README symlinks, missing roots, and empty scopes are refused before the upstream Action executes.

### Resource exhaustion

Preflight caps one README at 2,000,000 bytes, the combined selected README set at 10,000,000 bytes, and the selected README count at 250. These are product bounds, not claims that Markdown parsing is otherwise resource-safe under every adversarial environment.

### Mutation

Upstream `fix` is hard-coded to `false`. P-047 never promises auto-remediation. A failing README remains byte-for-byte user-controlled source.

### Sensitive content

Linting necessarily reads selected README text and upstream lint diagnostics can include line context depending on rule behavior. Public CI must therefore operate only on documentation appropriate for that CI visibility. P-047 does not redact sensitive README content and must not be used as a data-loss-prevention boundary.

## Fixed profile

The bundled `.markdownlint-cli2.yaml` keeps the standard rule set with four compatibility adjustments:

- `MD013` line length is disabled because prose, links, badges, and generated command lines often exceed arbitrary terminal widths;
- `MD024` allows duplicate headings only when they are not siblings, which supports repeated subsection names in distinct sections without losing local structure;
- `MD033` permits inline HTML because README badges/details blocks and accessible semantic snippets commonly use it;
- `MD041` permits content such as badges before the first heading.

These choices are an explicit product profile, not a claim that they are universally best Markdown style.

## Adversarial acceptance

The dedicated CI lane must prove all of the following on GitHub-hosted Ubuntu:

1. a valid generated README passes;
2. an invalid generated README fails;
3. a root with no README fails;
4. parent traversal is refused;
5. README input bytes are unchanged after a successful run;
6. outputs identify PASS, README count, and the exact upstream commit;
7. the workflow runs with `contents: read` only;
8. unit tests cover path containment, exclusions, size/count bounds, symlink refusal, immutable upstream pinning, no auto-fix, and no custom plugin surface.

Before completion, the released tag must also be consumed against at least two separate real public-repository checkouts without mutating them.

## Recovery and rollback

P-047 does not mutate README files. Recovery from a failed or interrupted run is therefore: preserve the source, discard incomplete CI evidence, correct configuration/source only through a reviewed commit if needed, and rerun. Rolling back the Action itself means reverting the workflow reference to a previously verified immutable release/tag or removing the P-047 workflow.

## Accessibility and multilingual review

The interaction surface is non-graphical text plus stable machine outputs. CI errors, PASS/FAIL, README counts, and rule identifiers do not rely on color or pointer interaction. This is an applicability review for a developer Action, not WCAG conformance or assistive-technology user acceptance. Stable rule/output identifiers allow localized explanatory layers; v0.4.0 human documentation is English-first.

## Interoperability and non-goals

P-047 complements rather than replaces:

- `P-044 Documentation Quality Assistant` for substantive documentation quality;
- `P-045 Repository Accessibility Reviewer` for accessibility review;
- `P-048 Broken-Link Scanner Action` for live link checks;
- `P-049 Secret-Exposure Detection Action` for specialist secret scanning.

A P-047 PASS is never promoted to documentation correctness, accessibility conformance, link health, security hygiene, or repository quality as a whole.

## Completion gates still open before v0.4.0 promotion

- governed exact-source public release/tag;
- released-ref consumption against representative public repositories;
- retained release and consumer evidence;
- final 19-gate completion record and independent audit;
- canonical portfolio/handover synchronization.
