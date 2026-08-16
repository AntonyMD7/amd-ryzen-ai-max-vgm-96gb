# DAIS Contributor Onboarding Assistant v0.9.1

Roadmap ID: **P-054 — Contributor Onboarding Bot**

## Patch purpose

`v0.9.1` is the completion-candidate patch for P-054. The earlier `v0.9.0` release published successfully at its exact reviewed source, but its deliberately stronger released-ref acceptance exposed a multilingual output-isolation defect and an incorrect acceptance assertion. `v0.9.0` therefore remains historical and is **not** completion evidence.

## Fixed

- English and Spanish Action invocations now use distinct runner-temporary output directories, preventing one language invocation from overwriting another invocation's report/guide path before verification.
- Hosted source acceptance now exercises English, repeated English and Spanish in one job and requires distinct EN/ES output paths, repeated-EN deterministic digest identity, shared technical status/missing-required truth, clean consumer Git state and byte-identical README input.
- The patch release verifier compares `missing-required-count` at the Action-output layer and compares `missing_required` arrays inside the JSON report, matching the actual contract.
- Implementation version is `0.9.1` and the failure/fix is documented in beginner and engineering guidance.

## Product boundary

The product remains a read-only local contributor-onboarding audit and EN/ES guide. It does not call the GitHub API, post comments/issues, add labels, invite collaborators, execute repository code, mutate the repository, verify GitHub Community Standards server state, certify policy correctness, guarantee contributor experience, or claim WCAG conformance.

## Exact release source

This patch release is governed against exact source commit:

`082b41527f016058ff8c199b43beaca3e716c390`

That canonical-main commit contains the language-isolation fix, passing source-level regression acceptance, and these patch release notes. The public tag must resolve exactly to this commit.

## Completion boundary

Publishing `v0.9.1` is not sufficient for P-054 completion. The released `@v0.9.1` Action must independently pass pinned real-public EN/EN-repeat/ES consumer acceptance, evidence must be retained, and the canonical 19-gate completion record and final handover must pass fresh post-merge verification before P-054 can become COMPLETE.
