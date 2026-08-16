# P-051 / P-057 Final Completion Record — v0.2.0

**Projects:** P-051 Release Automation Action; P-057 Release Governance Tool  
**Public product:** DAIS Governed Release Toolkit  
**Repository:** `AntonyMD7/amd-ryzen-ai-max-vgm-96gb`  
**Released version:** `v0.2.0`  
**Exact released product source:** `7fa66e4dd3d851b7fe6750cf7ee3d1f084d9811e`  
**Release-control main commit:** `091768c34e518218482a3605e64241da647d0773`  
**Release workflow:** `DAIS governed release toolkit v0.2.0`, run `31926735521`  
**Publication evidence artifact:** `governed-release-toolkit-publication-31926735521`, artifact ID `9258058715`, SHA-256 `edd9b1fa5f61bb791e050eea4fc40786a83b87e8ae5be2a225c1c82efebe75e7`  
**Plan evidence artifact:** `governed-release-toolkit-plan-31926735521`, artifact ID `9258056770`, SHA-256 `f30dcdbbe3de0dfd5d2840acf473fbe111847de59813a0d3471f648feecfcde8`  
**Completion date:** 2026-08-16

## Final judgement

P-051 and P-057 satisfy the DAIS public-build completion contract for the released `v0.2.0` scope.

They are completed as two roles of one intentionally shared public product rather than as duplicated repositories:

- **P-051 Release Automation Action** is the reusable, plan-first GitHub composite Action plus fixed-argument release tooling that validates and, only in a trusted push context, performs a draft → verify → publish → exact-tag-verify lifecycle.
- **P-057 Release Governance Tool** is the surrounding manifest, least-privilege policy, fail-closed state model, source-identity controls, evidence contract, recovery semantics, threat model and completion boundary.

A single implementation is deliberate: separating the write operation from its governance/evidence contract into independent products would duplicate the highest-risk logic and create inconsistent safety boundaries.

## Search-before-build decision

The product deliberately does not rebuild mature release/versioning systems. GitHub Releases remains the publication system of record. Release Please remains appropriate for Conventional-Commit-driven release PR/changelog automation, while Changesets remains appropriate for package/monorepo versioning and changelog workflows. The DAIS toolkit fills a narrower gap: exact reviewed-source publication with fail-closed context checks, draft identity verification, post-publication tag verification, recovery evidence and a hard rule that publication never implies product completion on its own.

## Released product surface

The released `v0.2.0` source contains:

- `.github/actions/governed-release/action.yml` — reusable composite action;
- `scripts/governed_release_manifest.py` — strict read-only manifest validator;
- `scripts/governed_release_publish.py` — plan-only-by-default publisher;
- `tests/test_governed_release_toolkit.py` — adversarial release lifecycle/security tests;
- `tests/test_governed_release_manifest_paths.py` — dot-path/traversal regression boundary;
- `docs/GOVERNED-RELEASE-START-HERE.md` — beginner/operator entry point;
- `docs/GOVERNED-RELEASE-TOOLKIT.md` — product README-equivalent, architecture, use, threat and limitation surface;
- `docs/RELEASE-GOVERNANCE.md` — governance and recovery semantics;
- `.github/ISSUE_TEMPLATE/governed-release-toolkit.yml` — privacy-safe public support path;
- `RELEASE-NOTES-v0.2.0.md` — release scope and non-claims;
- `release/governed-release-toolkit-v0.2.0.json` — reviewed release intent.

The toolkit is distributed from the shared DAIS public proving-ground repository instead of creating duplicate repositories for the Action and governance layer. Product-scoped documentation is therefore used as the complete README surface for these two IDs.

## Real-world acceptance

The final release was not simulated. GitHub Actions run `31926735521` exercised the generic toolkit against the public GitHub Releases service.

The read-only validation job passed:

- adversarial toolkit tests;
- exact source retention/ancestry check;
- actual loading/execution of the reusable composite Action in plan-only mode;
- explicit no-draft/no-publish/no-completion-mutation assertions;
- sanitized plan-evidence retention.

The separately permissioned publish job then passed:

- canonical-main checkout;
- the reusable generic Action with `publish: true`;
- draft creation and identity verification;
- public publication;
- independent public release identity verification;
- independent exact remote tag-target verification;
- sanitized publication evidence retention.

The public GitHub release `v0.2.0` is non-draft and was published at `2026-08-16T04:29:18Z`. The public `refs/tags/v0.2.0` ref resolves exactly to product source `7fa66e4dd3d851b7fe6750cf7ee3d1f084d9811e`.

## Red-team loop and permanent fixes

The dedicated release exercise found defects that source-only tests had not exposed. They were fixed before release rather than documented as workarounds.

### Finding 1 — composite Action manifest had never been loaded by GitHub

The first real integration run reached 9/9 passing unit tests, then GitHub rejected the Action manifest because an unquoted YAML description contained `contents: write`.

**Permanent fix:** quote the YAML scalar and preserve real composite-Action loading as an integration gate.

### Finding 2 — path safety guard rejected legitimate dot-prefixed repository paths

The next real Action execution exposed an over-broad `value.startswith('.')` rule that rejected `.github/...` and `.changeset/...` even though they are normal repository paths.

**Permanent fix:** allow legitimate dot-prefixed names while continuing to reject actual `.`, `..`, `./`, `../`, empty, absolute and embedded traversal/current-directory segments. Dedicated regression tests cover both acceptance and refusal cases.

### Finding 3 — pre-squash branch source identity is not canonical after squash merge

The first post-merge release attempt correctly failed closed because the manifest pointed to a PR-branch commit that was not an ancestor of squash-merged `main`. The write-capable publish job was skipped and no release/tag was created.

**Permanent fix:** bind release intent only to an exact product commit already present on canonical main. PR #87 rebound `v0.2.0` to `7fa66e4dd3d851b7fe6750cf7ee3d1f084d9811e`; the subsequent public release run passed end to end.

These findings are material acceptance evidence: the loop did not weaken a guard to obtain green CI; it corrected integration and identity semantics while preserving fail-closed behavior.

## Security and privacy review

The released boundary is intentionally narrow:

- plan mode performs no external release mutation;
- pull-request context cannot publish even if a token is accidentally present;
- the write job exists only on an exact trusted `push` ref and receives only `contents: write`;
- no `pull_request_target` write path exists;
- command execution uses fixed argument arrays rather than a generic shell executor;
- an existing tag or release is a hard refusal rather than an overwrite/move target;
- source commit must be exact, retained and ancestral to the release-control checkout;
- draft tag/title/target identity is verified before publish;
- remote public tag identity is verified after publish;
- token values are not copied to retained evidence;
- public issue intake explicitly prohibits credentials, private URLs/content and internal infrastructure details.

A successful release authenticates the tested release identity/lifecycle. It does not prove semantic product quality, package-registry publication, artifact safety, SLSA conformance, production readiness or the correctness of unrelated roadmap projects.

## Recovery / rollback semantics

The toolkit deliberately refuses silent retries over uncertain publication state.

- **Failure before draft creation:** no release mutation is expected; correct the reviewed input/context and make a new reviewed attempt.
- **Failure after draft creation but before publication:** leave the draft unpublished and inspect retained evidence before any manual deletion/retry.
- **Failure after publication but before exact-tag verification:** treat as a release incident; preserve evidence and compare intended source, public release and remote tag. Never move the tag automatically to manufacture success.
- **Existing tag/release:** refuse. Use a new reviewed version instead of overwriting public identity.

GitHub releases themselves are not automatically rolled back because public version identity is historical evidence. Recovery is fail-closed containment and explicit operator review, not destructive rewriting of release history.

## Accessibility and multilingual review

The product is text-first. Configuration/evidence are JSON/YAML, error conditions are explicit, and the GitHub/CLI paths are keyboard-operable. The beginner path describes the safety lifecycle without requiring internal implementation knowledge. This review does not claim WCAG conformance or human assistive-technology acceptance for GitHub's own interface.

The manifest/evidence semantics are language-neutral. Current public operator documentation is English-first; localized explanatory layers can be added without changing the canonical safety contract. This satisfies multilingual-path consideration, not multilingual user acceptance.

## Known limitations

- GitHub Releases is the only write backend in v0.2.0.
- The toolkit does not calculate semantic-version changes, generate changelogs or publish packages.
- It does not build/sign binaries or prove semantic artifact goodness.
- It does not configure branch-protection or immutable-release repository settings.
- GitHub job `contents: write` remains consequential authority and must stay isolated to trusted publication.
- A human/project-specific review is still responsible for deciding what should be released.
- The release is hosted inside the shared DAIS public proving-ground repository; P-051 and P-057 intentionally share one implementation/distribution surface.
- Public product documentation is English-first; no multilingual or WCAG conformance claim is made.

## Completion-contract evidence map

| Canonical gate | Result | Primary evidence |
|---|---|---|
| Problem / intended users | PASS | `docs/GOVERNED-RELEASE-TOOLKIT.md`, `docs/GOVERNED-RELEASE-START-HERE.md` |
| Public distribution surface | PASS | public repository + GitHub release `v0.2.0` |
| Open-source license | PASS | `LICENSE` (MIT) |
| Complete README | PASS | product-scoped `docs/GOVERNED-RELEASE-TOOLKIT.md` in the shared proving-ground repository |
| Beginner start path | PASS | `docs/GOVERNED-RELEASE-START-HERE.md` |
| Engineering / architecture | PASS | toolkit + `docs/RELEASE-GOVERNANCE.md` |
| Reproducible use | PASS | start-here + workflow/action examples |
| Safety / limitations | PASS | toolkit, governance, release notes |
| Recovery / rollback | PASS | toolkit + governance + this completion record |
| Tests / CI | PASS | adversarial tests + run `31926735521` |
| Security / privacy | PASS | `SECURITY.md`, toolkit threat model, issue form, real least-privilege release run |
| Accessibility | PASS WITH LIMITATIONS | toolkit/start-here review; no WCAG/AT claim |
| Multilingual path | PASS WITH LIMITATIONS | language-neutral schema/evidence; English-first docs |
| Real-world acceptance | PASS | generic Action published actual public `v0.2.0` via GitHub Releases |
| Evidence retained | PASS | release, tag, run + artifacts `9258058715` and `9258056770` |
| Version / release | PASS | `v0.2.0` |
| Known limitations | PASS | toolkit, release notes, this record |
| Contribution / issues | PASS | `CONTRIBUTING.md`, governed-release issue form |
| Canonical handover/build record | PASS | this document + machine-checkable per-ID completion records |

## Final status

**P-051: COMPLETE for DAIS Governed Release Toolkit v0.2.0.**  
**P-057: COMPLETE for DAIS Governed Release Toolkit v0.2.0.**

Completion is scope-bound. Future feature work, additional release backends, localization, independent security review or upstream integrations can improve later versions without invalidating the completed, evidence-bound v0.2.0 scope.
