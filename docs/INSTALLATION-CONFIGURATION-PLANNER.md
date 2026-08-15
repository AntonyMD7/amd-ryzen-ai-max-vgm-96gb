# Installation Assistant & Configuration Auditor

Status: **IN PROGRESS reference implementation** for:

- `P-019 Installation Assistant Framework`
- `P-020 Configuration Best-Practice Auditor`

## Search before build

Package managers, vendor installers, configuration-management systems and policy engines already exist. This project should not become another package ecosystem or universal configuration authority.

For policy-as-code, projects such as **Open Policy Agent (OPA)** are established general-purpose policy engines. Future larger deployments should adopt/wrap mature policy engines where justified rather than expanding this small reference evaluator into a competing language/runtime.

Platform package managers and official vendor installation documentation remain the authoritative source for actual installation commands, dependencies and supported versions.

## P-019: plan before install

The installation planner accepts only bounded identifiers plus:

- explicit package/tool name;
- platform;
- source authority identifier;
- explicit version;
- SHA-256 artifact identity;
- recovery-ready boolean;
- approval-granted boolean.

It emits **no install command**. Even when all review gates are true, the disposition is only `REVIEWABLE_MUTATION_PLAN`. Actual installation belongs in a separate governed SafeFix adapter using current platform/vendor instructions and fresh artifact verification.

This avoids common failure modes such as:

- silently installing `latest`;
- executing a copied pipe-to-shell command;
- losing artifact identity;
- treating download success as installation success;
- modifying a system before recovery and approval exist.

## P-020: policy facts, not secret-bearing configuration dumps

The configuration auditor consumes a small boolean fact map and a bounded list of rules. A rule can produce `PASS`, `REVIEW` or `UNKNOWN`.

`UNKNOWN` never becomes a pass merely because evidence is missing.

The reference implementation does not accept arbitrary configuration values, passwords, tokens, file bodies, registry exports or environment dumps. It therefore demonstrates the policy/evidence separation without creating a secret-ingestion surface.

## Beginner experience

The intended beginner result is something like:

> **Not ready to install yet.** A recovery path has not been confirmed. Nothing has been installed.

or:

> **Two checks need review and one setting is unknown.** This audit did not change your computer.

## Engineer experience

The machine record keeps policy evaluation and execution separate. A policy pass is not vendor support, security assurance or proof of a correct configuration. A future adapter should preserve the source and version of each policy rule so stale recommendations can be identified.

## Privacy and security

- no arbitrary command input;
- no commands emitted by the installation planner;
- no network access;
- no package installation;
- no service/configuration mutation;
- explicit version and artifact digest required;
- recovery + approval gates represented separately;
- configuration facts restricted to booleans;
- missing evidence represented as `UNKNOWN`;
- no secret values accepted.

## Recovery

The reference tools themselves are non-mutating and need no rollback. Any future installation or remediation executor must establish recovery **before** mutation and produce before/after evidence under the SafeFix lifecycle.

## Accessibility / multilingual path

The machine schema uses compact stable identifiers so the same outcome can be rendered in plain language, localized text, voice or engineer detail without changing policy truth. This tranche does not yet claim multilingual or assistive-technology acceptance.

## Completion gaps

Neither roadmap item is COMPLETE. Remaining gates include production-grade policy/source provenance, platform adapters, sandboxed real-world acceptance, accessible distribution, multilingual validation, release/version records, security/privacy/accessibility review, contribution workflows, known-limitations records and canonical completion evidence.
