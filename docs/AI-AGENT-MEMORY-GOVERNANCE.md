# AI Agents, Memory & Governance — Public Reference Layer

**Roadmap status:** `P-195` through `P-210` are **IN PROGRESS** reference work only.

## Search-before-build

Current open standards already solve important pieces of the interoperability problem. The Linux Foundation **Agent2Agent (A2A)** protocol defines agent-to-agent discovery, task collaboration and protocol bindings; its published specification identifies 1.0.0 as the latest released version at the time of this tranche. **Model Context Protocol (MCP)** standardizes model/agent connections to tools and resources and publishes both protocol schema and specification. They are complementary rather than reasons to create another wire protocol. **W3C PROV** provides a generic provenance model for entities, activities and agents. Existing DAIS Universal Evidence/OpenTelemetry-oriented work should map to these ecosystems rather than invent hidden proprietary lineage.

## Boundaries

- P-195/P-196: manifests declare capabilities/protocol candidates but contain no credentials and grant no execution.
- P-197: task handoffs bind IDs/artifact hashes; they do not delegate arbitrary execution or require disclosure of hidden reasoning.
- P-198/P-199/P-208: shared-memory/vault records carry content hashes, classification, source references and permissions; content is not embedded in public evidence and sensitive memory has no implicit cloud export.
- P-200: approval gates default to denial for consequential actions and record approval requirements separately from execution.
- P-201/P-202/P-203: audit/observability/provenance records omit secret values, prompts and hidden reasoning; operational transparency does not require exposing private chain-of-thought.
- P-204: budget records are local accounting/planning signals, not provider-billing truth or purchasing authority.
- P-205: sensitive/private data fails closed when an acceptable local route is unavailable; cloud permission never becomes an implicit fallback.
- P-206/P-210: workflow/no-code representations use portable capability steps and digests without vendor credentials or execution.
- P-207: RAG manifests bind corpus/index identity and require citations; source count/hash does not prove answer correctness.
- P-209: voice manifests declare languages/accessibility requirements without activating microphones, retaining audio or sending audio to cloud services.

## Security model

Interoperability must preserve authentication, authorization, least privilege, replay/idempotency rules, task/evidence identity, data classification and revocation. A protocol-compatible peer is not automatically trusted. Capability discovery is not authorization. Provenance is evidence for assessment, not a guarantee of truth. Observability should expose state transitions, tool calls, evidence identities, resource/cost metrics and policy decisions without requiring private model reasoning or sensitive content.

## Completion gaps

No mapped item is COMPLETE. Future gates include normative A2A/MCP/W3C-PROV interoperability fixtures, signed identity/authentication profiles, revocation and replay tests, portable schemas with version negotiation, real multi-agent acceptance, privacy/security threat modelling, accessibility/multilingual voice acceptance, releases, dedicated distribution and canonical completion records.
