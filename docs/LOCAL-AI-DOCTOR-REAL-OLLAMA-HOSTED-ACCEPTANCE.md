# Local AI Doctor — Real Ollama Hosted Acceptance v0.1

Status: **F-03 IN PROGRESS — real ephemeral runtime/model acceptance, not physical-device or production acceptance**

This tranche moves the Local AI Doctor beyond mock protocol fixtures by launching a real pinned Ollama runtime on a disposable GitHub-hosted Ubuntu runner, installing one deliberately small public model, and exercising the existing bounded loopback probe against that runtime.

## Search-before-build

Ollama already provides the local runtime, model distribution, and HTTP API. DAIS does not build another model server.

The official Ollama documentation defines:

- Linux installation and version pinning with `OLLAMA_VERSION`;
- loopback API access, including `/api/version`, `/api/tags`, and `/api/generate`;
- `keep_alive` behavior for generate/chat requests.

The official Ollama model library publishes `smollm:135m` as a small 135M-parameter model (about 92 MB in the library listing), which is suitable for a short CPU-hosted acceptance run without turning CI into a performance benchmark.

## Runtime pinning

The workflow pins:

```text
Ollama = 0.32.5
```

It downloads the `install.sh` asset from the official `ollama/ollama` GitHub release for `v0.32.5` and verifies the release-published SHA-256 before execution:

```text
25f64b810b947145095956533e1bdf56eacea2673c55a7e586be4515fc882c9f
```

The acceptance then requires `/api/version` to report the expected runtime version.

## Model boundary

The workflow downloads:

```text
smollm:135m
```

only into the disposable hosted runner. The Local AI Doctor probe itself remains incapable of pulling/creating/deleting/pushing models and reports `model_download_allowed=false`.

The exact observed model digest and size are retained in the bounded probe/tags evidence. The model **tag is not treated as an immutable content pin**; a future tranche should bind an acceptance policy to an immutable model artifact/digest if Ollama's supported distribution semantics make that reproducible across environments.

## Acceptance sequence

```text
pinned official Ollama installer asset
        ↓ SHA-256 verify
install Ollama 0.32.5
        ↓
serve on 127.0.0.1:11434 only
        ↓
GET /api/version
        ↓ exact version assertion
pull smollm:135m into ephemeral runner
        ↓
GET /api/tags
        ↓ exact tag present + observed digest/size
bounded Local AI Doctor read-only probe
        ↓
one bounded /api/generate inference
        ↓
hash response text; do not retain response text
        ↓
unload model with keep_alive=0
        ↓
retain sanitized acceptance JSON
```

The generated response content is never persisted by the probe; only its SHA-256 and bounded runtime metrics are retained.

## What a PASS proves

A successful hosted run proves that, in that disposable Ubuntu runner:

- a real pinned Ollama version launched successfully;
- the official loopback API was reachable;
- the named small model was present after an explicit CI-only pull;
- the existing bounded probe correctly discovered that model;
- one real bounded generate request completed through the probe;
- the probe retained a response digest rather than generated text;
- the probe did not gain model-download/create/delete/push capability.

## What it does NOT prove

A successful run does not prove:

- GPU/accelerator support;
- performance on AMD, NVIDIA, Apple, Intel, or any user-owned device;
- model quality, factuality, safety, instruction following, or task suitability;
- that the mutable model tag will always identify the same artifact;
- thermal, memory, power, long-context, concurrency, or sustained-load behavior;
- offline readiness after a clean installation;
- Windows/macOS runtime behavior;
- production readiness.

The existing probe therefore keeps `accelerator_support_verified`, `model_quality_verified`, `performance_characterized`, and `production_ready` false.

## Privacy and safety

The workload uses a fixed non-private prompt. No user prompt, message, corpus, credential, account token, device identifier, private model, or production endpoint is involved.

Only a loopback endpoint is accepted by the probe. Raw Ollama server logs are not uploaded; the artifact contains only a boolean summary of whether a log existed.

## F-03 progression

F-03 now has:

- deterministic mock/protocol tests;
- a bounded loopback-only Ollama adapter;
- a real pinned Ollama hosted runtime acceptance path;
- a real small-model bounded inference acceptance path that retains no generated text.

F-03 remains **IN PROGRESS**. Highest-value remaining evidence includes immutable model-artifact pinning where practical, representative physical hardware/model workloads, accelerator-specific truth, additional backend adapters, offline/recovery acceptance, dedicated distribution/release, accessibility/security review of the final user-facing surface, and canonical completion handover.
