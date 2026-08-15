# Local-vs-Cloud Decision & Private Offline Starter v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-037 Local-vs-Cloud AI Decision Assistant` and `P-038 Private/Offline AI Starter Kit`; reusable by `F-03/P-027 Local AI Doctor`.

## Search-before-build decision

A private/offline starter should not become another monolithic local-AI platform. Mature upstream projects already cover major execution/UI layers. Current examples include Ollama for local model runtime/API, LocalAI as an open-source local API engine, and AnythingLLM as a local-first/self-hosted chat/RAG application. AnythingLLM's self-hosted terms explicitly describe an air-gapped mode when local model/vector providers are used.

This tranche therefore builds only the missing **decision and architecture-manifest layer**. It does not fork or replace those projects.

## Local-vs-cloud decision assistant

`scripts/local_cloud_decision.py decide` takes explicit constraints rather than hidden preferences:

- data sensitivity;
- whether offline operation is mandatory;
- whether local hardware readiness is already verified;
- whether remote APIs are permitted by the caller's policy;
- low/intermittent bandwidth;
- availability priority.

It emits one architecture lane such as `LOCAL_ONLY_REQUIRED`, `LOCAL_PREFERRED`, `HYBRID_CANDIDATE`, or `EVALUATE_LOCAL_AND_CLOUD`, plus reasons, blockers and required next checks.

This is a prefilter, not legal/compliance/financial advice and not a provider recommendation. Provider pricing, retention/training policy, regional availability and security controls are volatile and must be verified at selection time.

Sensitive/regulated data does not get an automatic cloud fallback merely because cloud could improve availability. Hybrid designs must preserve the data-class boundary during failure.

## Private/offline starter manifest

The `offline-starter` mode generates a **manifest only** for a chosen local runtime label and interface. It can include a local document-RAG role, but it deliberately says `adopt-or-wrap-existing-local-first-project` rather than building another RAG stack.

The acceptance checklist includes:

1. core prompt/response works after external connectivity is removed;
2. runtime binds only to the intended local/trusted interface;
3. no automatic cloud fallback exists for restricted data;
4. model provenance/license is recorded;
5. a pinned local workload is verified;
6. backup/recovery for user documents/configuration is documented.

## Privacy boundary

"Local" and "self-hosted" are deployment properties to verify. A product can run inference locally while still offering update checks, model catalogs, telemetry or optional connectors. The manifest therefore requires inspection of outbound behavior and optional integrations before calling a deployment private/offline.

The planner itself performs no network requests, data uploads, model loads, installation, firewall changes, exposure changes or service starts.

## Beginner view

> "Tell me whether this AI must stay on my computer, could use the cloud, or should use both. I will show why, what is still unknown, and what must be tested before we trust the setup."

## Completion gaps

Both roadmap items remain **IN PROGRESS**. Completion requires:

- current provider-policy/pricing adapters for P-037 with dated evidence rather than cached claims;
- workload quality/latency/cost measurements on representative local and cloud paths;
- a policy engine able to express organization-specific approved data classes/providers;
- reference offline deployments using at least two upstream local stacks;
- verified no-network acceptance and outbound-connection inspection;
- recovery/backup exercises;
- accessibility and multilingual validation;
- dedicated distribution or deliberate integration decision;
- versioned release and canonical completion records.
