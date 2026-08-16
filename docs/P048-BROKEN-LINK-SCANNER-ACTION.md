# P-048 Broken Link Scanner Action v0.5.0

**Canonical status:** IN PROGRESS until release and completion evidence satisfy the roadmap contract.

## Product definition

P-048 provides a reusable, beginner-safe GitHub Action for detecting broken references in public repository documentation. Its intended users are maintainers and contributors who need repeatable link validation without accepting the full flexibility—and therefore the full attack surface—of a general-purpose network scanner.

The product deliberately composes the mature Lychee link checker. DAIS owns only the bounded input policy, private-network protection, supply-chain lock, evidence minimization, truth boundary, acceptance tests, and release governance.

## Search-before-build decision

The established Lychee ecosystem already parses common documentation formats, validates local references, performs HTTP(S) checks, reports structured results, supports retries/timeouts, and provides private-address exclusion. Reimplementing that engine would add risk without public-good value.

The upstream `lychee-action` v2.9.0 was also reviewed. It is useful for general consumers, but it intentionally exposes broad Lychee arguments and downloads a selected Lychee release at runtime. P-048 needs a stricter contract, so v0.5.0 invokes a checksum-pinned Lychee binary directly with a fixed argument set instead of wrapping arbitrary action inputs.

## Architecture

```text
checked-out public repository
        |
        v
network-free preflight
  - bounded root/files/bytes
  - no symlink escapes
  - explicit URL safety review
        |
        v
exact Lychee 0.24.2 binary
  - official release URL
  - fixed x86_64 Linux asset
  - exact SHA-256 check
        |
        v
fixed scanner policy
  - GitHub-hosted only
  - --exclude-all-private
  - bounded retry/concurrency/timeout
  - no preprocess/arbitrary args/token
        |
        v
raw transient diagnostics in RUNNER_TEMP
        |
        v
privacy-minimized result
  - status/counts
  - raw diagnostic SHA-256 only
  - explicit non-claims
```

## Threat model

### Assets protected

- private services reachable from self-hosted runners;
- cloud metadata endpoints;
- intranet hostnames and addresses;
- tokens or credentials accidentally embedded in URLs;
- repository documentation content that should not be copied into public evidence;
- CI integrity and reproducibility.

### Untrusted input

Repository-controlled documentation is untrusted. A pull request may introduce arbitrary link targets even when workflow code itself is unchanged.

### Primary abuse case: SSRF/network discovery

Blind URL traversal from a self-hosted runner can expose services unavailable to the public Internet. Static string checks alone are insufficient because a public-looking DNS name can resolve to a private address.

v0.5.0 therefore combines two independent controls:

- **pre-request control:** Python preflight rejects explicit non-global IP literals, local/private hostname patterns, single-label hosts, embedded credentials, unsupported schemes, traversal, and symlink escapes without network access;
- **request-time control:** Lychee runs with `--exclude-all-private`, which excludes private, link-local, and loopback targets at request time, including after resolution.

The Action additionally refuses non-GitHub-hosted runners. This sacrifices self-hosted convenience to prevent repository documentation from becoming a private-network probe.

### Supply-chain boundary

The Action supports GitHub-hosted Linux x64 only in v0.5.0. It downloads exactly the official `lychee-x86_64-unknown-linux-gnu.tar.gz` asset for Lychee 0.24.2 and requires SHA-256:

`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`

The archive member paths are screened before extraction and exactly one executable named `lychee` must be found. No `latest`, nightly, package-manager, or source-build fallback exists.

## Permissions

The reusable Action itself requires no GitHub write permission and is designed for workflows with:

```yaml
permissions:
  contents: read
```

No GitHub token is passed to Lychee in v0.5.0. Consequently, links requiring authentication are outside this release scope.

## Bounded local input

The preflight accepts `.md`, `.markdown`, `.mdx`, `.html`, `.htm`, `.rst`, and `.txt` documents. It ignores common dependency/build directories and enforces:

- at most 500 documents;
- at most 2 MiB per document;
- at most 25 MiB total selected content;
- an existing relative root inside `GITHUB_WORKSPACE`;
- no symlink root, symlinked selected document, or parent traversal.

These bounds are resource-protection controls, not statements about ideal documentation size.

## Fixed network policy

The caller cannot supply arbitrary Lychee arguments. v0.5.0 fixes:

- JSON output;
- no progress UI;
- private-address exclusion;
- two retries;
- 20-second request timeout;
- host concurrency of four;
- 200 ms host request interval;
- bounded root and preflight-generated file manifest.

No `--preprocess`, `--insecure`, custom headers, authentication token, arbitrary command, or caller-selected endpoint policy is exposed.

## Evidence and privacy

Raw Lychee stdout/stderr is transient runner state and can contain URLs or repository details. The public result JSON never copies it. Instead it retains SHA-256 fingerprints, counts, status, network-scope declarations, and hard-false semantic/security claims.

A public CI artifact should contain only the sanitized result. Raw diagnostics remain subject to the normal restricted workflow-log/runtime boundary and are deleted with the hosted runner.

## Result semantics

- `PASS`: exact fixed scan completed without broken references.
- `FAIL`: Lychee reported broken links.
- `ERROR`: execution/configuration could not establish a reliable link-health result.

A PASS does **not** establish destination correctness, destination security, documentation correctness, accessibility, legal safety, availability outside the tested moment, or whole-repository quality.

## False positives and operational limits

Public sites may intentionally block automation, rate-limit GitHub runner ranges, require JavaScript, require authentication, or return transient errors. Those conditions are not silently converted to success. Consumers should correct links, document a narrowly reviewed exception in a future governed policy version, or choose a more appropriate specialist test.

v0.5.0 intentionally does not support:

- self-hosted runners;
- authenticated/private URLs;
- GHES/private-network checking;
- arbitrary headers or tokens;
- caller-supplied Lychee CLI arguments;
- dynamic preprocessing;
- auto-fixing documentation;
- semantic evaluation of destination content.

## Accessibility / multilingual review

This release exposes machine-readable outputs and a plain-text job summary that does not encode status by color alone. Documentation separates beginner and engineering explanations. English is the supported documentation language for v0.5.0; the architecture does not bind scanner semantics to English. Multilingual user acceptance and WCAG conformance are not claimed.

## Recovery / rollback

The Action is read-only with respect to repository files. Recovery from a bad release is pinning the consumer workflow back to an earlier reviewed ref or removing the invocation. The scanner performs no repository write, auto-fix, issue creation, comment, release, deployment, or device mutation.

## Completion boundary

Source and green CI are not enough. P-048 remains IN PROGRESS until, at minimum, the exact v0.5.0 source is governed into a public version/tag/release, the released ref is consumed against representative real public repositories, evidence is retained, the 19-gate completion contract passes independently, and the canonical handover/status record is updated.
