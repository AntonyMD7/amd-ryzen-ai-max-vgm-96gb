# Local AI Doctor Orchestration v0.2

Status: **IN PROGRESS — evidence-gated planning/integration layer**

Canonical roadmap mapping: **F-03 Local AI Doctor**, with direct reuse of P-021 through P-038 public reference work.

## Problem

A beginner asking “what AI can this computer run?” can easily receive an answer that silently mixes several different questions:

1. What hardware/runtime signals are actually observed?
2. Does a model's stored weight representation approximately fit a supplied memory budget?
3. Does the intended backend support the exact OS, architecture and accelerator today?
4. Will the exact model/backend/context fit at runtime?
5. Is performance useful for the intended task?
6. Is the local/cloud data path permitted?
7. Has installation or operation actually been proven?

Those questions must not collapse into a single unsupported “yes, it runs.”

## Search-before-build decision

Local AI Doctor is an orchestration/evidence project, not a replacement for mature runtime-native tools.

- **Ollama** publishes current hardware-support and platform documentation. Its runtime remains the authority for its own supported accelerators and scheduling behavior: https://docs.ollama.com/gpu
- **llama.cpp** now includes runtime fitting behavior and `llama-fit-params`, which can fit projected model/runtime parameters against free device memory. When llama.cpp is the target backend, that backend-aware evidence is stronger than a generic arithmetic estimate: https://github.com/ggml-org/llama.cpp/blob/master/tools/fit-params/README.md
- **Hugging Face Accelerate** provides `estimate-memory` for supported Hub models. Its documentation explicitly distinguishes loading-memory estimation from inference requirements: https://huggingface.co/docs/accelerate/en/usage_guides/model_size_estimator
- **vLLM** maintains platform- and accelerator-specific installation/quickstart documentation. Requirements are volatile enough that Local AI Doctor should link to current upstream guidance rather than freeze a permanent install matrix: https://docs.vllm.ai/en/latest/getting_started/quickstart/

The DAIS value is therefore to connect discovery, privacy policy, fit prefilters, backend setup planning and required acceptance evidence while preserving the difference between **observed**, **estimated**, **supported**, **tested**, and **production-ready**.

## Architecture

```text
Privacy-minimizing discovery
        ↓
Normalized machine facts
        ↓
Accelerator evidence gate ──────────────┐
        ↓                               │
Caller-supplied usable-memory evidence  │
        ↓                               │
Generic weight-memory prefilter         │
        ↓                               │
Local/cloud policy prefilter            │
        ↓                               │
Backend review plans                    │
        ↓                               │
Current upstream support review         │
        ↓                               │
Backend-native fit / exact model proof  │
        ↓                               │
Pinned workload acceptance              │
        ↓                               │
Evidence / release decision <───────────┘
```

`scripts/local_ai_doctor.py` is intentionally **PLAN_ONLY**. It composes existing repository modules but contains no network client, subprocess executor, installer, model loader, benchmark runner or configuration mutator.

## Critical truth boundary: memory

Local AI Doctor never promotes **total system RAM** into “usable accelerator memory.” This matters for discrete GPUs, unified-memory systems, reservation policies and backends whose actual allocation behavior differs from nominal capacity.

A generic weight-memory prefilter runs only when the caller supplies a separate `usable_memory_gib` evidence value. Even then:

- a fit result remains `PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION` or a similar bounded state;
- it does not model all KV cache, activations, graph/workspace allocations, multimodal components or backend overhead;
- it never sets `model_runnable=true`.

Backend-native fitting and a pinned workload remain mandatory for an operational claim.

## Critical truth boundary: backend presence

An installed backend is reported only as `PRESENT_NOT_ACCEPTED`. Presence does not mean:

- the service is healthy;
- the accelerator is being used;
- the model is compatible;
- the intended context fits;
- performance is acceptable;
- network exposure is safe.

Every backend review candidate has both `support_claimed=false` and `selection_rank_claimed=false`.

## Local/cloud privacy gate

The orchestration reuses the constraint-first local/cloud decision layer. Sensitive or regulated data with no approved remote API path never gains an implicit cloud fallback. An offline requirement forces the local-only architecture lane, but Local AI Doctor will still report a blocker until exact local workload readiness is verified.

## Beginner view

> Local AI Doctor can now combine the safe checks into one answer: what we actually know about the machine, whether the model looks too large at a basic level, which local AI tools should be reviewed, and exactly what still has to be tested. It will not tell you a model definitely works until a real model/backend test proves it.

## Engineer view

The orchestrator consumes normalized, deliberately low-identity facts. It can also ingest the v0.1 privacy-minimizing discovery record, but it checks the discovery record's read-only/privacy/mutation declarations before using it. Total memory from that record is retained as an observation only and is not reused as accelerator-usable capacity.

The output contains explicit false claims for model runnability, exact-hardware backend support, performance, quality, installation, downloads, cloud approval and production readiness. This makes later promotion evidence additive rather than retroactively correcting an overclaim.

## Safety and privacy review

- No model or dataset content is read.
- No model is downloaded or loaded.
- No provider is contacted.
- No package, service, driver or configuration is changed.
- No benchmark is executed.
- No hostname, username, network address, credential or user document is required.
- Invalid normalized labels fail closed.
- Discovery inputs whose privacy or mutation declarations are not all false are rejected.

## Accessibility / multilingual path

The v0.2 module is a machine/planning layer, not the final user interface. Its structured states are intentionally suitable for rendering through F-06 Beginner / Intermediate / Engineer views without hiding uncertainty. Final user-facing strings must be localized and tested rather than treating machine state labels as the accessible interface.

## Acceptance in this tranche

The test suite proves, using synthetic/sanitized facts:

- missing usable-memory evidence stays `DISCOVERY_REQUIRED`;
- total system RAM is not silently promoted to accelerator memory;
- a positive generic fit still requires exact backend/workload acceptance;
- obviously insufficient supplied capacity rejects only the bounded fit prefilter;
- regulated/offline workloads never gain cloud fallback;
- backend presence does not become support evidence;
- native-Windows vLLM planning remains plan-only and does not claim support;
- privacy/mutation contract violations fail closed;
- no network/subprocess executor exists in the orchestration layer.

## What remains before F-03 can be COMPLETE

F-03 remains **IN PROGRESS**. Material completion gates include:

- dedicated public distribution surface and explicit release/version record;
- current-platform acceptance on representative Windows, Linux and macOS systems;
- representative NVIDIA, AMD/ROCm or Vulkan, Apple Metal, CPU and where appropriate NPU acceptance lanes;
- exact backend-native model-fit evidence;
- pinned real-model inference acceptance with context/KV/workspace evidence;
- model provenance/license verification;
- performance/quality acceptance for representative tasks rather than generic benchmark-only claims;
- safe installation/recovery integration through F-01;
- browser/mobile beginner interface;
- accessibility and multilingual human acceptance;
- community review and canonical completion record.

No device or production mutation is authorized by this tranche.
