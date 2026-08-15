# Universal Evidence provenance acceptance build type

**Identifier:** `https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/blob/main/docs/UNIVERSAL-EVIDENCE-PROVENANCE-BUILD-TYPE.md`  
**Status:** experimental public acceptance profile; not a SLSA level claim.

## Purpose

This document defines the narrow build type used by the Universal Evidence provenance acceptance workflow. It exists so the provenance `buildType` is resolvable and the expected external interface can be independently inspected.

The workflow creates one deterministic demonstration artifact by copying the repository's already-public sanitized Universal Evidence fixture. It then records an in-toto Statement v1 with the SLSA Provenance v1 predicate type, signs that complete statement with Sigstore keyless signing, verifies the signed attestation, and evaluates the authenticated statement against an exact DAIS policy.

## External parameters

Exactly these three fields are accepted:

```json
{
  "sourceRepository": "https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb",
  "sourceCommit": "<exact Git commit SHA for this workflow run>",
  "workflowRef": "<exact GITHUB_WORKFLOW_REF>"
}
```

No additional external parameter is accepted by the DAIS acceptance parser. This is intentionally stricter than the generic SLSA parsing rule because this profile is a narrow policy fixture rather than a general-purpose provenance consumer.

## Resolved dependency

Exactly one source dependency is recorded:

```json
{
  "uri": "git+https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb@<exact commit>",
  "digest": {
    "gitCommit": "<exact commit>"
  }
}
```

## Artifact

The artifact name is `universal-evidence-provenance-fixture.json`. Its subject contains exactly one lowercase SHA-256 digest calculated over the exact bytes copied from `examples/universal-evidence-readonly-example.json` in the checked-out source commit.

## Builder identity used by this acceptance

The provenance `builder.id` is:

`https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/blob/main/docs/UNIVERSAL-EVIDENCE-DEMO-BUILDER.md`

That identifier describes this repository's demonstration provenance producer and its limitations. It is **not** a claim that the workflow is a SLSA Build L1/L2/L3 builder.

## How to initiate

Run `.github/workflows/universal-evidence-provenance-acceptance.yml` from a Git push. The workflow requires only repository read access plus GitHub OIDC `id-token: write` for ephemeral Sigstore keyless signing.

## Output

The workflow retains a sanitized evidence artifact containing:

- the demonstration artifact and digest;
- unsigned generated provenance Statement;
- Sigstore attestation bundle;
- cryptographic verifier output;
- bundle-material inspection;
- authenticated statement extracted from the signed bundle when supported by the pinned verifier;
- DAIS semantic validation result;
- exact trust profile/result;
- a claim-boundary record.

## Security / truth boundary

The workflow is a public source/CI acceptance fixture. It does not use or mutate production systems, private infrastructure, device state, secrets or user data. A PASS demonstrates a narrow signed-provenance verification path. It does not establish a SLSA level, artifact goodness, semantic truth, production readiness or completion of F-05.
