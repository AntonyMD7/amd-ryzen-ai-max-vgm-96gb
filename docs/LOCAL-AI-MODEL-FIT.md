# Local AI Model-Fit Prefilter v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `F-03 Local AI Doctor`, `P-026 Model-to-Hardware Recommendation Engine`, `P-032 Model VRAM/RAM Calculator`, and `P-033 Local Model Selection Assistant`.

## Purpose

A beginner often wants one answer: **"Will this model fit on my machine?"**

A responsible tool must not turn a rough parameter-count calculation into a run guarantee. This reference implementation provides an offline arithmetic prefilter that can reject obviously impossible fits and identify candidates that still require backend-native validation.

It does not download models, inspect private files, allocate accelerator memory, install runtimes, benchmark inference, or select a model on the user's behalf.

## Search-before-build decision

This repository does **not** attempt to replace mature backend-aware tools.

- Hugging Face Accelerate provides `accelerate estimate-memory` for supported Hub models and explicitly distinguishes model-loading memory from full inference memory.
- `llama.cpp` provides `llama-fit-params`, which can fit projected runtime parameters to currently available device memory for an actual GGUF model/backend combination.
- Ollama publishes backend/hardware support information that should be consulted when deciding whether a detected accelerator/runtime combination is supported.

Our gap is narrower: a dependency-free, no-network, no-model-download prefilter that can be embedded into beginner-safe diagnostics before a backend-specific tool is available.

## Calculation contract

For a user-supplied parameter count `P` and nominal quantization bit width `b`:

```text
raw_weight_bytes = P * 1,000,000,000 * b / 8
estimated_weight_bytes = raw_weight_bytes * (1 + structural_overhead)
conservative_required = estimated_weight_bytes * (1 + runtime_headroom)
```

Defaults:

- structural overhead: 5%
- generic runtime headroom: 20%

Those defaults are **heuristics**, not backend truth. Real quantization formats can include scales, metadata and tensors with mixed precision. Real inference additionally consumes KV cache, activation/workspace memory and backend-specific allocations.

## Status vocabulary

`CAPACITY_NOT_SUPPLIED`
: Arithmetic estimate only; no capacity comparison was requested.

`DOES_NOT_FIT_ESTIMATED_WEIGHTS`
: Available capacity is below the estimated stored weights. This candidate should be rejected unless a materially different quantization/offload strategy is used.

`BORDERLINE_REQUIRES_BACKEND_VALIDATION`
: Estimated weights fit, but the generic headroom does not. Treat as uncertain.

`PREFILTER_FIT_REQUIRES_BACKEND_VALIDATION`
: The arithmetic prefilter has headroom, but this is **not** a claim that the model will run.

Every result includes `guarantee: false`.

## Beginner example

```bash
python scripts/model_memory_estimator.py \
  --params-billions 7 \
  --bits 4 \
  --available-gib 16
```

Read the `fit_status` and `limitations` fields. If the result says the candidate passes the prefilter, the next step is still to validate the exact model with the target backend.

## Engineer path

For a real model/backend combination, prefer evidence in this order:

1. exact model artifact identity/digest;
2. backend-native memory estimator or fit utility;
3. actual load attempt under controlled conditions;
4. pinned inference benchmark;
5. observed peak memory and failure/recovery evidence.

The Local AI Doctor should eventually combine the read-only hardware collector, backend support tables, exact model metadata, backend-native fit evidence and benchmark results. This arithmetic layer is only the earliest filter.

## Privacy and safety

The estimator accepts numeric arguments only. It does not read usernames, hostnames, environment values, network addresses, credentials, model files or process state. It performs no network access and no mutation.

Do not use the estimator to justify buying hardware, modifying firmware/memory allocation, or deploying a workload without exact-model/backend evidence.

## Completion gaps

The mapped roadmap items remain **IN PROGRESS**. Completion still requires a dedicated public distribution surface, exact-model metadata adapters, backend support mapping, acceptance on multiple hardware classes, accessible/browser UX, multilingual validation, release/tag evidence, and canonical completion records.
