# P-050 Evidence Validation Action v0.3.0 — Final Completion Record

**Roadmap ID:** P-050  
**Product:** DAIS Evidence Validation Action  
**Released version:** v0.3.0  
**Completion date:** 2026-08-16  
**Status:** COMPLETE for the explicitly bounded v0.3.0 scope after the machine-checkable 19-gate completion record and fresh completion CI pass.

## Product outcome

P-050 is a reusable public GitHub composite Action and Python validator for DAIS Universal Evidence. It validates one evidence record against the supported Draft 2020-12 schema and can verify exact SHA-256 values of directly declared local artifacts without executing or modifying them.

The released public ref is `v0.3.0`. It resolves to exact reviewed product source:

`f00ad749a07a9067075c87f5ca20feab04695288`

The later release-control and completion commits deliberately do not change the tag target.

## What COMPLETE means here

The canonical completion contract is satisfied for this public release scope:

- defined user/problem boundary;
- public MIT-licensed distribution;
- complete beginner and engineer documentation;
- reproducible declared runtime;
- adversarial tests and hosted CI;
- explicit security/privacy/accessibility/multilingual applicability review;
- failure/recovery guidance;
- real public release;
- two independent released-ref consumer executions;
- retained release/acceptance evidence;
- public issue/contribution paths;
- versioned release and final handover.

Completion does **not** widen the product's claims beyond the tested v0.3.0 boundary.

## Search-before-build and interoperability decision

P-050 intentionally does not reimplement mature generic schema, signing, identity or attestation systems. JSON Schema/python-jsonschema remains the schema-validation substrate. GitHub artifact attestations and established in-toto/Sigstore-style provenance mechanisms remain separate authenticated-provenance systems.

P-050 adds the DAIS-specific evidence/hash boundary and composes with signed provenance. Schema/hash validation and producer authentication are kept as different claims.

## Recursive break/fix evidence

The release process found material defects before completion rather than smoothing them over.

### 1. Incomplete supposedly hash-locked runtime

The first canonical-main signed-attestation run failed because `referencing==0.37.0` required `typing-extensions>=4.4.0`, but the initial `--require-hashes` file omitted it. Earlier PR tests had installed dependencies before invoking the Action and therefore accidentally masked the missing transitive package.

Permanent fix:

- add exact `typing-extensions==4.16.0` wheel SHA-256 to the runtime lock;
- verify every released dependency version after installation;
- add a clean hosted lane that first proves `jsonschema` is absent, then invokes the composite Action from scratch.

No hash/runtime gate was weakened.

### 2. Attestation creation was not robust independent verification

After the runtime fix, the canonical-main attestation lane successfully created a GitHub attestation but the immediately following repository lookup was brittle. Treating creation as equivalent to independent verification would have been incorrect.

Permanent fix:

- cryptographically verify the exact local attestation bundle emitted by the pinned attestation action;
- require exact repository, signer workflow, source ref and source digest;
- require certificate and verified timestamp material;
- separately require repository-attestation retrieval using the same exact policy with bounded propagation retry;
- retain sanitized verification evidence.

Canonical-main run `31929156755` passed both validation and the corrected signed-attestation interoperability path before release.

## Public release acceptance

Governed release/consumer run: `31929278253`.

The release-control job passed, the exact-source public release was published, and independent tag verification confirmed `refs/tags/v0.3.0` resolves to:

`f00ad749a07a9067075c87f5ca20feab04695288`

The public non-draft release is:

`https://github.com/AntonyMD7/amd-ryzen-ai-max-vgm-96gb/releases/tag/v0.3.0`

### Independent released-ref consumers

Two separate real public repositories were checked out read-only. The workflow downloaded the Action through `@v0.3.0`, which GitHub resolved to the exact released source above.

1. `AntonyMD7/learning-git`
   - exact consumer commit: `01723a1825113de08810193f37e8047d978433c2`
   - Action result: PASS
   - verified artifacts: 1
   - validator report SHA-256: `083493a2affc73346e70dcf3fcdbc0c0745f3d959d6bd26563ee2f7e277f7191`

2. `AntonyMD7/Kimi-Haul`
   - exact consumer commit: `5905f5be3f812b801ab5f7ec5b33c65c166131fc`
   - Action result: PASS
   - verified artifacts: 1
   - validator report SHA-256: `c8334ecc2b1532810ff6c1855a203adab2d091ffd821b29fe37e20607663b86a`

The consumer repositories were not mutated by acceptance.

## Retained evidence

Run `31929278253` retained:

- release-plan artifact `9258798897`, SHA-256 `85550a3554671c8bc5267b6aeba5b3b0e9f7c0341cb2b27910be3f4be5cf826e`;
- publication artifact `9258800798`, SHA-256 `739031f7b298a3bd50378964dbf0e322e00bd0449e17841e205e945ff19f324c`;
- learning-git consumer artifact `9258802973`, SHA-256 `48415009559fe7c21a30875dc341562a97fcc8418bdc0c62f09f34efb7e33055`;
- Kimi-Haul consumer artifact `9258802825`, SHA-256 `d88308a8ef0142ed809deef1d3ed227ce0bc4dc92ee150f4dff2fdeeb80e9588`.

The public release/tag and this permanent source record remain after short-retention CI artifacts expire.

## Security and privacy boundary

The validator:

- does not execute referenced artifacts;
- does not mutate evidence or artifact inputs;
- performs no validator network request;
- rejects absolute/traversal/symlink escapes;
- refuses duplicate artifact names;
- bounds artifact count and bytes hashed;
- writes its machine report atomically;
- warns that evidence validation is not sensitive-content redaction.

The GitHub wrapper's external dependency activity is limited to installation of the exact hash-locked runtime packages for the supported environment.

The public support form explicitly prohibits credentials, tokens, PHI, personal data, private infrastructure and unsanitized evidence.

## Accessibility and multilingual applicability

P-050 is a non-graphical developer/CI Action. Its interaction surface is text, JSON and YAML. PASS/FAIL is textual, counts are machine-readable, errors are categorized with plain-language reasons, and the full report remains available to assistive tooling. This is an applicability review, **not** a WCAG-conformance or human assistive-technology acceptance claim.

Stable machine keys remain English identifiers for interoperability. Human documentation is English-first and can be localized independently. Multilingual user acceptance is not claimed by v0.3.0.

## Recovery

P-050 is read-only for the evidence/artifact inputs. If execution, dependency installation or report publication is interrupted:

1. preserve unchanged input bytes;
2. treat a missing/partial/FAIL result as failure;
3. correct the environmental cause;
4. rerun against the same input bytes;
5. never synthesize or manually promote a PASS.

No input rollback is needed because the validator does not mutate inputs.

## Explicit limitations

v0.3.0 does not claim:

- Windows/macOS/ARM runtime support;
- recursive/nested evidence-bundle traversal;
- evidence redaction or data classification;
- producer authentication merely from a validation PASS;
- authorization proof;
- semantic truth of evidence claims;
- artifact safety/goodness;
- WCAG conformance;
- human assistive-technology acceptance;
- multilingual user acceptance.

Recursive evidence bundles were deliberately excluded from v0.3.0 rather than shipping underspecified cycle/depth/aggregate-resource semantics.

## Machine completion record

The complete canonical 19-gate evidence record is:

`examples/public-build-completion-p050-v0.3.0.json`

The portfolio ledger is updated in the same reviewed completion tranche. P-050 completion does not promote F-05 or any other project by implication.
