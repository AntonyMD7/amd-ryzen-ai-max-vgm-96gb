# P-049 Secret Exposure Detection Action v0.6.0

Status: **IN PROGRESS — release candidate**

Roadmap ID: **P-049 — Secret-Exposure Detection Action**

## Product promise

Provide a beginner-safe, CI-native secret-exposure signal without turning public CI logs or artifacts into a second secret leak.

The product is a narrow security/evidence boundary around the established **Gitleaks** engine. DAIS does not implement another secret-detection rules engine.

## Search-before-build decision

Fresh review on 2026-08-16 confirmed that Gitleaks already provides mature secret-rule detection and working-tree directory scanning. The DAIS value is therefore policy, privacy, reproducibility and fail-closed integration.

The current upstream latest release is `v8.30.1` (published 2026-03-21). P-049 deliberately pins the official `v8.30.0` Linux x64 release asset instead. Upstream issue `gitleaks/gitleaks#2086` remains open and records that the `v8.30.1` tag points to a commit not reachable from `master`, breaking normal reachable-tag tooling. The v8.30.0 Linux x64 asset is independently bound here by GitHub-published SHA-256:

`79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e`

This is not a claim that v8.30.0 is bug-free. Every run additionally performs a live positive detector canary and a clean negative canary before repository content is scanned.

## Recursive red-team finding before first PR

The first canary design used a sequential placeholder GitHub-PAT-shaped value. During upstream issue review, the implementation discovered that this exact placeholder lowercases to a string containing `abcdefghijklmnopqrstuvwxyz`, which Gitleaks intentionally includes in its global allowlist stopwords. Upstream maintainers demonstrated that such a placeholder is correctly ignored and that a non-sequential token-shaped value triggers the `github-pat` rule.

The candidate was corrected before relying on CI: its canary is now a non-sequential synthetic value assembled only at runtime. This is precisely why the product requires an actual detector canary rather than assuming that process exit 0 means the engine is healthy.

## Architecture

```text
repository working tree
        |
        v
bounded preflight
  - root containment
  - no symlinks
  - <= 5000 files
  - <= 10 MiB/file
  - <= 100 MiB total
  - .git excluded
        |
        v
private temporary staging copy
        |
        v
Gitleaks 8.30.0 `dir`
  - action-owned config
  - built-in default rules
  - action-owned empty ignore file
  - inline gitleaks:allow disabled
  - archive/decode recursion disabled
  - 10 MiB target limit
  - 100% redaction
        |
        v
raw JSON + stdout/stderr in RUNNER_TEMP
        |
        v
privacy sanitizer
        |
        +--> delete raw report/logs/staging
        |
        v
sanitized result
  - status/counts
  - rule IDs
  - metadata-only SHA-256 fingerprints
  - scope hash/counts
  - explicit non-claims
```

## Why working-tree-only in v0.6.0

P-049 uses `gitleaks dir`, not Git-history scanning.

This provides a bounded beginner-safe first product:

- no history traversal;
- no commit author/email/message collection;
- no dependency on repository Git plumbing correctness;
- no exposure of historical secret values in public evidence;
- predictable resource limits.

A PASS therefore never means Git history is clean. History scanning belongs in a separately threat-modeled mode or product revision with protected evidence handling.

## Threat model

### Asset: secret-like source material

A scanner can discover precisely the information it is meant to protect. Raw findings, stdout, stderr, file paths and matched lines are therefore treated as sensitive.

Controls:

- `--redact=100`;
- raw report/stdout/stderr never printed;
- raw files remain in `RUNNER_TEMP` only and are deleted after sanitization;
- sanitized public result excludes `Secret`, `Match`, file paths, author/email and commit information;
- public support form forbids secret values and private findings.

### Asset: integrity of the gate

A contributor could attempt to suppress detections through repository-controlled config, ignore files or inline comments.

Controls:

- action-owned `gitleaks.toml` explicitly extends Gitleaks built-in defaults;
- action-owned empty `.gitleaksignore` is passed explicitly;
- `--ignore-gitleaks-allow` disables inline suppression;
- no caller-supplied scanner arguments/config/token inputs exist;
- positive and clean runtime canaries are mandatory.

### Asset: private runner infrastructure

Repository-controlled files should not cause a security scanner on a private runner to read unexpected mounts or become an oracle for internal state.

Controls:

- `runner.environment` must be `github-hosted`;
- supported runtime is Linux x64 only;
- selected root must remain under `GITHUB_WORKSPACE`;
- all symlinks in scope are refused;
- repository code is never executed.

### Asset: supply-chain integrity

Controls:

- one exact official Gitleaks release URL;
- exact GitHub-published Linux x64 SHA-256;
- HTTPS-only curl with failure and retry handling;
- tar member traversal screening;
- exactly one `gitleaks` executable extracted;
- observed runtime version must equal `8.30.0`;
- mandatory live detection canary.

## Fork/PR execution model

The acceptance/recommended workflow uses the normal `pull_request` event with `contents: read` only. It does not use `pull_request_target`, does not receive repository secrets, and does not execute repository code.

That boundary matters: a secret-scanning workflow should not become a mechanism by which untrusted pull-request content receives stronger credentials or private runner access.

## Machine outputs

The composite Action exposes:

- `status`;
- `finding-count`;
- `rule-count`;
- `file-count`;
- `result-file`;
- `result-sha256`;
- `gitleaks-version`.

The result file is safe to retain publicly under the defined schema because it excludes secret values, matched text and source paths. It intentionally preserves rule IDs because those describe detector classes, not the discovered credential itself.

## Truth boundary

`PASS` means only:

> The pinned Gitleaks engine, after passing its mandatory runtime canaries, produced no findings under the fixed P-049 policy for the bounded staged working-tree scope in that run.

It does **not** mean:

- all secrets are absent;
- Git history is clean;
- a detected value is currently valid;
- a removed credential has been revoked;
- dependencies, Actions variables, external systems or CI settings are secret-free;
- the repository is secure;
- P-046 Security Hygiene Reviewer is complete;
- any flagship foundation is complete.

False positives and false negatives remain possible. A finding is an incident signal requiring context, not automatic proof of compromise.

## Accessibility and multilingual path

The beginner surface uses plain-language PASS/FAIL semantics and avoids requiring users to interpret raw scanner output. Machine outputs allow accessible downstream rendering without parsing ANSI output. Documentation is English-first in v0.6.0; the schema and status vocabulary are language-neutral so translated user interfaces can map the same evidence later. This is not a WCAG or multilingual-acceptance claim.

## Recovery and rollback

The Action is non-mutating with respect to repository source. Its only writes are disposable copies and reports under `RUNNER_TEMP` plus the caller-selected evidence copy made by the workflow.

Rollback is therefore removal of the workflow/Action reference. A failed scan leaves repository files unchanged. Credential incident recovery is a separate operational responsibility: rotate/revoke first, then remove exposed material and address history as required.

## Test and acceptance strategy

Pure adversarial tests cover:

- working-tree-only staging;
- `.git` exclusion;
- traversal refusal;
- symlink refusal;
- empty-scope refusal;
- secret/match/path/identity stripping;
- inconsistent scanner exit/report refusal;
- exact engine artifact/version policy;
- no repository config/ignore/inline bypass;
- fixed archive/decode/size bounds;
- no raw diagnostics printing;
- mandatory runtime canaries;
- no token/arbitrary argument input.

Hosted acceptance additionally requires:

- the exact Gitleaks binary download and SHA-256 check;
- live positive and clean canaries;
- a clean working-tree PASS with byte-for-byte input immutability;
- a runtime secret-like fixture to fail;
- that fixture to remain detectable despite a repository `.gitleaks.toml` and inline `gitleaks:allow` bypass attempt;
- symlink and parent-traversal refusal;
- only sanitized retained evidence.

## Completion gates still open

This tranche deliberately does not mark P-049 COMPLETE. After the exact source passes current-head CI and merges, completion still requires:

1. governed exact-source `v0.6.0` publication;
2. independent public tag/source verification;
3. released-ref execution against representative real public repositories;
4. retained sanitized release/consumer evidence;
5. final 19-gate P-049 completion record and handover;
6. fresh post-release completion audit;
7. canonical DAIS portfolio synchronization.
