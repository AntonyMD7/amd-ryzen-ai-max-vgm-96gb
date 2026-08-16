# DAIS Beginner-Safe PR Creator v0.7.0 — Release Candidate Notes

Roadmap ID: **P-052**

Release status: **CANDIDATE SOURCE — NOT YET PUBLISHED**.

## What ships

- reusable composite Action at `.github/actions/beginner-safe-pr`;
- network-free `plan` mode with deterministic SHA-256 lease;
- explicit five-check readiness contract;
- create mode requiring the exact reviewed plan hash and literal `CREATE_DRAFT_PR` confirmation;
- same-repository branch scope only;
- trusted `push` / `workflow_dispatch` create contexts only;
- exact base/head existence checks before mutation;
- duplicate-draft detection and idempotent reuse;
- hard-coded `draft=true` and `maintainer_can_modify=false`;
- no branch push, reviewer request, ready-for-review transition, approval, merge, close, label, collaborator or issue capability;
- bounded obvious-secret public-text refusal without echoing the value;
- sanitized error behavior that does not return token or API response bodies;
- adversarial tests, hosted plan-mode acceptance, beginner documentation, architecture/threat model and privacy-safe support path.

## GitHub authority boundary

GitHub remains the repository, branch, PR, permission and review authority. Create mode uses only the documented GitHub pull-request API after read-only same-repository preflight. The caller must explicitly grant the narrow PR-write permission and repository/organization policy may still prohibit workflow-created PRs.

## Important non-claims

A `READY_FOR_DRAFT_CREATE` plan is not proof that code is correct, tests passed, no secret exists, rollback is guaranteed, or the change is merge-ready. Safety flags are explicit caller attestations.

P-052 does not support forks, GitHub Enterprise Server, other forges, automatic branch pushes, reviewer assignment, approvals, ready transitions, merges or auto-closing. Obvious secret-pattern refusal is not comprehensive DLP; P-049 remains the dedicated repository secret-exposure product.

## Completion boundary

Publication alone will not mark P-052 COMPLETE. A released ref must create and independently verify a disposable real draft PR under the documented permission/event boundary, prove idempotent reuse and no source-file/branch mutation, retain sanitized evidence, and then pass the complete canonical completion record/handover and DAIS synchronization path.
