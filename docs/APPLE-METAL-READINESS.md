# Apple Metal Compatibility Discovery v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-025 Apple Metal Compatibility Checker`, reusable by `F-03 Local AI Doctor`.

## Purpose

This is a privacy-minimizing macOS discovery layer. It asks macOS for display/GPU information using `system_profiler SPDisplaysDataType -json`, keeps only bounded non-unique GPU model and Metal-related signals, and discards the rest of the profiler record.

A discovery signal is not the same as application-grade feature support.

## Search-before-build / Apple authority

Apple's Metal documentation already defines the authoritative capability model. Current Apple guidance uses `MTLGPUFamily` and `MTLDevice.supportsFamily(_:)` for feature-family checks; the older `MTLFeatureSet` enumeration is deprecated for newer families. Apple also publishes maintained Metal Feature Set Tables that map current GPUs to Metal versions/families.

This project therefore does not maintain an independent permanent table of Apple GPU capabilities. The CLI collector finds a safe host signal; exact feature requirements must be checked against Apple's current tables/API.

## Read-only command

On macOS the collector may run only:

```text
system_profiler SPDisplaysDataType -json
```

It does not compile shaders, run a Metal workload, install Xcode/tools, change graphics settings or query credentials.

`system_profiler` can contain more information than the public report should retain. Raw JSON therefore remains transient in-process. The report intentionally does **not** expose display serial numbers, hardware UUIDs, network addresses, hostname, username or credentials.

## Interpretation

`METAL_DISCOVERY_SIGNAL_PRESENT`
: a Metal-related field was present in the bounded display profile. This is useful discovery evidence only.

`METAL_SUPPORT_NOT_PROVEN`
: the profiler ran but the collector did not find a recognized Metal signal. Do not infer that Metal is unsupported.

`NOT_APPLICABLE_NON_MACOS`
: the collector is running outside macOS and deliberately does not attempt emulation or inference.

## Required next gates

For a real Metal application or local-AI backend:

1. identify the exact capability/features the application requires;
2. use Apple's current Metal Feature Set Tables for the GPU/OS combination;
3. in an application-grade probe, obtain an `MTLDevice` and call `supportsFamily(_:)` for the specific feature families required;
4. run a pinned workload on a real Mac;
5. record OS, application/backend version, result and limitations.

## Beginner interpretation

> "This Mac reports a Metal-related GPU signal. That means we have a promising starting point, but we still need to verify the exact Metal features required by the app and test the real workload."

## Completion gaps

`P-025` remains **IN PROGRESS**. Completion requires a native Swift/Metal capability adapter using `MTLDevice`, Mac hardware/OS fixtures across representative families, real local-AI/backend acceptance, accessibility and multilingual documentation, dedicated distribution, release/tag evidence, known limitations and canonical completion evidence.
