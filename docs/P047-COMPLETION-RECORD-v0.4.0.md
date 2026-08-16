# P-047 README Lint Action v0.4.0 — Final Completion Record

Status: **COMPLETE candidate pending fresh completion-tranche CI; canonical status must not be promoted until this record passes on its final head**

Roadmap ID: **P-047 — README Linting Action**

## Product

**DAIS README Lint Action v0.4.0** is a reusable, non-mutating GitHub composite Action for bounded `README.md` style/structure checking. It adopts the established `DavidAnson/markdownlint-cli2-action` rather than implementing a competing Markdown parser or rules engine.

The released product source is exact commit `e8ec4a6f5dfbaadfaca46c98ad3679dce8e1ddd7`. Public `v0.4.0` was published through the governed release workflow and independently verified to resolve to that exact source.

## Search-before-build decision

Fresh upstream review on 2026-08-16 found `DavidAnson/markdownlint-cli2-action` release `v24.2.0`; its signed annotated tag resolves to commit `21c1be1b93ad9ed58fa840aacc3f279cde2a72ff`. P-047 pins that immutable commit. The DAIS value is the safety/adoption boundary: fixed no-plugin configuration, fail-closed scope preflight, no auto-fix, explicit outputs, least-privilege workflow guidance, truthful negative controls, privacy guidance, release evidence and beginner/engineer documentation.

## Architecture and security boundary

The Action accepts one relative workspace root, then `preflight.py` validates containment and refuses absolute/parent-traversing/glob roots, root symlinks, README symlinks, missing/no-README scopes, more than 250 selected READMEs, files over 2,000,000 bytes, and total selected README content over 10,000,000 bytes.

The fixed markdownlint profile exposes no repository-controlled `customRules`, Markdown-it plugin, or custom output formatter surface. Upstream `fix` is hard-coded to `false`, so linting never edits README files. The documented baseline permission is `contents: read`.

README text must be readable to lint it and diagnostics can reflect source lines. P-047 is therefore not a redaction/DLP boundary; sensitive documentation must not be sent to a public CI context.

## Recursive break/fix evidence

The product was not promoted from the earlier plan-only `P-047` reference. It was rebuilt as a real composite Action with:

- pinned upstream identity;
- bounded preflight;
- no-plugin/no-auto-fix profile;
- explicit machine outputs;
- positive and adversarial negative controls;
- byte-for-byte no-mutation proof;
- privacy-safe public support form;
- governed exact-source release;
- released-ref consumption against two separate public repositories.

The consumer acceptance deliberately treats a truthful lint finding as valid product behavior: a public repository may PASS or FAIL lint, but the Action output must agree with the GitHub step outcome, bounded README discovery must succeed, and README bytes must remain unchanged. This prevents a completion audit from laundering arbitrary style conformity into the acceptance requirement.

## Hosted and release evidence

### Product acceptance

PR #96 productized P-047 and its dedicated `P-047 README Lint Action acceptance` lane passed on the reviewed product head before squash promotion to exact public source `e8ec4a6f5dfbaadfaca46c98ad3679dce8e1ddd7`.

The acceptance lane proved:

1. a valid generated README passes;
2. an invalid generated README fails closed;
3. an empty scope fails closed;
4. parent traversal is refused;
5. the valid README remains byte-for-byte unchanged;
6. outputs carry PASS, README count and the exact upstream commit;
7. adversarial contract tests pass.

### Governed release

Run `31930292226` completed both validation and publication jobs successfully. It retained:

- release-plan artifact `9259065772`, SHA-256 `b7f979f53204932a4d82020c3c4bdf030396f3f73af7177e92c3f992d2c5b18f`;
- publication artifact `9259068031`, SHA-256 `4c1ab7b62595bd2dd2c9b4f2a07af6535070096da5b4c42f278f341cb3db7491`.

The public non-draft release is `v0.4.0`, titled **DAIS README Lint Action v0.4.0**, published 2026-08-16. Independent workflow verification resolved the public tag to exact reviewed product source `e8ec4a6f5dfbaadfaca46c98ad3679dce8e1ddd7`.

### Released-ref real-public-consumer acceptance

Run `31930402427`, job `95124180487`, completed successfully using the public `@v0.4.0` Action against:

- `AntonyMD7/learning-git@01723a1825113de08810193f37e8047d978433c2`;
- `AntonyMD7/Kimi-Haul@5905f5be3f812b801ab5f7ec5b33c65c166131fc`.

Both released-Action invocations completed successfully and the workflow's independent semantic/immutability assertion passed. Both README hashes were rechecked unchanged after consumption. Sanitized evidence is retained as artifact `9259091393`, SHA-256 `91f424baff55c0b38553592a4743f8acc2a23d50508417210293770e10118a35`, with 30-day retention.

## Accessibility and multilingual applicability

P-047 is a non-graphical developer/CI Action. Its primary interaction is text plus stable machine outputs, explicit PASS/FAIL states, README counts and markdownlint rule identifiers; it does not require color or pointer interaction. This is an applicability review, not WCAG conformance or human assistive-technology acceptance.

Stable rule/output identifiers are language-neutral interoperability keys and can support localized explanatory documentation. v0.4.0 human documentation is English-first; multilingual user acceptance is not claimed.

## Recovery and rollback

P-047 does not mutate README files. For an interrupted/missing/partial run, discard the incomplete result and rerun against unchanged source. For an undesired Action release, consumers can pin a previously verified immutable tag/commit or remove the workflow. P-047 never moves consumer branches or rewrites documentation.

## Known limitations

v0.4.0 is deliberately scoped:

- GitHub Actions Linux runner context with Python 3 preflight and upstream Node 24 Action;
- README Markdown style/structure only;
- fixed DAIS rule profile;
- no repository-controlled custom rules/plugins/formatters;
- no auto-fix;
- no factual/currency/completeness proof;
- no link-health proof;
- no accessibility-conformance proof;
- no secret/DLP guarantee;
- no GitHub Enterprise Server, local `act`, Windows-hosted or macOS-hosted runner acceptance claim;
- English-first human documentation.

## Completion decision

The companion machine record `examples/public-build-completion-p047-v0.4.0.json` enumerates all 19 canonical gates. P-047 may be promoted to `COMPLETE` only after the final completion tranche containing that record, this handover and its completion tests passes fresh CI without weakening any gate. The released v0.4.0 scope remains exactly the scope described above; completion does not imply broader repository quality or documentation correctness.
