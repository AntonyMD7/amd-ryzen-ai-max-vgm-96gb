# Offline, Low-Bandwidth & Intermittent-Connectivity Reference Layer

Status: **IN PROGRESS reference implementation** for `P-101` through `P-108`.

## Search before build

Offline knowledge distribution and synchronization already have mature ecosystems. **Kiwix** provides an established offline-content ecosystem around ZIM packages and readers/servers; **Syncthing** provides an established decentralized file-synchronization system. These are candidates to adopt/wrap where their licenses, threat model and UX fit the project. This tranche does not rebuild either engine.

The public reference layer instead defines small metadata/integrity contracts that can sit around mature tools and make offline state understandable to beginners and inspectable by engineers.

## P-101 — Offline Knowledge Kit

A package manifest records identity, version, SHA-256, license and provenance status. A package with missing rights/provenance evidence stays in review. The helper downloads or serves no content.

## P-102 — Low-Bandwidth Web Application Framework

The reference reports transparent project-policy budget warnings for initial bytes and JavaScript, plus whether a core no-script path and caching strategy exist. The numeric budgets are examples for a project to tune; they are not presented as universal web standards.

## P-103 / P-104 — Offline Education and Emergency References

The manifest makes source authority, version and review date visible offline. Emergency information must have an explicit refresh/replacement path because stale emergency guidance can be harmful. The module ships no reference corpus and makes no accuracy/currency certification.

## P-105 — Offline Translation Toolkit

A translation-pack manifest pins the local engine/ruleset artifact, language pair and digest. Real deployment still requires license review, human validation and a critical-term glossary. The reference performs no translation.

## P-106 — Offline Document Search/RAG

The plan requires corpus identity, document count, embedding-engine identity, chunk provenance, citations, index version, rebuild procedure and insufficient-evidence refusal. It reads no documents and creates no embeddings/index.

## P-107 — Progressive/Compressed Knowledge Distribution

The helper computes chunk count for a caller-selected package/chunk size and requires per-chunk digests, manifest integrity, resumability and atomic activation after verification. It does not predict compression ratio or write data.

## P-108 — Intermittent-Connectivity Synchronization

The plan explicitly refuses silent last-writer-wins behavior. Unknown common base requires reconciliation; simultaneous local/remote changes create a conflict that must be retained for policy or human review. Future adapters need atomic writes, retry/idempotency and content digests; timestamps alone must not become authority.

## Security / privacy

- no network operations;
- no file/content reads or writes;
- no synchronization execution;
- no content translation/RAG execution;
- no redistribution-rights inference;
- explicit integrity/provenance fields;
- conflict preservation rather than silent overwrites.

## Accessibility / global access

Offline packages should expose a human-readable version/date, plain-language update status, accessible navigation and language metadata without requiring persistent connectivity. Interfaces should degrade gracefully on modest devices and retain an engineer-level integrity manifest.

## Completion gaps

All mapped IDs remain IN PROGRESS. Completion requires real Kiwix/ZIM and/or equivalent package interoperability where appropriate, controlled Syncthing or other sync integration, browser/offline acceptance, actual package/update integrity tests, low-bandwidth measurements on constrained networks, multilingual and assistive-technology acceptance, emergency-source governance, licensing/data-rights review, releases, contribution paths and canonical completion records.
