# P-048 Broken Link Scanner — Start Here

**Status:** IN PROGRESS release candidate  
**Version target:** v0.5.0  
**Roadmap ID:** P-048

## What this does

The DAIS Broken Link Scanner checks links in public documentation and fails CI when a reference is broken. It is designed for maintainers who want a simple GitHub Actions check without giving repository-controlled documentation a path to probe private networks.

The scanner uses the established open-source **Lychee** engine instead of inventing another link checker. DAIS adds a deliberately narrow safety, privacy, reproducibility, and evidence boundary around it.

## Quick use

Copy or consume the released Action in a GitHub-hosted Ubuntu workflow and grant only `contents: read`:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@<reviewed-immutable-sha>
    with:
      persist-credentials: false
  - uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/broken-link-scan@<released-ref>
    with:
      root: docs
```

Until v0.5.0 is actually released, treat this example as release-candidate documentation and do not invent a tag.

## What PASS means

`PASS` means the fixed scanner configuration found no broken references in the bounded files selected for that exact run.

It does **not** mean:

- the destination says the right thing;
- a destination is safe or trustworthy;
- every transient website will always answer GitHub-hosted runners;
- the documentation itself is correct, complete, accessible, or secure;
- authenticated/private links have been checked.

## Why it refuses self-hosted runners

A documentation file can contain a URL such as `http://127.0.0.1`, `http://10.0.0.5`, or the cloud metadata address `169.254.169.254`. A generic link checker that blindly follows repository-controlled URLs can become an SSRF/private-network probe.

P-048 v0.5.0 therefore:

1. runs only on GitHub-hosted Linux x64 runners;
2. performs a network-free preflight over the documentation first;
3. rejects explicit loopback, link-local, private IP, local/private hostname, embedded-credential, and unsupported-scheme targets;
4. invokes Lychee with its request-time private-address exclusion so DNS resolving to a private address is also refused;
5. exposes no arbitrary Lychee argument or preprocessor input.

## Privacy

Raw scanner output can contain full URLs, query strings, fragments, or repository text. The reusable Action does not retain that output as public evidence. Its machine-readable result keeps counts, exit classification, and SHA-256 fingerprints of raw diagnostics instead.

Do not use v0.5.0 for private documentation or authenticated URLs. Do not put credentials in documentation URLs.

## If the check fails

A `FAIL` means broken links were reported. An `ERROR` means the scanner itself could not complete reliably. Both fail CI closed.

Review the failing workflow logs under the repository's normal access controls. Fix or intentionally remove the reference, then rerun. Do not weaken the private-network or checksum gates to make CI green.

## Recovery

The product does not modify documentation. Rollback is therefore straightforward: remove the workflow invocation or pin back to the prior reviewed Action ref. No repository content repair is required because the Action has no auto-fix mode.

## Accessibility and language

The Action is non-visual and exposes concise text status plus machine outputs. Error meaning is written in plain English and does not depend on color. The v0.5.0 documentation path is English-first; consumers may localize explanatory workflow text without changing scanner semantics. This is not a claim of multilingual user acceptance or WCAG conformance.

## Need help?

Use the P-048 public issue form and provide sanitized reproduction details. Never paste credentials, private URLs, intranet hostnames, or proprietary documentation into a public issue.
