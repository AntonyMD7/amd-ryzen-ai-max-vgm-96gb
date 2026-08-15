# Local AI Doctor — exact-model Ollama runtime footprint acceptance

**Roadmap:** F-03 Local AI Doctor  
**Status:** IN PROGRESS  
**Acceptance environment:** disposable GitHub-hosted Ubuntu 24.04, loopback-only Ollama

## Why this tranche exists

The earlier F-03 real-Ollama acceptance proved that a pinned tiny model could be present and generate one bounded response on a pinned disposable Ollama runtime. That still left several facts conflated:

- stored model size is not the same as loaded runtime footprint;
- a generic memory estimate is not exact backend runtime evidence;
- a requested context is not proof of the maximum context a device can sustain;
- one observed token rate is not a performance characterization;
- a license string is not a legal compatibility determination;
- an Ollama model digest is not, by itself, upstream model provenance.

This tranche records those distinctions explicitly.

## Search-before-build

Ollama already exposes the required runtime-native evidence surfaces, so DAIS wraps them instead of estimating them from first principles:

- `GET /api/ps` reports currently loaded models and includes runtime `size`, `size_vram`, and `context_length` fields: https://docs.ollama.com/api/ps
- generation responses expose `load_duration`, prompt/evaluation token counts, and timing metrics: https://docs.ollama.com/api/usage
- `POST /api/show` exposes model details, capabilities, model metadata, and license text: https://docs.ollama.com/api-reference/show-model-details
- Ollama documents that larger context length increases memory requirements and recommends inspecting the loaded model state: https://docs.ollama.com/context-length

The chosen disposable acceptance model `smollm:135m` is published in Ollama's public library with Apache License 2.0 text, and the upstream Hugging Face model card also declares `apache-2.0`. Those independent public metadata sources support the *expected license-family fixture* used in CI, but they do not substitute for legal review or artifact provenance verification.

## Probe contract

`scripts/ollama_runtime_footprint_acceptance.py` accepts only an explicit loopback HTTP Ollama endpoint and an exact already-installed model identifier. Runtime-footprint acceptance additionally requires explicit `--allow-inference` authority.

The probe calls only:

1. `GET /api/tags` — prove the exact model is already installed and retain its Ollama digest/size;
2. `POST /api/show` — collect a narrow allowlist of model metadata and hash, but do not retain, license text;
3. `POST /api/generate` — run one tiny deterministic prompt with a caller-bounded `num_ctx`, no streaming, and temporary keep-alive so the model remains loaded for inspection;
4. `GET /api/ps` — observe the exact loaded model's runtime size, VRAM allocation field, context length, digest and bounded details.

The probe contains no `/api/pull`, `/api/create`, `/api/copy`, `/api/delete`, or `/api/push` path. The workflow—not the probe—downloads the explicit public acceptance model into the disposable runner before the probe starts.

## Evidence retained

### Exact model identity

- requested model name;
- installed Ollama digest;
- stored model size;
- loaded digest equality with the installed digest.

Digest equality is an Ollama-internal content identity check for the tested run. It does **not** prove that the Ollama artifact corresponds to a particular upstream Hugging Face commit or training provenance.

### Runtime footprint

- loaded `size_bytes`;
- loaded `size_vram_bytes`;
- loaded `context_length`;
- requested `num_ctx`;
- whether the observed loaded context equals the request exactly.

A `size_vram_bytes` value of zero is valid evidence on a CPU-only hosted runner. It must not be rewritten into an unsupported accelerator claim.

### Model metadata

Only bounded `format`, `family`, `parameter_size`, `quantization_level`, capabilities, and advertised context-length integers are retained.

License text itself is **not** retained. The probe records only:

- whether non-empty license metadata was present;
- its UTF-8 byte-derived SHA-256;
- character length;
- `license_text_retained=false`.

The CI acceptance separately checks that the disposable `smollm:135m` model's live `/api/show` license contains the expected Apache-license family and then deletes that raw response rather than uploading it.

### Inference usage metrics

The probe retains:

- total/load durations;
- prompt and output token counts;
- prompt/evaluation durations;
- arithmetic observed tokens-per-second values;
- SHA-256 of generated response text, never the response itself.

These are **single-run observations**, not benchmark results. `performance_characterized` remains false.

## Truth and safety boundary

A green acceptance means the exact model was loaded and the documented bounded fields were observed on that exact pinned Ollama/disposable-hosted run. It does **not** prove:

- representative Windows/macOS behavior;
- NVIDIA/AMD/Apple/NPU accelerator support;
- physical device memory capacity;
- maximum safe context length;
- sustained throughput/latency;
- model quality or task suitability;
- upstream model provenance;
- legal license compatibility;
- production readiness;
- F-03 completion.

Generated response text and license text are not retained. The probe allows no non-loopback network destination and no model-management mutation endpoint.

## Beginner interpretation

> “This exact small model really loaded in Ollama during the test. We recorded how much memory Ollama reported for that run, the context it actually loaded, and a hash of its license metadata. That is stronger than a guess, but it still does not mean every model will fit your computer or that this model is legally/technically suitable for your use.”

## Engineer interpretation

The useful distinction is between four evidence classes:

1. **stored artifact** — `/api/tags` digest and size;
2. **declared metadata** — `/api/show` details/capabilities/license/context metadata;
3. **executed workload** — one exact pinned generate call plus usage metrics;
4. **loaded runtime state** — `/api/ps` size/VRAM/context/digest after that call.

F-03 should only promote future claims when the evidence class actually supports the claim.

## Remaining F-03 gates

- representative Windows and macOS backend acceptance;
- representative accelerator lanes (NVIDIA, AMD/ROCm or Vulkan, Apple Metal, CPU and appropriate NPU paths);
- stronger upstream model provenance/license mapping to exact model artifacts;
- multiple pinned workload/context cases and real user-task acceptance;
- safe install/recovery integration with F-01;
- F-05 signed evidence binding for F-03 runtime artifacts;
- browser/mobile beginner UI and F-06 accessibility/multilingual human acceptance;
- reusable release/distribution, community review and canonical completion record.

F-03 remains **IN PROGRESS**.
