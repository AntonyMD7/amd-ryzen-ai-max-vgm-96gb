# DAIS Public Build Status Ledger

**Status:** PUBLIC PROVING-GROUND LEDGER — NOT THE MASTER ROADMAP  
**Snapshot date:** 2026-08-15  
**Canonical opportunity register:** `DAIS_PUBLIC_BUILD_OPPORTUNITY_MASTER_ROADMAP_v1.0.md` in the DAIS canonical/library record.

This file prevents public-build work from being mistaken for completion. The master roadmap remains authoritative for IDs, names, priority and the completion contract. A row in this ledger means source/reference work exists in this public proving ground; it does **not** change the master roadmap checkbox by itself.

## State rules

- `IN PROGRESS` — source/reference implementation exists, but at least one completion-contract gate remains.
- `COMPLETE` — reserved for an item whose full canonical completion contract is evidenced. **No item in this snapshot is COMPLETE.**
- IDs not listed below remain `NOT STARTED` in this proving-ground ledger unless another canonical evidence record says otherwise.

## Flagship foundations

| ID | State | Current proving-ground evidence | Major remaining gates |
|---|---|---|---|
| F-01 SafeFix | IN PROGRESS | `scripts/safefix_contract.py`, tests, VGM safety lifecycle | dedicated distribution; broader real-world acceptance; release; external review |
| F-02 Universal System Doctor | IN PROGRESS | cross-platform diagnostic/reference surfaces and beginner/system-doctor documentation | broader adapters; real hardware acceptance; release; accessibility/multilingual validation |
| F-03 Local AI Doctor | IN PROGRESS | readiness, model-fit, setup planning, benchmark evidence, local/cloud decision layers | integrated end-to-end product; backend/model acceptance; release; broader platforms |
| F-04 Hardware Compatibility Commons | IN PROGRESS | compatibility-report schema + VGM community proving ground | dedicated commons/database; community ingestion; independent reports; release |
| F-05 Universal Evidence Standard | IN PROGRESS | Universal Evidence JSON Schema + examples + validator/action | signed-attestation interoperability; external review; dedicated standard/release |
| F-06 Accessible AI | IN PROGRESS | plain-language/accessibility reference contracts and docs | real UI/assistive-tech acceptance; multilingual validation; reusable distribution |

## Opportunity items with reference work in this proving ground

| IDs | State | Evidence / tranche |
|---|---|---|
| P-001, P-017, P-018 | IN PROGRESS | beginner technology rescue, plain-English error/command explanation references |
| P-002, P-016, P-215 | IN PROGRESS | system-doctor/read-only diagnostic/troubleshooting framework references |
| P-009, P-021, P-022, P-023, P-024 | IN PROGRESS | hardware/AI readiness, accelerator/ROCm/CUDA/Metal discovery adapters |
| P-025 | IN PROGRESS | this AMD VGM repository is the hardware-specific unified/variable-memory configuration proving ground |
| P-026, P-027, P-032, P-033 | IN PROGRESS | model-to-hardware/model-memory/local-model recommendation reference layers |
| P-028, P-029, P-030 | IN PROGRESS | `local_ai_setup_planner.py` plan-only Ollama/llama.cpp/vLLM setup paths |
| P-031 | IN PROGRESS | `quantization_candidate_selector.py` evidence-first static-fit prefilter |
| P-034, P-035, P-036 | IN PROGRESS | Local AI benchmark evidence schema + fail-honest comparator + energy evidence classes |
| P-037, P-038 | IN PROGRESS | local-vs-cloud constraint prefilter + private/offline starter manifest |
| P-039, P-040, P-041, P-044, P-045, P-058, P-059 | IN PROGRESS | read-only Repository Doctor preflight; specialist-tool adoption boundary |
| P-050 | IN PROGRESS | Universal Evidence validator + reusable composite GitHub Action |
| P-087, P-091, P-093 | IN PROGRESS | accessibility/plain-language/multilingual reference layers |
| P-211, P-214 | IN PROGRESS | SafeFix/recovery-first mutation contracts |
| P-212 | IN PROGRESS | Universal Evidence schema/reference records |
| P-213 | IN PROGRESS | evidence-first automation plan contracts |
| P-220 | IN PROGRESS | hardware compatibility report schema + VGM-specific evidence workflow |

## Current-run merged evidence

The following tranches were promoted only after their branch CI succeeded:

| PR | Scope | Result |
|---|---|---|
| #9 | Correct canonical `P-025` mapping; preserve stable IDs | MERGED |
| #10 | P-028/P-029/P-030 setup planners | MERGED |
| #11 | P-031 quantization candidate selector | MERGED |
| #12 | P-034/P-035/P-036 benchmark evidence/comparator | MERGED |
| #13 | P-037/P-038 local-vs-cloud/offline starter | MERGED |
| #14 | P-039/P-040/P-041/P-044/P-045/P-058/P-059 Repository Doctor | MERGED |
| #15 | P-050 Evidence Validation Action | MERGED |

CI failures encountered during development were not hidden: the setup-planner and Repository Doctor tranches each failed tests during iteration and were corrected before merge. A merge means **source promotion only**, not roadmap completion.

## Search-before-build adoption register

Where mature upstream tools already own the core problem, DAIS should integrate/adopt rather than create inferior duplicates. Current decisions include:

- benchmark execution: `llama-bench` and MLPerf where their scenarios fit;
- local energy estimation: preserve tools such as CodeCarbon as an explicit `SOFTWARE_ESTIMATED` evidence class rather than direct-meter truth;
- local-AI runtimes/apps: build decision/safety layers around established upstreams such as Ollama, llama.cpp, vLLM, LocalAI and local-first/self-hosted applications rather than creating another inference engine;
- repository security health: OpenSSF Scorecard;
- secret scanning: Gitleaks or equivalent specialist scanner with redacted reporting;
- Markdown lint: markdownlint;
- broken-link validation: lychee or an equivalent mature checker;
- generic JSON Schema validation: mature JSON Schema tooling;
- signed artifact provenance/attestation: interoperate with in-toto/GitHub artifact attestations rather than treating schema validity as signed provenance.

## Known portfolio constraints

1. The current connector can create branches/files/PRs and merge CI-passing work in existing repositories, but no create-repository action is currently exposed. Generic foundations therefore remain in this public proving ground until a governed dedicated-repository path exists.
2. No device/production mutation is part of this public-build program.
3. Real-world hardware acceptance, accessibility/assistive-technology acceptance, multilingual validation, versioned releases and independent/community acceptance remain substantial completion gates for most items.
4. Public evidence must not contain credentials, private infrastructure identities, prompt/message content, sensitive documents or personal data.

## Next dependency order

The next GitHub/open-source tranche should prefer integration layers around the mature tools above (`P-046`–`P-049`, `P-051`–`P-057`, `P-060`–`P-063`) before moving deeper into the Hugging Face/data category. Each must remain fail-honest and must not convert an upstream tool signal into a stronger claim than the upstream evidence supports.
