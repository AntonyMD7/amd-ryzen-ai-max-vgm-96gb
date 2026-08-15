# DAIS Public Build Status Ledger

**Status:** PUBLIC PROVING-GROUND LEDGER — NOT THE MASTER ROADMAP  
**Snapshot date:** 2026-08-15  
**Canonical opportunity register:** `DAIS_PUBLIC_BUILD_OPPORTUNITY_MASTER_ROADMAP_v1.0.md` in the DAIS canonical/library record.

This ledger records public source/reference progress without weakening the canonical completion contract. The master roadmap remains authoritative for stable IDs, names, priority and completion requirements.

## Portfolio state

| State | Count | Meaning |
|---|---:|---|
| COMPLETE | 0 | No opportunity currently satisfies the full canonical completion contract |
| IN PROGRESS | 227 | Every `P-001` through `P-227` has public source/reference evidence or a directly mapped public proving-ground implementation |
| BLOCKED | 0 | No item is globally blocked from further source work; individual completion gates remain |
| DEFERRED | 0 | None intentionally deferred |
| NOT STARTED | 0 | No opportunity remains without an initial public source/reference tranche |

**Important:** `227/227 started` does **not** mean `227/227 complete`. The current milestone is full portfolio **source/reference coverage** plus deeper acceptance/evidence work on all six flagship foundations.

## Flagship foundations

| ID | State | Current proving-ground evidence | Major remaining gates |
|---|---|---|---|
| F-01 SafeFix | IN PROGRESS | fail-closed lifecycle; marked file-only sandbox mutation; snapshot-before-write; exact rollback; PREPARED/COMMITTED/ROLLED_BACK journals; interruption recovery; recovery-corruption refusal; bounded 2–8-resource sequential bundle with visible partial-commit state and all-snapshot prevalidation before compensating rollback | dedicated distribution; governed native adapters; true group/power-loss atomicity or explicit native-transaction integration; representative real-world acceptance; release; external review |
| F-02 Universal System Doctor | IN PROGRESS | privacy-minimizing diagnostic layer; strict public schema; EN/ES accessible render; repeatable hosted Ubuntu plus cross-platform Ubuntu/Windows/macOS read-only acceptance with digest-bound evidence | representative physical hardware acceptance; bounded vendor adapters; dedicated distribution/release; independent review |
| F-03 Local AI Doctor | IN PROGRESS | readiness, accelerator, model-fit, setup, quantization, benchmark and local/cloud policy orchestration; loopback-only bounded Ollama adapter; real CI acceptance against pinned Ollama 0.32.5 and public `smollm:135m` with bounded inference and response-content non-retention | physical accelerator/model acceptance; additional backends/platforms; long-context/concurrency and offline evidence; dedicated distribution/release; independent review |
| F-04 Hardware Compatibility Commons | IN PROGRESS | compatibility schemas; VGM proving ground; privacy-safe intake validator; exact-context multi-report index preserving verified conflicts and refusing majority-vote-as-truth; bounded query/browse reference surface | dedicated commons/database; community ingestion/moderation; independent real reports; richer search/browse UX; release |
| F-05 Universal Evidence Standard | IN PROGRESS | schema/examples/validator/action; fail-honest in-toto/SLSA/OpenTelemetry/W3C PROV/SPDX/CycloneDX mappings; exact-byte Cosign verification; exact Sigstore keyless GitHub workflow identity/issuer; explicit transparency-log + RFC3161 timestamp material; signed authenticated in-toto Statement v1 carrying SLSA Provenance v1 semantics; exact signer-builder trust policy and negative controls | independent/external interoperability evidence; long-term trust-root/version archival + offline verification policy; independently assessed builder/security model; dedicated reusable distribution/release; external standards/security review |
| F-06 Accessible AI | IN PROGRESS | semantic multilingual reporting; static accessibility contracts; privacy-safe supporting evidence schema; pinned axe hosted EN/ES exact-artifact automated evidence; browser keyboard/reflow supporting acceptance with explicit non-conformance boundary | multiple real assistive-technology environments; 400% zoom/manual acceptance; disability-inclusive usability evidence; broader languages; dedicated distribution/release |

## Opportunity coverage register

All ranges below are **IN PROGRESS**. They are grouped by the public tranche carrying their initial implementation/reference evidence.

| IDs | Public evidence / tranche |
|---|---|
| P-001, P-017, P-018 | Beginner Tech Rescue: health/error/command explain-first interfaces |
| P-002, P-016 | Universal System Doctor / privacy-minimizing diagnostic reference |
| P-003–P-010 | Cross-platform system support planner: Windows/Linux/driver/BIOS/network/peripheral/compatibility/firmware plans |
| P-011–P-015 | Hardware upgrade and benchmark advisor reference |
| P-019–P-020 | Plan-only installation and configuration-audit contracts |
| P-021–P-024 | AI hardware, GPU/NPU, ROCm and CUDA readiness discovery |
| P-025 | AMD VGM repository itself: unified/variable-memory configuration proving ground |
| P-026–P-038 | Local AI Doctor ecosystem: model fit, setup, quantization, benchmark evidence, local/cloud/offline decisions |
| P-039–P-045 | Repository Doctor plus safe issue/PR/docs automation planning |
| P-046–P-050 | specialist-tool integration for Scorecard/Markdown/link/secret checks plus Universal Evidence validation Action |
| P-051–P-063 | release governance, contributor safety, community maintenance, license/dependency integration and GitHub agentic prefilters |
| P-064–P-076 | model publication/evaluation and privacy-first dataset stewardship |
| P-077–P-086 | least-privilege Workspace/API accessibility planner |
| P-087–P-100 | accessibility and inclusion reference layer |
| P-101–P-108 | offline and low-bandwidth reference layer |
| P-109–P-118, P-120 | education and digital-literacy reference layer |
| P-119 | public `learning-git` practical beginner Git/GitHub laboratory |
| P-121–P-133 | defensive cybersecurity, privacy and trust reference layer |
| P-134–P-147 | guardrailed health, medicine and emergency reference layer |
| P-148–P-155 | community, ministry and nonprofit reference layer |
| P-156–P-172 | agriculture, small-business and finance reference layer |
| P-173–P-182 | travel, civic and public-information reference layer |
| P-183–P-194 | science, research and environmental evidence reference layer |
| P-195–P-210 | AI agent interoperability, shared memory, governance, privacy routing, RAG, voice and workflow portability contracts |
| P-211–P-220 | SafeFix, Universal Evidence, automation/recovery, troubleshooting, attestation/fleet and compatibility foundations |
| P-221–P-227 | community evidence, troubleshooting knowledge graph, open compatibility/evidence, reference implementations, architecture kits and problem→public-solution intake |

## Latest promoted tranches

Every item below was merged only after its branch safety/test gates succeeded. A merge is source promotion, **not** roadmap completion.

| PR | Scope | Result |
|---|---|---|
| #23 | P-003–P-010 system support | MERGED / CI PASS |
| #24 | P-011–P-015 hardware upgrades/benchmark interpretation | MERGED / CI PASS |
| #25 | P-019–P-020 installation/configuration planning | MERGED / CI PASS |
| #26 | P-064/P-065/P-066/P-067/P-068/P-074/P-076 model ecosystem | MERGED / CI PASS |
| #27 | P-069/P-070/P-071/P-072/P-073/P-075 dataset stewardship | MERGED / CI PASS |
| #28 | P-077–P-086 Workspace/API accessibility | MERGED / CI PASS |
| #29 | P-087–P-100 accessibility/inclusion | MERGED / CI PASS |
| #30 | P-101–P-108 offline/low-bandwidth | MERGED / CI PASS |
| #31 | P-109–P-118/P-120 education/digital literacy | MERGED / CI PASS |
| #32 | P-121–P-133 cybersecurity/privacy/trust | MERGED / CI PASS |
| #33 | P-134–P-147 health/medicine/emergency | MERGED / CI PASS |
| #34 | P-148–P-155 community/ministry/nonprofit | MERGED / CI PASS |
| #35 | P-156–P-172 agriculture/business/finance | MERGED / CI PASS |
| #36 | P-173–P-182 travel/civic/public information | MERGED / CI PASS |
| #37 | P-183–P-194 science/research/environment | MERGED / CI PASS |
| #38 | P-195–P-210 AI agents/memory/governance | MERGED / CI PASS |
| #39 | P-211–P-227 infrastructure/fleet/evidence consolidation | MERGED / CI PASS |
| #40 | 227/227 source/reference status ledger | MERGED / CI PASS |
| #41 | F-05 standards interoperability mappings | MERGED / CI PASS |
| #42 | machine-checkable P-001–P-227 + F-01–F-06 coverage verifier | MERGED / CI PASS |
| #43 | F-01 disposable sandbox recovery acceptance | MERGED / CI PASS |
| #44 | F-02 hosted Ubuntu acceptance + F-06 static accessible-report evidence | MERGED / CI PASS |
| #45 | F-03 integrated Local AI Doctor orchestration | MERGED / CI PASS |
| #46 | F-04 privacy-safe compatibility intake | MERGED / CI PASS |
| #47 | F-06 supporting accessibility acceptance evidence protocol | MERGED / CI PASS |
| #48 | truthful flagship-depth status ledger | MERGED / CI PASS |
| #49 | F-06 pinned axe hosted automated supporting acceptance | MERGED / CI PASS |
| #50 | F-05 pinned Cosign exact-blob verification + tamper rejection | MERGED / CI PASS |
| #51 | F-02 hosted Ubuntu/Windows/macOS read-only acceptance matrix | MERGED / CI PASS |
| #52 | F-01 interruption journal + corrupted-recovery refusal | MERGED / CI PASS |
| #53 | F-03 loopback-only bounded Ollama acceptance adapter | MERGED / CI PASS |
| #54 | F-04 conflict-preserving exact-context compatibility index | MERGED / CI PASS |
| #55 | F-05 real disposable-key Cosign exact-byte signature acceptance | MERGED / CI PASS |
| #56 | project completion-record schema/auditor preserving 19-gate completion contract | MERGED / CI PASS |
| #57 | F-05 exact signer/transparency/timestamp/builder trust-policy evaluator | MERGED / CI PASS |
| #58 | F-01 bounded multi-resource partial-commit recovery acceptance | MERGED / CI PASS |
| #59 | P-025 completion-readiness audit: 17/19 evidenced, release/tag + final handover still open | MERGED / CI PASS |
| #60 | F-04 bounded compatibility query/browse reference surface | MERGED / CI PASS |
| #61 | F-06 browser keyboard/reflow supporting acceptance | MERGED / CI PASS |
| #62 | truthful depth update preserving 0 COMPLETE / 227 IN PROGRESS | MERGED / CI PASS |
| #63 | F-03 real pinned Ollama runtime + public small-model CI acceptance | MERGED / CI PASS |
| #64 | F-05 Sigstore keyless exact GitHub workflow identity/issuer acceptance | MERGED / CI PASS |
| #65 | F-05 explicit Sigstore transparency-log + RFC3161 timestamp material gate | MERGED / CI PASS |
| #66 | F-05 signed authenticated in-toto/SLSA provenance + exact signer-builder policy | MERGED / CI PASS |

Earlier merged PRs #1–#22 establish the six flagship foundations and the remaining P-001–P-133 proving-ground coverage. The `learning-git` public repository separately carries P-119 and complementary repository-quality exercises.

## Search-before-build adoption register

The portfolio explicitly prefers established upstreams where they already own the specialist problem. Current examples include:

- systems/hardware: osquery, hw-probe/Linux Hardware, vendor/OEM tooling;
- local AI: Ollama, llama.cpp, vLLM, LocalAI, MLPerf/llama-bench and other pinned specialist tools;
- repository/supply-chain: OpenSSF Scorecard, Gitleaks, markdownlint, lychee, OSV tooling, SPDX/REUSE;
- evidence/provenance/observability: in-toto Attestation Framework, SLSA, Sigstore/Cosign, OpenTelemetry, W3C PROV, SPDX/CycloneDX where applicable;
- research/data: Crossref, Zotero, ReproZip, RO-Crate, Frictionless Data Package;
- accessibility/public services: WCAG/WAI evaluation guidance, axe-core/axe CLI, Pa11y and mature public-service design systems;
- health information: NLM RxNorm, DailyMed/FDA SPL, NCBI Entrez/PubMed/PMC, HL7 FHIR as applicable;
- community/ministry: mature scheduling/CRM/event systems and licensed CrossWire/STEPBible ecosystems;
- farm/business/finance: farmOS, mature ERP/accounting/personal-finance systems where their exact license and deployment model fit;
- agent interoperability: A2A and MCP rather than another proprietary wire protocol.

## Portfolio-wide completion gaps

The following prevent a truthful `COMPLETE` state for most or all entries:

1. The current GitHub connector can develop within existing repositories but does not expose a create-repository action; many generic opportunities still need dedicated public distribution surfaces.
2. Each dedicated project needs its own explicit license decision, README/START-HERE/architecture/recovery/security/contribution surface as applicable.
3. Most projects still need representative real-world acceptance beyond hosted unit/contract CI; hosted OS matrices, browser automation, real CI model runtimes and protocol fixtures are supporting evidence, not physical-device/human acceptance.
4. High-stakes domains require independent domain review and jurisdiction/current-source validation.
5. Accessibility, assistive-technology and multilingual acceptance need broader human validation; automated/browser evidence is supporting evidence, not conformance proof.
6. Public examples/evidence must remain sanitized; credentials, private infrastructure, prompt/message content, patient/customer/donor personal data and other sensitive material are prohibited.
7. Versioned releases/tags, retained acceptance evidence and canonical completion handovers remain outstanding for most projects.
8. F-05 now has real exact signer identity, issuer, transparency/timestamp material and signed-provenance/builder-policy acceptance, but still lacks independent interoperability/security review, long-term trust-root/archive policy and a dedicated released distribution.

## Next phase

The portfolio has moved from **opportunity enumeration** to **227/227 source/reference coverage** and is now deepening the flagship foundations with repeatable evidence. The next dependency order is:

1. continue SafeFix durability/native-transaction integration and representative non-production recovery acceptance without overstating power-loss/group atomicity;
2. deepen Universal Evidence with independent interoperability, long-term verification/trust-root archival and external review while preserving the non-SLSA-level truth boundary of the current demo builder;
3. expand System Doctor, Local AI Doctor, Hardware Compatibility Commons and Accessible AI across representative physical hardware/backends/assistive technologies when bounded non-production acceptance is available;
4. extract flagship foundations and highest-impact opportunities into dedicated reusable distributions when repository creation becomes governed/available;
5. establish repeatable release/version/community-maintenance pipelines and independent/domain review;
6. only then promote individual roadmap items from `IN PROGRESS` to `COMPLETE` when every canonical gate is evidenced.
