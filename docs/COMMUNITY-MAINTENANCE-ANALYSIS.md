# Community Maintenance Analysis v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-053 Visual Git History Explainer`, `P-062 OSS Maintenance/Bus-Factor Dashboard`, and `P-063 Community Issue Deduplication/Triage System`.

## Search-before-build / terminology

GitHub already exposes repository activity/contributor graphs and can suggest potential duplicate issues while an issue is being written. CHAOSS defines the maintenance-concentration metric formerly called Bus Factor as **Contributor Absence Factor**. DAIS adopts that terminology and formula rather than inventing a new health score.

`scripts/community_maintenance_analysis.py` operates only on explicit sanitized JSON so the analysis can be reproduced without handing an autonomous tool write authority over public issues or contributor accounts.

## Visual Git history

The `history` mode converts supplied commit SHA/message/parent records into a Mermaid flowchart and reports roots/tips/merge commits visible **within that input**. It does not query `.git` or GitHub and does not require author identity. Missing parents/history are an explicit limitation.

## Contributor Absence Factor

The `absence` mode follows the CHAOSS >50% rule: sort supplied contribution counts descending and find the smallest number of contributors whose cumulative contributions exceed half of the supplied total.

The result is a concentration/risk conversation signal, not a score of a person's value or proof that a project is healthy/unhealthy. The contribution definition and time window must be stated upstream. Commit count alone can omit review, issue, documentation, governance, release and community work.

## Duplicate-issue prefilter

The `dedupe` mode uses transparent lexical Jaccard similarity over supplied public issue title/body text. It returns candidates only for **human review** and explicitly forbids automatic duplicate marking.

GitHub's own guidance supports duplicate workflows, but equivalence should be confirmed before a duplicate comment/mark/close action. Lexical similarity can miss semantic duplicates and can over-rank templates or boilerplate; a later semantic layer must retain this review gate.

## Privacy/data ethics

Use public/sanitized labels rather than contributor emails or private identity data. Do not use concentration metrics to shame, rank or make employment decisions about individuals. Issue analysis should exclude private/security reports unless it runs inside an appropriately protected boundary.

## Completion gaps

All mapped items remain **IN PROGRESS**. Completion requires governed GitHub metadata adapters, explicit time-window/contribution definitions, richer visual interactions/accessibility, CHAOSS-compatible metric provenance, issue semantic retrieval with evaluation datasets, duplicate false-positive measurement, human-confirmation UI, multilingual support, public release/distribution and canonical completion evidence.
