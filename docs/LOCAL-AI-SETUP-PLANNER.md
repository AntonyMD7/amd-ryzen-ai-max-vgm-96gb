# Local AI Setup Planner v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-028 One-Click Ollama Setup Assistant`, `P-029 llama.cpp Setup Assistant`, and `P-030 vLLM Setup Assistant`; reusable by `F-03 Local AI Doctor` and `P-027 Local AI Doctor`.

This tranche intentionally stops before the word **install** becomes an action. It generates a reviewable plan from local platform signals and points back to the current upstream authority. It does not download, install, start, stop, reconfigure, or expose anything.

## Why plan-only first

Local-AI installation guidance changes rapidly across operating systems, accelerators, Python versions, driver/runtime versions and backend releases. A static installer that embeds stale commands can become incorrect or dangerous long before the surrounding repository is updated.

The first reusable layer therefore separates:

```text
DETECT -> SELECT UPSTREAM AUTHORITY -> PLAN -> REVIEW
                                      |
                                      X no mutation in v0.1
```

A later mutating adapter can consume this plan only after SafeFix recovery/approval gates and backend-specific acceptance tests exist.

## Search-before-build decisions

### Ollama

Ollama already maintains official platform-specific installation documentation for Linux, Windows and macOS. The planner links those pages rather than mirroring their commands. This is especially important on Linux: the official documentation currently includes convenience shell pipelines, while this public-build program has a stronger supply-chain rule against blindly emitting arbitrary pipe-to-shell installation as a default beginner action.

### llama.cpp

`ggml-org/llama.cpp` is the authority for its build system, accelerator backends, binaries and GGUF model workflow. The planner does not create a competing build tool. It records whether basic source-build prerequisites such as CMake are visible and tells the user to choose an upstream release or pinned source commit.

### vLLM

vLLM's official documentation currently distinguishes CUDA, ROCm, Intel, TPU, Ascend, Apple and CPU paths and carries platform/version-specific requirements. The planner therefore never caches a `pip`/`uv` install command. It directs the user to the current vendor-specific installation page at execution time. Native Windows is not presented as an upstream-supported GPU path; the plan explains the WSL boundary instead.

## CLI

Examples are plan generation only:

```text
python scripts/local_ai_setup_planner.py ollama
python scripts/local_ai_setup_planner.py llama.cpp
python scripts/local_ai_setup_planner.py vllm --accelerator amd
```

The JSON output contains:

- bounded platform/tool-presence signals;
- authoritative upstream documentation locations;
- review steps;
- post-install verification requirements;
- rollback considerations;
- explicit declarations that no network/download/install/service/driver/model/configuration action occurred.

## Security / privacy

The planner does not read usernames, hostnames, network addresses, credentials, environment values, model prompts or user files. It uses only OS/architecture/Python version and Boolean presence checks for a small tool allowlist.

It emits no `curl | sh` command and no hidden executor. A generated plan cannot be used as evidence that an installation happened.

## Beginner view

> "I can tell you which official setup path matches this computer and what we must verify afterward. I will not silently install anything."

## Engineer view

The planner is dependency-free and deterministic from the supplied platform/tool signals. Tests enforce that the safety declaration remains all-false, native-Windows vLLM fails honest, stale vLLM install commands are not embedded, missing CMake is reported rather than installed, and unknown platforms do not receive invented support claims.

## Completion gaps

These roadmap items remain **IN PROGRESS**. Before any can be marked COMPLETE they still need, as applicable:

- dedicated distribution and versioned release;
- SafeFix-governed mutating adapters or a deliberate decision that guided/manual installation is the product boundary;
- signed/pinned artifact and supply-chain verification appropriate to each upstream;
- real Windows/macOS/Linux acceptance for Ollama;
- representative CPU/CUDA/ROCm/Metal/Vulkan acceptance for llama.cpp;
- representative vLLM backend acceptance against current upstream requirements;
- accessibility and multilingual validation;
- reproducible recovery tests;
- evidence-backed post-install verification;
- known-limitations and canonical completion records.

A future implementation must continue to fetch/resolve volatile installation facts from current upstream sources rather than silently relying on this v0.1 documentation snapshot.
