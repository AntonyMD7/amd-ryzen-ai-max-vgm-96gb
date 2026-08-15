# Supply-Chain Integration Plan v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-056 License Compliance Checker` and `P-060 Dependency Risk Summarizer`.

## Search-before-build decision

Do not create a new license engine or vulnerability database.

For licensing, the integration path should combine:

- **SPDX** identifiers/expressions and SBOM/licensing metadata standards;
- **REUSE** practices/tooling for machine-readable per-file copyright/license information;
- GitHub's repository-level license recognition/API for a coarse repository signal.

For dependencies, the integration path should combine:

- **GitHub Dependency Review** for pull-request dependency changes and policy enforcement;
- **OSV-Scanner** for broader open-source vulnerability scanning/remediation workflows.

`scripts/supply_chain_integration_plan.py` inventories only bounded local signals and emits this adoption plan. It does not execute any of the specialist tools.

## License-compliance boundary

A LICENSE filename alone does not prove every file/dependency can be distributed under one policy. SPDX expressions are needed for compound licensing, and vendored/third-party material must preserve its own notices/terms. Policy compatibility is organization/legal policy and must not be silently reduced to a generic pass/fail scanner claim.

The planner lexically reports SPDX markers and possible REUSE signals but does not claim full SPDX grammar validity or legal compatibility.

## Dependency-risk boundary

Manifest/lockfile presence is inventory only. A vulnerability scan needs a current database, supported ecosystem parser, exact dependency provenance and context. GitHub's own dependency-review documentation notes that source diffs still deserve review because dependency metadata may not capture every change/source.

A future report must preserve scanner/database version and unsupported/unknown status. `no findings` must never be rendered as `no dependency risk`.

## Security/privacy

The planner skips `.git` and common dependency/build/vendor directories, performs no network access, installs nothing and changes no repository file. Future vulnerability/license integrations should redact sensitive paths or private package coordinates when operating outside a public repository boundary.

## Beginner view

> "This project does not guess whether your licenses and dependencies are safe. It finds the files that matter, points to established tools and standards, and tells you what must still be checked."

## Completion gaps

Both roadmap items remain **IN PROGRESS**. Completion requires reviewed/pinned REUSE/SPDX/GitHub/OSV integrations, multi-ecosystem fixtures, license-expression/policy test cases, vulnerability false-positive/unsupported-state handling, SBOM/provenance integration, fork/untrusted-input threat tests, accessible/multilingual reporting, versioned distribution and canonical completion evidence.
