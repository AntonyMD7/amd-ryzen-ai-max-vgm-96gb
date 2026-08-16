# DAIS Dangerous-Script Detector v0.12.0

Roadmap ID: **P-058 — Dangerous-Script Detector**

## Release purpose

`v0.12.0` is the first governed release candidate for the bounded P-058 Dangerous-Script Detector. It is intentionally a narrow, non-executing risk-policy and evidence layer for obvious high-risk script constructs. It does not replace general-purpose static analysis, malware analysis, ShellCheck, CodeQL, Semgrep, or human security review.

## Product capabilities

- Scans only a bounded set of shell, PowerShell, batch and GitHub Actions workflow/action YAML files.
- Uses fixed CRITICAL, HIGH and MEDIUM rule families for remote-pipe execution, encoded/dynamic execution, destructive filesystem/storage/Git operations, privilege/service/registry/firewall/package mutation, forced termination and persistence-like constructs.
- Performs no subprocess execution, network request, repository-code execution or repository mutation.
- Fails closed on traversal, symlinks, non-regular files, invalid UTF-8 and configured file/count/aggregate-size limits.
- Emits deterministic privacy-minimized JSON evidence containing rule/severity/category/language/line number plus path and line fingerprints, never source text, matched text or absolute paths.
- Exposes stable composite-Action outputs. HIGH/CRITICAL findings fail the Action; MEDIUM findings remain explicit `REVIEW_REQUIRED` evidence rather than being silently accepted.
- Retains sanitized fail-closed error evidence for invalid or unsafe inputs without leaking source content.
- Includes adversarial tests and hosted clean/critical/medium/containment acceptance with consumer-input immutability checks.
- Provides beginner and engineering documentation plus a privacy-safe support path.

## Search-before-build boundary

P-058 deliberately does not create another full static-analysis engine. ShellCheck remains the specialist shell analyzer; GitHub CodeQL remains a mature GitHub/application-code analysis ecosystem; Semgrep remains a broad pattern-based SAST ecosystem. DAIS adds only a small portable policy/evidence layer for a deliberately obvious high-risk subset where deterministic fail-honest behavior and privacy-minimized evidence are useful.

## Security and privacy boundary

No repository script is executed. No shell command, PowerShell command, package manager, network client, Git mutation, service operation, registry operation, device action or arbitrary analyzer argument is available to the product. Reports do not retain raw source lines, matched source text, absolute paths, credentials or private infrastructure identifiers.

## Truth boundary

`PASS` means only that the exact bounded v0.12.0 rule set found no matching construct in the exact scanned inputs. It does **not** prove a script safe, establish developer intent, detect every malicious/destructive behavior, perform AST/data-flow analysis, or establish repository security. `REVIEW_REQUIRED` and failure findings are signals requiring contextual review, not automatic proof of malicious intent.

## Verified candidate evidence

The productization source merged to public main at `f2379f01980d7edea51be86b7d43292b341685f9`. Fresh exact-main hosted acceptance run `31947619776` completed successfully and retained sanitized evidence artifact `9263736975` with digest `sha256:7e216e0c74a04c9b521684a72d2a063b2dc1c580055e11489bcd309fc3c4f1d4`.

## Exact-source release requirement

This notes file is merged before publication. The governed release manifest must subsequently bind `v0.12.0` to the exact canonical-main commit that contains the reviewed product implementation, tests, documentation and these release notes. The public tag must resolve exactly to that retained commit.

## Completion boundary

Publishing `v0.12.0` alone does not complete P-058. The released `@v0.12.0` Action must independently pass real-public consumer acceptance with deterministic privacy-minimized evidence and zero consumer mutation. A 19-gate completion record, final handover, fresh post-merge completion verification and canonical private DAIS synchronization remain separate mandatory gates before P-058 may be promoted to COMPLETE.
