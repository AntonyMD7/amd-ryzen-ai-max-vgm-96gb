# P-048 Broken Link Scanner Action v0.5.0 — Release Notes

**Release status:** candidate; do not treat `v0.5.0` as published until the governed release workflow creates and independently verifies it.

## Purpose

P-048 turns mature Lychee link checking into a deliberately constrained public GitHub Action with a stronger default security and evidence boundary for repository-controlled documentation.

## Included in v0.5.0

- GitHub-hosted Linux x64 execution only;
- Lychee 0.24.2 exact official Linux x64 release asset;
- immutable SHA-256 verification of the downloaded binary archive;
- archive traversal screening before extraction;
- network-free documentation preflight;
- explicit refusal of loopback, private/non-global IP literals, cloud metadata, local/private hostnames, embedded URL credentials, unsupported absolute URL schemes, parent traversal, and selected-file symlinks;
- request-time Lychee `--exclude-all-private` protection for DNS/private-address resolution;
- fixed retry, timeout, host-concurrency, and request-interval policy;
- no caller-supplied Lychee arguments, preprocessor, insecure TLS option, GitHub token, custom headers, or authentication inputs;
- bounded documentation file count and byte limits;
- raw scanner output kept transient, with a privacy-minimized JSON result retaining only status, counts, explicit truth boundaries, and SHA-256 fingerprints;
- adversarial unit tests and hosted positive/negative integration acceptance;
- beginner, engineering, threat/privacy, recovery, accessibility, multilingual-path, limitation, and support documentation.

## Deliberate limitations

v0.5.0 does not support self-hosted runners, private/internal URLs, authenticated links, GHES/private-network checks, arbitrary Lychee configuration, auto-fixing, destination-content correctness, or security verdicts.

A site that blocks CI traffic can still fail the check. That is reported rather than silently converted to success.

## Completion boundary

Publishing v0.5.0 will not itself make P-048 COMPLETE. The released ref must still be exercised against representative real public repositories, evidence retained, and the canonical 19-gate completion audit and handover completed independently.
