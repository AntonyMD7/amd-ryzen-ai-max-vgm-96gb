# Universal Evidence Validation Action v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-050 Evidence Validation Action`; reusable by `F-05 Universal Evidence Standard`, `P-212 Universal Evidence Schema`, `P-213 Evidence-First Automation Library`, and `P-214 Recovery-First Mutation Framework`.

## Search-before-build decision

Generic JSON-schema validation already has mature tooling, including `python-jsonschema`/`check-jsonschema` and multiple GitHub Actions. GitHub and in-toto also provide stronger signed artifact-attestation ecosystems. This action therefore does not claim to replace a generic validator or signed attestation verifier.

Its narrow value is applying the DAIS Universal Evidence v0.1 contract and, when requested, independently checking SHA-256 values of evidence-referenced local artifacts without executing those artifacts.

## Components

- `scripts/evidence_validate.py` — schema + optional artifact-digest validator;
- `.github/actions/evidence-validate/action.yml` — reusable composite GitHub Action wrapper;
- `tests/test_evidence_validate.py` — mutation fail-closed, hash match/mismatch and path-traversal tests.

The composite action pins `jsonschema==4.26.0` instead of floating an unconstrained dependency. A future release should further improve supply-chain reproducibility with a lock/hash or packaged runtime.

## Fail-closed behavior

Validation fails when:

- the evidence does not satisfy the Universal Evidence schema;
- a declared artifact is missing;
- a declared SHA-256 does not match;
- an artifact path is absolute or escapes the configured artifact root.

The validator never invokes, imports or executes an evidence artifact.

## Trust boundary

A valid record is **not proof that the claimed event happened**. It only means the record conforms to the schema and, when requested, the local artifact bytes match the declared hashes.

Strong claims may additionally need producer authentication, signed attestations, protected CI provenance, independent acceptance and/or an in-toto/GitHub artifact attestation. GitHub's official `actions/attest` family uses in-toto-format attestations for artifact predicates; that ecosystem should be interoperated with rather than replaced.

## Beginner view

> "This check can tell us whether the evidence file is shaped correctly and whether the saved artifact still has the same SHA-256. It cannot prove by itself that someone really performed the action they described."

## Security/privacy

The action reads only the evidence JSON, schema and explicitly referenced artifacts under an optional caller-supplied root. It makes no network request itself, changes no artifact and executes nothing from the evidence bundle. The composite wrapper may access the Python package index to install the pinned JSON-schema library unless the runner already provides it.

## Completion gaps

`P-050` remains **IN PROGRESS**. Completion requires:

- a versioned/released standalone action surface rather than a subdirectory proving ground;
- locked/verifiable action dependencies and supply-chain attestation;
- machine-readable action outputs and annotations;
- interoperability mapping to in-toto/GitHub attestations;
- recursive evidence-bundle rules where needed;
- fixtures from multiple public projects;
- accessibility/multilingual documentation and canonical completion evidence.
