# DAIS Governed Release Toolkit v0.2.0

This release publishes the reusable public-good implementation for roadmap projects **P-051 — Release Automation Action** and **P-057 — Release Governance Tool** from exact reviewed source commit `c119631d29e68412aa15097d364fb50eb27d19e8`.

## What ships

- reusable composite GitHub Action at `.github/actions/governed-release/action.yml`;
- strict, dependency-free governed-release manifest validation;
- plan-only-by-default publisher with an explicit trusted-push execution gate;
- draft → identity verification → publish → exact public tag verification lifecycle;
- hard refusal to overwrite an existing tag/release;
- fail-closed fork/PR, path-traversal, duplicate-ID, source-drift and completion-overclaim handling;
- sanitized release evidence that never retains the GitHub token;
- recovery guidance for partial draft/publication states;
- adversarial automated tests and public beginner/operator/engineer documentation.

## Search-before-build position

This toolkit does not replace Release Please, Changesets, GitHub Releases or package-manager publishing systems. Release Please remains a strong conventional-commit/changelog/release-PR solution; Changesets remains a strong package/monorepo versioning workflow. DAIS supplies a narrower fail-closed evidence and exact-source publication boundary that can compose with them.

## Security and truth boundary

A successful governed release proves only that the exact reviewed source revision was published through the tested GitHub release lifecycle and that the public tag resolves to that exact source. It does not prove semantic quality, package-registry publication, artifact safety, SLSA conformance, immutable-release repository settings, production readiness, or completion of unrelated roadmap projects.

The write-capable path requires an exact trusted `push` context and `contents: write`; pull-request execution is refused. Existing tags/releases are never moved or overwritten. Publication itself does not mark P-051 or P-057 complete.

## Completion follow-up

After this release is published, an independent post-publication audit must verify the generic path, retain evidence, run the canonical 19-gate completion contract for P-051 and P-057, and bind final completion records/handover before either roadmap item can move to `COMPLETE`.
