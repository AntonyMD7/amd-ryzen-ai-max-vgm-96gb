# P-048 Broken Link Scanner Action v0.5.0 — Final Completion Record

Status: **COMPLETE candidate pending fresh completion-tranche CI; canonical portfolio status must not be promoted until this record passes on its final head**

Roadmap ID: **P-048 — Broken-Link Scanner Action**

## Product

**DAIS Broken Link Scanner Action v0.5.0** is a reusable, non-mutating GitHub composite Action for bounded public-documentation link validation. It adopts the established Lychee project rather than building another parser/network checker, and adds a deliberately strict DAIS safety/evidence boundary for repository-controlled URLs.

The exact released product source is `1cc9cb51539e7e39e7141d994d9ad1709c71fece`. Public `v0.5.0` was published through the governed release workflow on 2026-08-16 and independently verified to resolve to that exact source.

## Search-before-build decision

Fresh upstream review selected Lychee as the specialist engine because it already handles common documentation formats, local references, HTTP(S) reachability, structured output, retries/timeouts and private-address exclusion. The upstream `lycheeverse/lychee-action` v2.9.0 was reviewed at exact commit `e7477775783ea5526144ba13e8db5eec57747ce8`.

P-048 does not duplicate Lychee. The DAIS product boundary is narrower than the generic upstream Action because arbitrary repository-controlled URLs are a network-security input. v0.5.0 therefore fixes the scanner policy, strips arbitrary argument/authentication surfaces, locks the downloaded engine artifact, minimizes retained evidence, and refuses self-hosted execution.

## Threat model and security boundary

The primary abuse case is SSRF/private-network discovery. A contributor can place a link to loopback, RFC1918, link-local/cloud metadata, a private suffix, or a public-looking DNS name that resolves privately. Running a generic checker on a self-hosted runner could expose infrastructure the contributor cannot otherwise reach.

P-048 v0.5.0 uses layered controls:

1. **GitHub-hosted-only execution.** The composite Action refuses any runner whose GitHub runner environment is not `github-hosted`.
2. **Network-free preflight.** The Python preflight rejects explicit non-global IP literals, localhost/private suffixes, single-label hosts, embedded URL credentials, unsupported absolute URL schemes, parent traversal, root/file symlinks and out-of-workspace paths before Lychee runs.
3. **Request-time protection.** Lychee runs with `--exclude-all-private`, so addresses that resolve to private/link-local/loopback space are excluded at request time rather than relying only on string inspection.
4. **No arbitrary scanner control.** No caller-supplied Lychee args, preprocessor, insecure TLS switch, custom header, GitHub token or authentication input exists in v0.5.0.
5. **Resource bounds.** The selected documentation corpus is capped at 500 files, 2 MiB per file and 25 MiB total.

The product is intentionally less flexible than a generic link checker. That is a security feature, not an omission.

## Supply-chain boundary

The Action supports GitHub-hosted Linux x64 in v0.5.0 and downloads the official Lychee 0.24.2 GNU x86_64 release archive only. It requires exact SHA-256:

`1f4e0ef7f6554a6ed33dd7ac144fb2e1bbed98598e7af973042fc5cd43951c9a`

Archive member paths are screened for traversal before extraction and exactly one `lychee` executable must be found. There is no moving `latest`, nightly, package-manager or source-build fallback.

## Privacy and evidence boundary

Raw link-scanner output can contain full URLs, query strings, fragments, source context or repository details. P-048 keeps raw stdout/stderr transient in `RUNNER_TEMP`; the reusable public result records only status/counts, explicit non-claims and SHA-256 fingerprints of raw diagnostics.

The product does not accept credentials or private URLs, and its dedicated public issue form explicitly instructs contributors not to paste credentials, intranet/private URLs, proprietary documentation or personal data into public support issues.

## Recursive break/fix evidence

The completion path deliberately did more than wrap an upstream Action.

During implementation review, a path-safety defect was caught before merge: resolving a candidate root before testing `is_symlink()` would erase the evidence that the original root itself was a symlink. The preflight was corrected to test the unresolved workspace candidate first and to verify each selected document resolves inside the workspace. URL parsing was also hardened to turn malformed-host parser failures into explicit fail-closed refusals rather than unhandled behavior.

Supply-chain review found that the generic upstream action's flexibility did not meet this product's reproducibility/security target. The DAIS Action instead downloads one exact official engine artifact and verifies its published SHA-256 before extraction.

The hosted acceptance then exercised positive and adversarial network inputs, while the release lane independently proved the exact public tag target and consumed the public release against real repositories.

## Product acceptance

Productization PR #99 passed the dedicated `P-048 Broken Link Scanner Action acceptance` workflow at reviewed head `41c687eab189cd6dbc212396aac4bd6a9a768f6a`. Run `31933502139` completed successfully before squash promotion to exact product source `1cc9cb51539e7e39e7141d994d9ad1709c71fece`.

The acceptance lane proved:

- a real public GitHub link plus local reference succeeds;
- scanner outputs and sanitized result digest are internally consistent;
- selected documentation remains byte-for-byte unchanged;
- an actual broken local reference fails;
- loopback and `169.254.169.254` cloud-metadata targets are refused;
- embedded-credential, empty-scope and parent-traversal inputs are refused;
- adversarial pure-Python contract tests pass;
- only the sanitized acceptance record is uploaded as evidence.

## Governed release

Release-control PR #100 passed its plan-only release validation and merged to canonical main `4473cd12cd0adae78e3f4c0fdf8248a7c01cb142`.

Push run `31933662718` completed validation, publication and released-consumer jobs successfully. It retained:

- release-plan artifact `9260014487`, SHA-256 `50690c2fc89cf937d00fb9bef76ed667f143de60516087844efc834e5e0254c3`;
- publication artifact `9260017297`, SHA-256 `5cbd00ff0528ac0cee36708a96b5e46426d62924608c6594cbd85db0becc6a76`;
- released-ref consumer artifact `9260019794`, SHA-256 `1cc38f8760d32ca949f4159aebd07c86e70c4ffeb2fcf9c92522d3b46d22d84d`.

The public non-draft release is `v0.5.0`, titled **DAIS Broken Link Scanner Action v0.5.0**, published at 2026-08-16T07:21:42Z. Independent workflow verification resolved the public tag to exact reviewed source `1cc9cb51539e7e39e7141d994d9ad1709c71fece`.

## Released-ref real-public acceptance

The public `@v0.5.0` Action was then consumed against real public repositories in run `31933662718`.

### Positive consumer

`AntonyMD7/learning-git@01723a1825113de08810193f37e8047d978433c2` was checked using the released Action. The scanner observed the real public documentation, returned PASS, and the workflow independently rechecked the README hash unchanged.

### Safety-negative consumer

`AntonyMD7/Kimi-Haul@5905f5be3f812b801ab5f7ec5b33c65c166131fc` contains an explicit `http://localhost:3000` documentation target. The released Action failed closed on that real public repository rather than attempting to make the private/local request. That failure is an acceptance success for the product's declared network-safety contract.

The two consumers intentionally prove different things: useful public link checking and refusal of a repository-controlled private target. Neither is relabeled as a universal availability/security verdict.

## Result semantics

- `PASS` means the exact fixed scanner configuration found no broken references in the bounded tested scope at that time.
- `FAIL` means a broken reference was reported or an explicitly unsafe target was refused.
- `ERROR` means scanner/configuration execution could not produce a trustworthy PASS result.

A PASS does not establish destination correctness, destination security, documentation factual correctness/completeness, accessibility conformance, legal safety, availability from other networks, or future availability.

## Accessibility and multilingual applicability

P-048 is a non-graphical CI/developer Action. Its primary interface is text plus stable status/count/hash outputs; operation does not depend on color or pointer interaction. This is an applicability review, not WCAG conformance or human assistive-technology acceptance.

Stable machine outputs are language-neutral integration keys and explanatory workflow text can be localized independently. v0.5.0 human documentation is English-first; multilingual user acceptance is not claimed.

## Recovery and rollback

P-048 never edits repository documentation. If execution is interrupted or evidence is missing, the incomplete result is discarded and rerun against unchanged source. If an Action release is undesirable, a consumer can pin a previously reviewed immutable ref or remove the workflow invocation. No content rollback transaction is required because the product has no auto-fix path.

## Known limitations

v0.5.0 intentionally does not support:

- self-hosted runners;
- GHES/private-network link checking;
- authenticated or private URLs;
- custom headers or tokens;
- arbitrary Lychee CLI arguments or preprocessing;
- insecure TLS bypass;
- auto-fixing documentation;
- destination semantic/security evaluation;
- guaranteed success against sites that rate-limit or block GitHub-hosted automation;
- documentation correctness/completeness proof;
- accessibility conformance;
- future-availability guarantees;
- multilingual human acceptance.

The current runtime acceptance is GitHub-hosted Linux x64 only.

## Completion decision

The companion machine record `examples/public-build-completion-p048-v0.5.0.json` enumerates all 19 canonical gates. P-048 may be promoted to `COMPLETE` only after the final completion tranche containing that record, this handover, completion tests and fresh released-ref verification passes CI without weakening any gate.

After that public completion merge, the governing private DAIS portfolio status must be synchronized from 5 COMPLETE / 222 IN PROGRESS to 6 COMPLETE / 221 IN PROGRESS. That portfolio synchronization records the product's verified completion; it does not broaden the v0.5.0 scope or promote any flagship foundation.
