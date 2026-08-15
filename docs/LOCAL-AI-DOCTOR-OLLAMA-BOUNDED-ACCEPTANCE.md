# Local AI Doctor bounded Ollama acceptance v0.3

Status: **IN PROGRESS — bounded backend acceptance adapter**  
Canonical foundation: **F-03 Local AI Doctor**.

## Search-before-build decision

Ollama already owns its runtime and API. DAIS does not reimplement an inference server. Current Ollama documentation defines a local API at `http://localhost:11434/api`, including `GET /api/version`, `GET /api/tags`, and `POST /api/generate`; non-streaming generation is supported by setting `stream: false`.

This tranche therefore adds a narrow **acceptance adapter around Ollama's existing API**, not another backend.

## Default mode

The default probe is read-only inventory over explicit loopback HTTP only:

- `GET /api/version`;
- `GET /api/tags`.

It records the runtime version and model count. It does not retain the full local model inventory. When the caller supplies an exact model identifier, the public evidence records only whether that exact identifier is present plus its reported digest/size when available.

## Explicit inference mode

Inference is disabled unless `--allow-inference` and an exact model identifier are both supplied.

Even then:

1. the model must already be present in `/api/tags`;
2. the adapter refuses to pull/download a missing model;
3. it sends one fixed tiny prompt to `/api/generate`;
4. `stream` is false;
5. `keep_alive` is zero to avoid intentionally retaining the model after the request;
6. the generated text is **not retained** in the evidence record; only its SHA-256 and bounded runtime metrics are retained.

The adapter contains no `/api/pull`, `/api/create`, `/api/delete`, `/api/push` or `/api/copy` path.

## Network boundary

Only `http://127.0.0.1`, `http://localhost`, or `http://[::1]` style loopback endpoints are accepted. HTTPS/cloud endpoints, credentials embedded in URLs, query strings and non-loopback hosts fail before the request is made.

This means the adapter cannot silently fall back to Ollama cloud or another remote provider.

## Acceptance semantics

A successful inventory probe proves only that the expected Ollama loopback API contract responded and that the observed version/tags shape was usable.

A successful explicit inference probe proves only that the already-installed exact model completed the tiny bounded request through that specific Ollama runtime. It still does not establish:

- accelerator support correctness;
- broader context-length/workload fit;
- model quality;
- sustained performance;
- thermal/stability behavior;
- production service exposure/authentication safety;
- production readiness.

## CI testing

Hosted CI uses a loopback mock that implements only the documented endpoints needed by this adapter. That verifies request allowlisting, non-loopback refusal, exact model matching, missing-model refusal, fixed bounded inference payload and generated-text non-retention. **The mock is protocol conformance only and is not real Ollama acceptance.**

The next F-03 gate is to run this adapter against an actual pinned Ollama version and an already-present, license-reviewed test model on representative non-production hardware, retaining the exact model digest/backend version and bounded evidence.
