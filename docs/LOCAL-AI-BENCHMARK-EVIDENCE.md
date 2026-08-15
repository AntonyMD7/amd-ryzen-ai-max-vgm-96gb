# Local AI Benchmark Evidence & Comparison v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-034 Reproducible Local-AI Benchmark Suite`, `P-035 Inference Performance Comparator`, and `P-036 AI Energy/Performance Benchmark Tool`; reusable by `F-03/P-027 Local AI Doctor`.

## Search-before-build decision

This project does not need another inference engine or benchmark kernel. Mature upstream systems already exist:

- `ggml-org/llama.cpp` ships `llama-bench`, including structured JSON/JSONL/CSV output;
- MLCommons publishes MLPerf Inference as a standardized inference benchmark suite with reference implementations and submission rules;
- CodeCarbon provides an open-source software-estimation path for local compute energy/emissions.

The public-build gap addressed here is evidence normalization and **refusal to compare non-equivalent runs**.

## Benchmark evidence schema

`schemas/local-ai-benchmark-v0.1.schema.json` records:

- producer/version/source revision;
- privacy-sanitized platform/accelerator class;
- exact backend version/revision and driver/runtime label;
- model ID, revision and SHA-256 artifact digest;
- quantization label;
- task, token counts, context, batch, repetitions and warmups;
- throughput and/or latency plus measurement source;
- a separately classified energy record;
- privacy declarations and limitations.

The sanitized example under `examples/` is explicitly **not live benchmark evidence**.

## Comparison gate

`scripts/benchmark_compare.py` runs no benchmark. It compares two existing records only when the fields that materially define the software/workload match. Differences in backend/version, model/revision/digest, quantization, task, prompt/generated tokens, context, batch, repetition or warmup settings cause a fail-honest refusal to rank performance.

When comparable records contain token throughput, higher tokens/second is reported. If throughput is unavailable and comparable latency is present, lower latency is reported. The tool does not claim statistical significance.

## Energy evidence

Energy is deliberately separate from performance and preserves its evidence class:

- `NOT_MEASURED`
- `DIRECT_METERED`
- `SOFTWARE_ESTIMATED`
- `EXTERNAL_REPORTED`

Numeric energy is compared only when the workload is otherwise comparable and both records declare the same non-empty energy status and the same measurement method. A CodeCarbon estimate therefore cannot silently become direct wall-meter evidence or be compared as though it were one.

## Privacy and security

Public records explicitly prohibit credentials, usernames, network addresses and prompt content. Hardware labels should be broad public-safe descriptions rather than machine identity. Raw evidence references may point to separately sanitized retained evidence but must never embed secrets.

This layer has no model loader, shell executor, package installer or energy sensor. It cannot mutate a device.

## Beginner view

> "Two speed numbers are only fair to compare when they ran the same model and test settings. If the settings differ, this tool will tell you instead of declaring a winner. Energy estimates also stay labelled as estimates."

## Engineer view

The schema is designed as an interchange layer. Future adapters can import `llama-bench`, MLPerf Client/Inference or other benchmark outputs while retaining upstream raw evidence and exact version identity. The comparator is intentionally conservative and deterministic.

## Completion gaps

All mapped roadmap items remain **IN PROGRESS**. Completion requires:

- upstream adapters with pinned fixture coverage, beginning with `llama-bench` structured output;
- repeated-run statistical treatment and uncertainty;
- representative cross-platform hardware acceptance;
- a published reference workload matrix rather than arbitrary local settings;
- energy adapters with explicit calibration/evidence semantics;
- accessibility and multilingual presentation;
- dedicated distribution or an intentional integrated-product decision;
- release/tag and canonical completion evidence.

MLPerf should be adopted for standardized scenarios where its scope fits rather than recreated. Lightweight local benchmarking should remain clearly distinct from an official MLPerf result/submission.
