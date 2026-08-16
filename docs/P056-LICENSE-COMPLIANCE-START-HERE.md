# Start Here — P-056 License Compliance Checker

P-056 helps you check whether a repository's **copyright and license metadata** satisfies the REUSE Specification using the real upstream REUSE linter.

## What you get

The Action returns one of two successful audit states:

- `REUSE_COMPLIANT` — pinned REUSE 6.2.0 reports the snapshot compliant with REUSE Specification 3.3.
- `REUSE_NONCOMPLIANT` — the audit worked, but REUSE says the snapshot still has metadata issues to fix.

A noncompliant result is **not** an Action malfunction. It is useful evidence.

## What you do not get

This tool does not tell you that software is legally safe to distribute. It does not decide whether two licenses are compatible, whether every third-party notice is complete, or whether dependency licensing is acceptable for your organization. Those decisions need separate policy and, where appropriate, legal review.

## Safe first use

```yaml
name: License metadata check
on: [pull_request]
permissions:
  contents: read
jobs:
  license:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
        with:
          persist-credentials: false
      - id: check
        uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/license-compliance@<reviewed-ref>
        with:
          root: .
          language: en
      - run: |
          echo "status=${{ steps.check.outputs.status }}"
          echo "compliant=${{ steps.check.outputs.compliant }}"
```

The product installs exact `reuse==6.2.0` into runner-temporary storage, records the resolved environment digest, runs only `reuse lint --json`, and writes its outputs outside your checkout.

## Privacy note

The sanitized P-056 JSON intentionally removes file paths, copyright identities, recommendations and literal license IDs. The separate `raw-report-path` can contain repository-relative filenames and other diagnostic details. **Do not automatically publish the raw report from private repositories.**

## If the result is noncompliant

1. Open the raw REUSE report locally in the workflow/run environment or reproduce `reuse lint` in a safe checkout.
2. Fix the reported SPDX/REUSE metadata on a normal reviewed branch.
3. Rerun P-056.
4. Review dependencies, vendored material, notices and license compatibility separately.

P-056 never edits your files for you, so rollback is simply removing your own proposed metadata change if review rejects it.

## Spanish guidance

Set `language: es`. The guide text changes language, but the underlying compliance report and SHA-256 remain the same technical truth.

For architecture, threat model, exact claim boundaries and test coverage, see [`P056-LICENSE-COMPLIANCE.md`](P056-LICENSE-COMPLIANCE.md).
