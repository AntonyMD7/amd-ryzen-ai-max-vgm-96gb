# DAIS Contributor Onboarding Assistant — Start Here

Roadmap ID: **P-054**  
Current release: **v0.9.0 — released, but not completion-accepted**  
Patch candidate: **v0.9.1**  
Status: **IN PROGRESS**

## What it does

P-054 gives maintainers and first-time contributors a small, deterministic onboarding audit without sending repository content anywhere. It checks whether a checkout contains the core public contribution surfaces a newcomer normally needs, then produces:

- a sanitized machine-readable JSON report;
- a human-readable onboarding guide in English or Spanish;
- a deterministic report SHA-256;
- an explicit list of required and recommended gaps.

It does **not** post comments, create issues, add labels, invite collaborators, run repository code, call the GitHub API, or change the repository.

## Why v0.9.1 exists

The first released-ref acceptance of `v0.9.0` deliberately exercised English and Spanish invocations in the same GitHub Actions job. That test exposed an output-isolation defect: both languages used the same runner-temporary directory, so the later Spanish invocation could overwrite the earlier English report/guide path before independent verification. The release remained **not COMPLETE**.

`v0.9.1` permanently fixes this by including the language in the runner-temporary output directory and adds a regression acceptance that requires English and Spanish output paths to be distinct while preserving the same underlying technical truth state.

## Quick local use

```bash
python scripts/p054_contributor_onboarding.py \
  --root /path/to/public-repository \
  --language en \
  --out-dir /tmp/p054-onboarding
```

The output directory must be outside the audited repository. Spanish guidance uses `--language es` and a separate output directory.

## GitHub Action use

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@<reviewed-commit>
    with:
      persist-credentials: false

  - id: onboarding
    uses: AntonyMD7/amd-ryzen-ai-max-vgm-96gb/.github/actions/contributor-onboarding@<released-version>
    with:
      root: .
      language: en

  - run: echo "${{ steps.onboarding.outputs.status }}"
```

Do not use `v0.9.0` as completion evidence. Use the later patch release only after its released-ref acceptance is green.

## What is checked

Required baseline:

- `README.md`;
- contribution guidelines in a supported project location;
- `SECURITY.md` in a supported project location;
- a recognizable root license file.

Recommended supporting surfaces:

- code of conduct;
- support guidance;
- pull-request template;
- one or more issue templates/forms;
- DAIS `START-HERE.md` where a project chooses to provide one.

The audit reports only bounded path, file-size and SHA-256 evidence. It does not copy file contents into its JSON evidence.

## How to read the result

`ONBOARDING_BASELINE_READY` means the P-054 required local surfaces were found in the audited checkout. It does **not** mean GitHub's Community Standards API has approved the repository, that policies are correct, that `good first issue` work exists, or that a contributor will have a good experience.

`ONBOARDING_BASELINE_HAS_GAPS` preserves missing required surfaces instead of manufacturing a passing score.

## Privacy

The generated guide reminds contributors not to put credentials, private repository material, personal/medical data, private network details, or other sensitive information into public issues or pull requests.

P-054 itself performs no network request and emits no audited absolute filesystem path.

## Recovery

The product is read-only. Delete runner-temporary/output reports and rerun. If a maintainer later changes community-health files based on the report, normal Git review/revert is the recovery path; P-054 does not make those changes.

## Completion boundary

P-054 remains IN PROGRESS until the patch is released and independently accepted. Completion still requires:

- green adversarial and hosted Action CI;
- exact-source patch release;
- released-ref real-public English/Spanish consumer acceptance with output isolation;
- retained evidence;
- final 19-gate completion audit and handover;
- fresh post-merge verification;
- canonical DAIS synchronization.
