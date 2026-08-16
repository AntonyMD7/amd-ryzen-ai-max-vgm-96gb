# P-050 Evidence Validation Action — Start Here

P-050 is a small GitHub Action for checking **DAIS Universal Evidence** files.

## What it can tell you

A successful run means:

1. the evidence JSON follows the DAIS Universal Evidence schema; and
2. when you provide an artifact directory, each checked file has the SHA-256 value declared by the evidence.

A successful run does **not** prove that the event described in the evidence really happened, that its producer was authorized, or that an artifact is safe/correct. Signed provenance and independent acceptance are separate evidence layers.

## Supported released runtime

The v0.3 product scope is intentionally narrow and reproducible:

- GitHub Actions Linux x64 runner;
- CPython 3.12;
- fully version- and SHA-256-locked validator dependencies.

Unsupported platforms fail closed instead of silently selecting a different dependency graph.

## Minimal workflow

```yaml
name: Validate DAIS evidence
on: [push, pull_request]

jobs:
  evidence:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - id: validate
        uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/evidence-validate@<immutable-reviewed-ref>
        with:
          evidence: evidence/result.json
          artifact-root: evidence/artifacts
      - run: |
          test "${{ steps.validate.outputs.status }}" = PASS
          echo "report sha256=${{ steps.validate.outputs.report-sha256 }}"
```

For a released version, replace `<immutable-reviewed-ref>` with the exact published tag or, for maximum immutability, the release's exact source commit.

## Outputs

The action returns text outputs suitable for CI gates:

- `status`
- `schema-error-count`
- `artifact-failure-count`
- `verified-artifact-count`
- `report-path`
- `report-sha256`

The complete report is JSON. Treat `FAIL`, a missing report, or an interrupted job as failure—not as unknown success.

## If something fails

**Schema errors:** correct the evidence producer or evidence file. Do not edit evidence merely to make the check green if the underlying claim is wrong.

**Artifact hash mismatch:** re-establish which artifact is authoritative. A mismatch is evidence that the declared and observed bytes differ.

**Traversal/symlink error:** keep referenced artifacts under the configured `artifact-root` and use relative paths only.

**Unsupported runtime:** run the released action on Linux x64 with CPython 3.12. Other platforms can invoke the Python validator from source, but they are outside the hash-locked release acceptance boundary until separately released and tested.

**Dependency installation failure:** retry only after determining why the exact hash-locked wheel could not be installed. Never remove `--require-hashes` as a workaround.

## Privacy

P-050 does not redact sensitive evidence. Before storing evidence in a public repository or CI artifact, make sure the evidence is itself suitable for public retention. Do not publish credentials, private infrastructure, patient information, personal identifiers, or other sensitive payloads.

## Accessibility

P-050 is CLI/CI-first: results are expressed in text, counts and JSON rather than relying on color or a visual dashboard. GitHub annotations include plain-language reasons. This is an accessibility design choice, not a WCAG conformance claim.

## More detail

- Engineering/trust model: [`EVIDENCE-VALIDATION-ACTION.md`](EVIDENCE-VALIDATION-ACTION.md)
- Security policy: [`../SECURITY.md`](../SECURITY.md)
- Contribution guide: [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
- Universal Evidence schema: [`../schemas/universal-evidence-v0.1.schema.json`](../schemas/universal-evidence-v0.1.schema.json)

For bugs or compatibility questions, use the P-050 Evidence Validation issue template so the report includes the action ref, runner and failure class without requiring sensitive evidence content.
