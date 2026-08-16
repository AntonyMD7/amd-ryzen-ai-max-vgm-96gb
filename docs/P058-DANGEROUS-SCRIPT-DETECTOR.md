# P-058 Dangerous-Script Detector — Engineering and Threat Model

## Problem

Repositories routinely contain shell, PowerShell, batch, and CI scripts. Reviewers need a fast, reproducible signal for obviously dangerous execution/mutation patterns without granting a scanner authority to execute the repository.

P-058 is a **bounded lexical risk detector**, not a malware classifier, sandbox, SAST replacement, or proof of safety.

## Search-before-build decision

P-058 deliberately composes with established analysis ecosystems instead of pretending one heuristic engine can replace them:

- **ShellCheck** remains the specialist static-analysis tool for shell correctness and includes security-relevant diagnostics such as unsafe filename injection.
- **GitHub CodeQL** supports GitHub Actions plus major application languages, but its published supported-language list does not make POSIX shell a general CodeQL language.
- **Semgrep** provides broad SAST capabilities and Bash scanning support, but P-058 does not require a cloud account or arbitrary external rules.

The DAIS contribution is a transparent, dependency-light policy boundary for a narrow set of high-risk constructs, with deterministic privacy-minimized evidence and no execution authority.

## Architecture

```text
contained repository root
        ↓
supported-file discovery
        ↓
size / symlink / UTF-8 guards
        ↓
line-oriented fixed rule set
        ↓
severity + rule/category classification
        ↓
privacy-minimized deterministic JSON
        ↓
HIGH/CRITICAL fail gate
```

No network client, subprocess, shell executor, package installer, repository mutation, GitHub API token, or arbitrary rule/config input exists in the detector.

## Current rule families

CRITICAL:
- remote content piped directly into a shell;
- download + PowerShell expression execution;
- encoded PowerShell execution.

HIGH:
- root-targeted recursive forced deletion;
- storage formatting/initialization and raw block-device writes;
- dynamic expression execution;
- privileged mutation;
- service/registry/firewall mutation;
- world-writable permissions;
- PowerShell execution-policy bypass.

MEDIUM:
- destructive Git operations;
- package mutation;
- forced process termination;
- recursive forced deletion away from root;
- scheduled persistence.

Rules are intentionally review-biased. Legitimate administrative scripts may match. Findings are **risk evidence**, not intent classification.

## Security boundaries

### Repository-controlled input

Repository input is untrusted. P-058 therefore:

- accepts one relative root only;
- rejects traversal, absolute roots, NULs, and symlinked root components;
- rejects symlinked supported candidates;
- does not follow `.git`, `.venv`, `node_modules`, or symlinked directories;
- caps 5,000 candidate files;
- caps each candidate at 1 MiB and aggregate bytes at 50 MiB;
- requires UTF-8 text and rejects NUL/binary candidates;
- has no repository-supplied regex/rules configuration.

GitHub workflow identity is evaluated relative to the repository workspace, not relative only to the caller-selected scan root. This matters when a consumer intentionally narrows `root` to `.github/workflows`: workflow YAML must remain workflow YAML rather than silently disappearing from the scan. A dedicated regression test preserves this boundary.

### No execution

The detector uses Python standard-library file/regex/hash operations only. It does not import subprocess/socket/urllib/requests and does not call `os.system`.

The composite Action uses Bash only to launch the Action-owned detector and process its already-sanitized result; repository files are never sourced or executed.

### Evidence privacy

A finding retains:

- rule ID;
- severity/category/language;
- one-based line number;
- SHA-256 of the relative path;
- SHA-256 of the full source line;
- fixed rule rationale.

It does not retain the path itself or line/match text. This reduces leakage if evidence is uploaded from a private repository.

## Recursive red-team finding and permanent fix

Post-productization review found a real classification defect: YAML recognition was originally computed relative to the selected scan root. A consumer scanning the repository root worked correctly, but a consumer narrowing the scan root to `.github/workflows` caused those same workflow files to lose their `.github/workflows/` identity and therefore be skipped. That is a dangerous false-negative shape because a valid containment feature could reduce security coverage.

The permanent fix classifies GitHub workflow/action YAML against the resolved repository workspace while retaining the selected scan root only for containment and privacy-relative result hashing. The new regression test scans the same critical workflow through a `.github/workflows` subroot and requires the same `DS001` detection. No rule severity or fail gate was weakened to make the test pass.

## Accessibility and multilingual path

The product is non-graphical and exposes stable textual/machine-readable outcomes that do not depend on color or pointer interaction. The beginner documentation uses plain-language status meanings. Stable rule IDs and JSON keys are language-neutral integration surfaces.

Current human documentation is English-first. Multilingual human acceptance and WCAG conformance are **not claimed**.

## Recovery

P-058 does not mutate scanned content. Recovery is therefore discard-and-rerun:

1. discard incomplete runner-temporary evidence after interruption;
2. verify the repository input is unchanged;
3. rerun the same reviewed product version.

Consumers can roll back by pinning a prior reviewed release/ref or removing the Action invocation.

## Known limitations

P-058 does not:

- parse full shell/PowerShell AST semantics;
- follow data flow or resolve variable indirection;
- deobfuscate arbitrary payloads;
- inspect compiled binaries;
- detect every persistence/exfiltration/destruction method;
- prove a finding is malicious;
- prove a clean script is safe;
- replace ShellCheck, CodeQL, Semgrep, malware analysis, sandboxing, or human review.

A future release may add carefully pinned specialist analyzers, but only if their execution and evidence/privacy boundaries are independently reviewed.

## Completion boundary

This tranche productizes P-058 but does **not** mark it COMPLETE. Completion still requires a governed exact-source release, released-ref real-public acceptance, retained evidence, final 19-gate completion record/handover, fresh post-merge verification, and canonical DAIS synchronization.
