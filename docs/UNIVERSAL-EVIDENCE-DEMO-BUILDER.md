# Universal Evidence demonstration provenance builder

**Builder identifier:** `https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/blob/main/docs/UNIVERSAL-EVIDENCE-DEMO-BUILDER.md`  
**Roadmap mapping:** F-05 Universal Evidence Standard  
**Security status:** demonstration / supporting acceptance only.

## Scope

This identifier represents the repository-controlled GitHub-hosted workflow used only for the Universal Evidence provenance acceptance fixture. The workflow is defined at:

`.github/workflows/universal-evidence-provenance-acceptance.yml`

The workflow runs on a GitHub-hosted Ubuntu runner, checks out one exact public repository revision, copies one sanitized fixture into a deterministic demonstration artifact, generates a provenance statement, signs the statement keylessly with Sigstore/Cosign, verifies the signed attestation and evaluates the authenticated statement with an exact local policy.

## Trust base

For this demonstration, the relevant trust base includes GitHub Actions' hosted execution/control plane, this repository's workflow definition and dependencies, the pinned Cosign installer/action and binary version, Sigstore public-good signing/verification infrastructure, and the repository-controlled statement-generation logic.

Because the provenance statement is assembled by tenant-controlled workflow logic rather than an independently assessed provenance generator/control plane, this identifier intentionally claims **no SLSA Build level**.

## Accuracy / completeness promise

The acceptance policy checks only the following fields:

- exact artifact SHA-256 subject;
- exact in-toto Statement v1 type;
- exact `https://slsa.dev/provenance/v1` predicate type;
- exact repository-defined build type;
- exact three-field external parameter object;
- exact source repository and commit dependency;
- exact builder identifier;
- a GitHub run invocation identifier.

No claim is made that optional provenance fields are complete or that this workflow meets all SLSA producer/build-platform requirements.

## Signer-builder pairing

The expected signer is the exact GitHub Actions workflow certificate identity produced from `GITHUB_WORKFLOW_REF`. The DAIS trust profile accepts this builder identifier only after the signed statement has been cryptographically verified under that exact signer identity and exact GitHub Actions OIDC issuer.

This is a deliberately narrow signer-builder pair. Wildcard/regex identities are not accepted by the local trust-policy layer.

## Security limitations

This acceptance does not independently assess or prove:

- GitHub Actions build-platform hardening;
- SLSA Build L1/L2/L3 conformance;
- protection against a malicious repository maintainer changing the workflow;
- provenance completeness beyond the explicitly checked fields;
- semantic truth or safety of the artifact;
- production signing policy;
- long-term trust-root archival.

Consumers must not map this builder identifier to a SLSA level unless a separate evidence-backed assessment explicitly establishes that mapping.
