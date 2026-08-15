# Evidence-First Runbooks — Public Reference v0.1

Roadmap mapping:

- `P-213 Evidence-First Automation Library` — **IN PROGRESS**
- `P-214 Recovery-First Mutation Framework` — **IN PROGRESS**

`P-020` is **Configuration Best-Practice Auditor** in the canonical roadmap and is intentionally not claimed by this tranche.

## Search-before-build

Mature runbook/automation platforms already exist, including **Rundeck** and configuration-management/orchestration ecosystems. This reference does not attempt to replace their execution engines, schedulers, inventories, credential systems or plugin ecosystems.

The gap explored here is deliberately smaller and composable: a machine-readable plan contract that can sit **in front of** an execution engine and make evidence, recovery, approval and acceptance requirements reviewable before anything runs.

## Core rule

> A runbook is a plan. A validated runbook is still **not evidence that any step executed or succeeded**.

Execution and evidence are separate concerns.

## Automation-plan schema

`schemas/automation-plan-v0.1.schema.json` captures:

- plan ID/title/roadmap IDs;
- mode: `READ_ONLY` or `MUTATING`;
- subject/environment and explicit exclusions;
- ordered lifecycle steps;
- step classification: `READ_ONLY`, `MUTATING`, or `HUMAN_GATE`;
- command/reference pointers without executing them;
- expected evidence per step;
- timeout and idempotency metadata;
- acceptance criteria;
- evidence schema/retention policy;
- rollback readiness;
- approval/authorization state;
- known limitations.

For a `MUTATING` plan, schema validation fails unless recovery is required+established with a procedure reference and explicit approval is required+present with an authorization reference.

## Runbook generator

`scripts/runbook_generator.py`:

1. loads the plan and JSON Schema;
2. validates structural safety gates;
3. enforces lifecycle rules beyond basic schema shape;
4. renders reviewable Markdown;
5. **never executes `command_ref` values**.

Additional lifecycle checks require:

- every plan to include `DISCOVER` and `ATTEST`;
- a READ_ONLY plan to contain no MUTATING step;
- a MUTATING plan to include an explicitly MUTATING step;
- mutating lifecycle order: `PREFLIGHT` before `APPROVE` before `MUTATE` before `ATTEST`.

## Recovery-first mutation

The recovery contract is established **before** the mutation, not invented afterward.

A completion-grade executor built around this plan should additionally prove:

- pre-change state captured;
- backup/snapshot/rollback procedure actually usable;
- mutation target and scope re-verified immediately before action;
- lost connection does not imply failure or success;
- retries are forbidden or explicitly idempotent unless evidence says otherwise;
- post-change state independently re-read;
- rollback is exercised in test/staging where feasible;
- evidence is retained without secrets.

The v0.1 runbook generator itself does not perform any of those actions; it only validates that the plan declares the required contract.

## Evidence-first automation

Each step lists `expected_evidence`. The plan points to the Universal Evidence schema rather than embedding ad-hoc success prose.

This makes it possible for a future executor to enforce:

```text
PLAN
  -> PRECHECK
  -> AUTHORIZATION
  -> EXECUTION
  -> INDEPENDENT VERIFICATION
  -> ACCEPTANCE
  -> EVIDENCE RECORD
```

instead of:

```text
run command -> assume success because exit code was zero
```

## Beginner view

A generated runbook puts the mode, environment, exclusions, steps, evidence and limitations into one document. Mutating plans display approval and recovery state before the steps.

A beginner should be able to answer:

- Will this plan change anything?
- What is excluded?
- What must be backed up first?
- Who approved the change?
- How will success be checked afterward?
- Where is the evidence?

## Security/privacy

- secret values are forbidden in retained evidence by schema;
- `command_ref` is treated as inert text/reference by the renderer;
- the generator makes no network requests;
- no credential provider is implemented;
- no arbitrary command executor is implemented;
- plans should reference sanitized evidence rather than paste sensitive output.

## Completion gaps

No mapped project is COMPLETE. Remaining work includes a dedicated public package/repository, explicit reusable license decision, signed/versioned plan/evidence formats, adapters for mature orchestration engines, robust command-reference policy, cross-platform execution sandboxing, capability leases, idempotency/retry enforcement, rollback drills, real-world acceptance, accessibility/multilingual runbook presentation, releases/tags and canonical completion evidence.
