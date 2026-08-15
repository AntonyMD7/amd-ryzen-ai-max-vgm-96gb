# Quantization Candidate Selection v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-031 Quantization Recommendation Assistant`; reusable by `P-026 Model-to-Hardware Recommendation Engine`, `P-032 Model VRAM/RAM Calculator`, `P-033 Local Model Selection Assistant`, and `F-03/P-027 Local AI Doctor`.

## Scope

This project does **not** invent a quantization scheme, quantize a model, or claim that one quantization is universally better than another. Mature runtimes such as `llama.cpp` already provide quantization tooling and support multiple quantized model formats. The public-build gap addressed here is narrower: help a user compare candidate artifacts without pretending that a filename or file size proves runtime fit or answer quality.

## Evidence-first input

The selector accepts a JSON array where each candidate has:

- a unique opaque `name`;
- observed positive `artifact_size_bytes`;
- a non-empty `source`/provenance label;
- optionally, an integer `quality_rank` supplied by the caller or a trusted evaluation source.

The tool deliberately treats quantization names as opaque labels. It does not encode a permanent table saying, for example, that one named quantization is always higher quality than another.

## Selection rule

The user provides available memory and an explicit reserve fraction. The selector calculates a **static artifact budget** and separates candidates that fit that budget from those that do not.

That is only a prefilter. Model artifact size is not runtime RAM/VRAM consumption. Runtime memory can also include KV cache, context-dependent allocations, graph/workspace buffers and backend/offload overhead.

If a source-supplied integer quality rank exists, the best-ranked statically fitting artifact is surfaced. Otherwise the smallest statically fitting artifact is surfaced as the conservative starting point. Every recommendation carries `guarantee: false`.

## Example

```text
python scripts/quantization_candidate_selector.py candidates.json \
  --available-memory-gib 24 \
  --reserve-fraction 0.20
```

No model is loaded or downloaded by this command.

## Search-before-build / upstream boundary

`ggml-org/llama.cpp` already ships quantization tooling and supports a wide range of quantized GGUF models/backends. This reference layer does not duplicate that quantizer or freeze its evolving option list. Exact candidate creation and backend-format support belong to the current upstream project and model publisher.

The selector is useful before those runtime-specific checks because it can reason over observed artifact metadata without requiring a model download or GPU allocation.

## Security and privacy

The selector is offline and dependency-free. It receives only user-supplied candidate metadata and an explicit memory budget. It does not inspect user files other than the selected JSON input, contact model hubs, access credentials, read network state, start a runtime, or mutate configuration.

## Required verification after selection

1. Verify artifact provenance and license at the source.
2. Verify the exact backend accepts the model format/quantization.
3. Measure actual runtime RAM/VRAM consumption.
4. Run a pinned task/quality evaluation before comparing output quality.
5. Run a pinned performance benchmark before making speed claims.

## Beginner view

> "This model file fits inside the memory budget you gave me, with the reserve you requested. That does **not** prove it will run. We still need to test the real model with the real AI program."

## Completion gaps

`P-031` remains **IN PROGRESS**. Completion requires model-hub metadata adapters with provenance, representative backend/model acceptance, quality-evaluation integrations rather than arbitrary ranks, accessibility/multilingual validation, dedicated distribution or an intentional integrated-product decision, release/tag evidence, and a canonical completion record.
