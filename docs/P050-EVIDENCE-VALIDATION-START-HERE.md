# P-050 Evidence Validation Action — Start Here

Roadmap ID: `P-050`

This guide is the shortest safe path for maintainers who want to validate DAIS Universal Evidence in GitHub Actions without confusing structural/hash validation with proof that an event really happened.

## What you get

The Action validates a DAIS Universal Evidence JSON record against the repository's Draft 2020-12 schema and, when `artifact-root` is supplied, verifies the SHA-256 values of explicitly named local artifacts. It returns bounded machine-readable outputs for downstream gates.

A `PASS` means the record has the expected structure and any requested local artifact hashes match. It does **not** authenticate the producer, authorize an action, prove the described event occurred, establish artifact safety, or prove semantic truth.

## Supported released runtime

The v0.3.0 release scope is intentionally fail-closed:

- GitHub-hosted or compatible Linux runner;
- x64 architecture;
- CPython 3.12;
- exact hash-locked binary-wheel dependency set committed with the Action.

Unsupported platforms fail instead of silently changing the dependency/runtime contract.

## Minimal use

```yaml
steps:
  - uses: actions/checkout@v4

  - uses: actions/setup-python@v5
    with:
      python-version: '3.12'

  - name: Validate DAIS evidence
    id: evidence
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/evidence-validate@v0.3.0
    with:
      evidence: evidence/result.json
      artifact-root: evidence/artifacts
      max-artifacts: '64'
      max-artifact-bytes: '104857600'

  - name: Require validation PASS
    if: ${{ steps.evidence.outputs.status != 'PASS' }}
    run: exit 1
```

For high-assurance use, pin the exact release commit instead of the human-readable tag after independently resolving it.

## Outputs

- `status`: `PASS` or `FAIL`;
- `schema-error-count`;
- `artifact-failure-count`;
- `verified-artifact-count`;
- `report-path`;
- `report-sha256`.

The complete report is written atomically before outputs are published.

## Producer provenance is separate

If you need to know who/what produced an artifact, combine P-050 with a signed attestation system. The project's acceptance lane uses GitHub artifact attestations and independently verifies the exact P-050 validation report. That provenance check is deliberately separate from P-050's schema/hash result.

## Failure and recovery

P-050 is read-only with respect to the evidence record and referenced artifacts. On interruption or dependency failure:

1. treat the missing/partial result as failure;
2. preserve the original evidence/artifact bytes;
3. fix the environmental cause;
4. rerun against the same bytes;
5. never convert a missing or `FAIL` report into success.

No rollback of input data is required because P-050 does not mutate it.

## Security and privacy

P-050 does not redact sensitive evidence. Do not publish private infrastructure details, credentials, PHI, personal data, or other sensitive content merely because it validates successfully.

The validator never executes referenced artifacts and performs no network access. Its wrapper performs only the hash-locked dependency installation needed for the declared runtime.

## Nested evidence bundles

Recursive/nested evidence-bundle traversal is explicitly **out of scope for v0.3.0**. Each invocation validates one evidence record and its directly declared artifacts. This keeps cycle/depth/size semantics unambiguous and avoids turning the validator into a workflow engine. A future version may add a separately specified bounded bundle protocol.

## Accessibility and language

The interface is text/JSON/YAML first: failure categories and plain-language reasons do not require a graphical dashboard, and outputs are accessible to assistive tooling. This is not a WCAG-conformance claim. Machine keys remain stable English identifiers for interoperability; human-facing documentation may be localized independently.

## Need help?

Use the repository's P-050 issue form. Report the smallest sanitized fixture that reproduces the problem; never attach secrets or private evidence.

For architecture, threat boundaries, detailed semantics, tests and limitations, see `docs/EVIDENCE-VALIDATION-ACTION.md`.