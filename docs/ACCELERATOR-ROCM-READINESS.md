# GPU/NPU + ROCm Readiness Discovery v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-022 GPU/NPU Capability Detector` and `P-023 ROCm Readiness Validator`, with reuse by `F-03 Local AI Doctor`.

## Scope

This tranche answers a narrow first question safely: **which recognized accelerator-management/runtime tools are present, and do their documented read-only inspection commands respond?**

It does not install ROCm, Ryzen AI, CUDA or drivers; it does not run accelerator validation/stress workloads; it does not change NPU/GPU power modes; and it does not claim that a detected device/runtime is officially supported for a particular framework, model or operating-system combination.

## Search-before-build / upstream adoption

The reference implementation intentionally uses vendor tools as the authority instead of creating a parallel hardware-discovery engine.

AMD's ROCm documentation identifies `rocminfo` and AMD SMI as installation-verification/system-management tools. AMD's Ryzen AI documentation identifies `xrt-smi examine` as the NPU inspection path; `xrt-smi validate` runs sanity tests and `xrt-smi configure` changes performance settings, so this public discovery layer **does not invoke either of those commands**. NVIDIA discovery uses a bounded `nvidia-smi` query for the non-unique GPU name and deliberately excludes UUID, serial and bus identity.

Official compatibility matrices remain the authority for support. A responding `rocminfo` plus a parsed `gfx*` architecture means only that a useful discovery signal exists.

## Read-only contract

`scripts/accelerator_readiness.py` has a fixed command allowlist:

```text
rocminfo
amd-smi version
xrt-smi examine --report platform
nvidia-smi --query-gpu=name --format=csv,noheader
```

There is no arbitrary command argument or shell execution surface.

The structured output intentionally omits raw command output. It records only bounded signals such as command presence/return code, parsed `gfx*` architecture tokens and non-unique device names. It explicitly declares whether unique GPU identifiers, host/user/network data or credentials were collected.

## Interpretation

`RUNTIME_RESPONDS_ACCELERATOR_ARCH_SEEN`
: `rocminfo` returned successfully and a `gfx*` architecture token was parsed. This is discovery evidence, **not** official support evidence.

`NPU_EXAMINE_RESPONDS_DEVICE_SIGNAL_SEEN`
: the bounded `xrt-smi examine` call returned successfully and a Ryzen AI NPU device-name signal was parsed. This is discovery evidence, not workload validation.

`NOT_PROVEN`
: the relevant tool is absent, fails, or does not yield the expected bounded signal. This does not prove that the physical machine lacks an accelerator.

## Required next gates for ROCm

Before a `SUPPORTED` claim, record and compare at least:

1. exact GPU/APU architecture;
2. operating system and supported distribution/version;
3. kernel/driver where applicable;
4. installed ROCm or framework package version;
5. AMD's current compatibility matrix entry for that combination;
6. exact target framework/backend support;
7. a pinned real workload acceptance test.

On Ryzen AI Max-class APUs, AMD publishes platform-specific OS/kernel and framework guidance. Those constraints can change between ROCm releases, so they must not be hard-coded permanently into this lightweight probe.

## NPU safety boundary

AMD documents `xrt-smi` commands with different semantics: `examine` inspects state, `validate` executes sanity tests, and `configure` manages NPU performance settings. This implementation invokes **only `examine`**. Validation workloads belong in a separately governed acceptance stage; configuration belongs behind SafeFix recovery/approval controls.

## Beginner view

If the tool reports a discovery signal, read it as:

> "Your machine exposes a promising accelerator/runtime signal. We still need to check the official compatibility table and test the exact workload before saying it is supported."

If it reports `NOT_PROVEN`, read it as:

> "This check could not prove accelerator readiness. It is not proof that your hardware is unsupported."

## Completion gaps

`P-022` and `P-023` remain **IN PROGRESS**. Completion requires a dedicated user-facing distribution surface, support-matrix adapter with source/version provenance, broader NVIDIA/AMD/Intel/Apple/NPU coverage as appropriate, Windows/Linux acceptance, real supported and unsupported fixtures, accessibility/multilingual verification, release/tag evidence, known-limitations records and canonical completion evidence.
