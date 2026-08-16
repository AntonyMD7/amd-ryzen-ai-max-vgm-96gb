# DAIS Contributor Onboarding Assistant v0.9.0

Roadmap ID: **P-054 — Contributor Onboarding Bot**

## What ships

`v0.9.0` is a reusable, read-only contributor-onboarding audit and guidance product. It checks a bounded set of local community-health surfaces, emits deterministic privacy-minimized JSON evidence, and produces the same evidence state as plain-language English or Spanish contributor guidance.

The product ships as:

- `.github/actions/contributor-onboarding/action.yml` — reusable composite GitHub Action;
- `scripts/p054_contributor_onboarding.py` — dependency-light local auditor;
- `docs/P054-CONTRIBUTOR-ONBOARDING-START-HERE.md` — beginner path;
- `docs/P054-CONTRIBUTOR-ONBOARDING.md` — architecture, threat model, recovery and claim boundaries;
- dedicated adversarial and GitHub-hosted acceptance tests;
- a privacy-safe P-054 support Issue Form.

## Search-before-build decision

GitHub already provides Community Standards/community profiles, CONTRIBUTING guidance, security policies, issue and pull-request templates, the repository `contribute` surface, and contributor-discovery labels. P-054 does not replace those services. It adds a portable network-free local audit and evidence contract around established GitHub contribution surfaces.

## Security and privacy boundary

The released product:

- performs no GitHub API request and accepts no token or credential input;
- performs no repository mutation, issue/comment creation, label/invite/permission change or contributor trust decision;
- executes no repository code and spawns no subprocess from the Python auditor;
- refuses path escape, symlink and oversized-file inputs;
- emits no absolute local path in its evidence;
- writes Action output only under `RUNNER_TEMP` and may append text guidance to `GITHUB_STEP_SUMMARY`;
- deliberately avoids a privileged `pull_request_target` posting bot.

## Accessibility and language

The interface is text-first JSON/Markdown with explicit headings and no color-only state. English and Spanish guidance are generated from the same underlying evidence contract. This is accessibility-oriented product design, not a WCAG conformance or assistive-technology acceptance claim.

## Evidence semantics

`ONBOARDING_BASELINE_READY` means the bounded P-054 required local files are present as acceptable regular files. It does **not** prove GitHub's server-side Community Standards result, policy correctness, availability of good-first-issue work, contributor trust, maintainer responsiveness, repository security, license compatibility for a contribution, WCAG conformance or multilingual human acceptance.

## Recovery

The product does not mutate the audited repository. Delete its runner-temporary/external outputs and rerun. Maintainer changes to community-health files remain normal Git-reviewed changes with ordinary Git revert/rollback.

## Release acceptance

The governed release requires:

1. exact-source retention and ancestry for source commit `a4ff77c6fb07f9284a451110f7acd1520aaddacc`;
2. fresh adversarial P-054 tests;
3. non-mutating governed-release planning on pull requests;
4. publication of `v0.9.0` only from trusted canonical `main`;
5. independent verification that the public tag resolves exactly to the reviewed source commit;
6. released-ref consumption against pinned public `AntonyMD7/learning-git@01723a1825113de08810193f37e8047d978433c2`;
7. repeated released-ref execution with identical report digest and byte-identical consumer input;
8. sanitized release and consumer evidence retention.

Publishing `v0.9.0` does not by itself mark P-054 COMPLETE. The canonical 19-gate completion record, final handover, fresh completion audit and governing DAIS synchronization remain separate gates.
