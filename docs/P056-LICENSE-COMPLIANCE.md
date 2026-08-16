# P-056 — DAIS License Compliance Checker v0.11.0

Status: **IN PROGRESS product candidate**  
Roadmap ID: **P-056 License Compliance Checker**

## Product promise

Give maintainers a reproducible, read-only answer to one narrow technical question:

> Does the pinned upstream REUSE tool report this exact repository snapshot compliant with the REUSE Specification?

The product deliberately does **not** answer the different legal question “may I distribute this project?” and it does not invent a competing license parser.

## Search-before-build decision

P-056 adopts established authority instead of duplicating it:

- **REUSE Specification 3.3** defines practical machine-readable per-file copyright/licensing requirements.
- **REUSE tool 6.2.0** is the upstream reference linter used by this product. P-056 runs its documented `reuse lint --json` interface.
- **SPDX identifiers/expressions** remain the license-expression vocabulary used by REUSE.
- GitHub repository license recognition is a useful coarse signal but is not substituted for per-file REUSE evidence.

The official `fsfe/reuse-action` v6.0.0 source is available at immutable Git commit `676e2d560c9a403aa252096d99fcab3e1132b0f5`, but that action's Dockerfile uses the moving image reference `fsfe/reuse:6`. P-056 therefore does not describe that path as a fully immutable runtime. The DAIS Action instead creates an ephemeral Python environment, installs **exact `reuse==6.2.0`**, verifies the observed tool version, records the sorted resolved `pip freeze --all` SHA-256, then destroys nothing outside runner-temporary state. This improves provenance while explicitly **not claiming a fully hash-locked transitive dependency closure**.

## Architecture

```text
consumer checkout (read-only)
        |
        v
runner-temp Python venv
  exact reuse==6.2.0
  + resolved environment digest
        |
        v
fixed command only:
  reuse lint --json
        |
        +--> raw upstream JSON (runner-temp only; may contain relative paths)
        |
        v
P-056 evidence boundary
  - validate tool/spec/schema
  - preserve compliant/noncompliant truth
  - count categories
  - hash used-license set
  - remove file paths / identities / recommendations
        |
        +--> deterministic sanitized JSON
        +--> EN or ES guide sharing same technical state
```

## Security and privacy model

The wrapper accepts no arbitrary REUSE arguments and executes with `shell=False`. The composite Action supplies the REUSE binary from its own ephemeral environment; there is no token input, GitHub API client, uploader, package/license mutator, or repository-code execution path.

Repository root and output locations are fail-closed:

- existing directory required;
- symlink root refused;
- output must resolve outside the audited repository;
- fixed output filenames refuse symlinks;
- REUSE executable must be a concrete executable named `reuse`/`reuse.exe`;
- command runtime and raw-report size are bounded.

The sanitized evidence intentionally omits upstream file paths, copyright identities, recommendations and literal license IDs. It retains counts and cryptographic digests. The **raw REUSE JSON is kept separately in runner-temporary storage** because it is useful for remediation but may disclose repository-relative filenames or copyright information. Workflows must not publish that raw file blindly, especially for private repositories.

## Truth model

`REUSE_COMPLIANT` means only:

1. the exact observed REUSE executable identified itself as 6.2.0;
2. its JSON identified REUSE Specification 3.3;
3. the JSON contract was structurally accepted by P-056; and
4. upstream `summary.compliant` was `true` for that run/snapshot.

`REUSE_NONCOMPLIANT` is a valid successful audit result, not a tool failure.

The following always remain separate and are never inferred by this product:

- legal advice or redistribution permission;
- compatibility between multiple licenses or organizational policy;
- dependency-license safety;
- completeness of third-party notices;
- repository security;
- approval for production/distribution.

## Failure model

The checker fails closed on:

- wrong REUSE tool version;
- unexpected REUSE Specification version;
- malformed/non-object JSON;
- missing or wrongly typed required fields;
- malformed source revision or dependency-environment digest;
- unsafe root/output/executable paths;
- command timeout;
- oversized raw upstream report.

It never converts an inability to audit into `REUSE_COMPLIANT`.

## Action usage

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
    with:
      persist-credentials: false
  - id: license
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/license-compliance@<reviewed-ref>
    with:
      root: .
      language: en
```

Important outputs include `status`, `compliant`, exact REUSE/spec versions, the resolved dependency-environment SHA-256, sanitized report SHA-256/path, guide path and raw report path. Treat `raw-report-path` as local diagnostic material, not a default artifact.

## Accessibility and localization

P-056 produces a text-first Markdown guide in **English or Spanish**. Both language paths consume the same deterministic technical JSON; localization cannot change compliance state. No WCAG conformance or multilingual human acceptance is claimed by this source tranche.

## Recovery / rollback

The product is read-only against the audited repository. Recovery from a failed run is simply to discard runner-temporary output/venv, correct the input/tool problem, and rerun. License metadata fixes must happen separately on a reviewed branch; P-056 never writes them.

## Tests and acceptance

The product test suite covers compliant and noncompliant upstream results, privacy minimization, version/spec mismatch, malformed schema/JSON, path/symlink controls, invalid evidence identities, deterministic EN/ES truth, raw-vs-sanitized separation and repository immutability.

Hosted acceptance additionally exercises the **real pinned REUSE 6.2.0** on disposable fixtures and a pinned real public repository, verifying that classification does not mutate consumer input.

## Remaining completion gates

This tranche is productization, not completion. P-056 remains **IN PROGRESS** until an exact-source versioned release, released-ref public acceptance, retained release/acceptance evidence, independent 19-gate completion record, final handover, fresh post-merge verification and canonical DAIS synchronization all succeed. Full transitive package hash-locking is not silently claimed; its risk is recorded in release evidence and may be tightened if a stronger immutable upstream distribution path is adopted.
