# P-049 Secret-Exposure Detection Action — Completion Record v0.6.0

**Roadmap ID:** P-049  
**Final product status:** COMPLETE candidate, contingent on this tranche's fresh completion CI and merge  
**Public release:** `v0.6.0`  
**Exact released source:** `f90538531fdeafd05d1f1d22c96d6db70c3d2d96`  
**Upstream engine:** Gitleaks `v8.30.0`  
**Official Linux x64 archive SHA-256:** `79a3ab579b53f71efd634f3aaf7e04a0fa0cf206b7ed434638d1547a2470a66e`

## Product

P-049 is a reusable GitHub composite Action for maintainers who need a deliberately bounded secret-exposure signal without granting repository content execution, Git-history scanning, arbitrary detector arguments, repository-controlled bypass policy, or public retention of secret material.

It adopts Gitleaks instead of reimplementing a detector. The reviewed release remains on v8.30.0 because the next upstream release had an unresolved tag-lineage concern during release review; detector upgrades are explicit product changes requiring renewed provenance, canary and privacy acceptance.

## Security and privacy boundary

The Action runs only on GitHub-hosted Linux x64. It stages only bounded regular files from the requested current-worktree scope, excludes `.git`, rejects traversal and symlinks, caps file/aggregate size, disables archive/decode recursion, uses Action-owned Gitleaks configuration and an empty Action-owned ignore file, disables inline `gitleaks:allow`, accepts no token or arbitrary argument input, and never executes repository code.

A mandatory runtime-generated secret-shaped positive canary proves the exact detector recognizes a GitHub-PAT-shaped fixture before target scanning; a clean canary proves clean-path behavior. Canary files and raw detector outputs are deleted. Public evidence retains only status/counts/rule IDs and non-secret hashes. Findings must be handled privately.

## Recursive correction retained

An early sequential placeholder canary was correctly suppressed by Gitleaks' stopword logic. That test weakness was not bypassed. The canary was permanently replaced with a non-sequential runtime-only token-shaped fixture, eliminating a false detector-health signal without committing a real credential.

## Governed release evidence

Release/acceptance run `31936719410` passed the release plan, exact-source publication, independent public-tag verification and released-ref consumer acceptance. The non-draft `v0.6.0` release was published on 2026-08-16 and resolves exactly to `f90538531fdeafd05d1f1d22c96d6db70c3d2d96`.

Retained artifacts:

- release plan `9260859716`, SHA-256 `9688749fb6d90646d6551ee86b5fbe9b8dcf772043f1fbcdcee97eac1680cc90`;
- publication `9260862610`, SHA-256 `6184b164812676de4dd4a12468d06156c00735f721c3b631d037ea27a549f631`;
- released-ref consumer `9260864255`, SHA-256 `38385e7dd189f3f59ab90abcad2c470a037483e9e015d35c0ec3d721b92c029c`.

The release-source notes retain their pre-publication wording because they are part of the immutable reviewed source snapshot. This completion record is the later canonical state record and does not rewrite release history.

## Real public acceptance

The released `@v0.6.0` Action was consumed from GitHub Actions against `AntonyMD7/learning-git` exact commit `01723a1825113de08810193f37e8047d978433c2` on Ubuntu 24.04. It downloaded exact released Action source `f90538531fdeafd05d1f1d22c96d6db70c3d2d96`, verified Gitleaks v8.30.0 and its archive digest, passed the live positive detector canary and clean canary, scanned 19 files / 54,156 bytes, returned PASS with zero findings, verified the consumer README byte-identical, and retained no secret values/raw findings/stdout/stderr.

## Accessibility and localization

The product is non-graphical and exposes explicit text plus stable machine outputs; operation does not depend on pointer gestures or color. That is a scoped accessibility review, not WCAG conformance or human assistive-technology acceptance. Stable status/count/hash keys are language-neutral integration surfaces; human documentation is English-first and multilingual user acceptance is not claimed.

## Recovery

P-049 does not mutate scanned repository content. If a run is interrupted or reports ERROR, discard incomplete evidence and rerun against unchanged input. Consumers can roll back by pinning a prior reviewed release or removing the workflow invocation.

## Permanent non-claims

PASS does not prove every secret is absent, Git history is clean, credentials are valid or revoked, all detector rules are perfect, or a repository is secure. False positives and false negatives remain possible. P-049 does not scan private history, run on self-hosted runners, accept arbitrary detector policy, auto-revoke credentials, auto-edit repositories, claim WCAG conformance, or promote any flagship/adjacent product by implication.

## Completion decision

The accompanying machine-readable record enumerates all 19 canonical gates. This tranche must freshly rerun the P-049 contract tests, independently re-fetch the public release and exact tag, re-consume `@v0.6.0` against the pinned real public consumer, confirm input immutability and runtime canaries, and run the generic completion-contract auditor. Only a green current-head result permits merge and subsequent governing DAIS portfolio synchronization.
