# CUDA Readiness Precheck v0.1

Status: **IN PROGRESS reference implementation**

Roadmap mapping: `P-024 CUDA Readiness Validator`, reusable by `F-03 Local AI Doctor`.

## Purpose

This tool answers a narrow preflight question without changing the machine: are the NVIDIA driver and CUDA compiler surfaces present, what versions can be parsed, and does the observed driver major clear NVIDIA's documented **major-family minor-version compatibility floor** for CUDA 11.x, 12.x or 13.x?

It is not an application compatibility test and does not run CUDA code.

## Search-before-build / vendor authority

NVIDIA already defines CUDA driver/toolkit compatibility and GPU architecture support. This reference layer therefore consumes those rules rather than inventing a competing compatibility model.

The offline snapshot embedded in `scripts/cuda_readiness.py` is dated **2026-08-15** and reflects NVIDIA's CUDA 13.3 documentation for minor-version compatibility family floors:

- CUDA 11.x: driver major 450 or newer;
- CUDA 12.x: driver major 525 or newer;
- CUDA 13.x: driver major 580 or newer.

The exact CUDA Toolkit release notes remain authoritative, and CUDA architecture support changes over time. The script explicitly fails honest for a CUDA major family outside its dated snapshot.

## Important `nvidia-smi` distinction

NVIDIA documents that the CUDA version shown by `nvidia-smi` represents the CUDA user-mode capability supported by the installed driver and is **usually, but not always, the version of the CUDA Toolkit installed on the machine**. Therefore this probe keeps driver capability and `nvcc` toolkit version as separate fields.

## Read-only operations

The collector may run only:

```text
nvidia-smi
nvcc --version
```

It does not query or return GPU UUID, serial number, PCI bus identity, hostname or credentials. Raw command output is used only for bounded in-process parsing and is not emitted in the report.

It does not install/update a driver or toolkit, compile code, run `deviceQuery`, execute a CUDA workload or change GPU state.

## Interpretation

`FAMILY_FLOOR_PRECHECK_PASSES_MORE_VALIDATION_REQUIRED`
: the parsed driver major clears the dated family floor. This is only an early compatibility precheck.

`BELOW_DOCUMENTED_MINOR_COMPATIBILITY_FAMILY_FLOOR`
: the driver is below the family floor in the embedded documentation snapshot. Do not automatically update the driver; first establish recovery, hardware/OS support and the exact target toolkit requirement.

`CUDA_FAMILY_OUTSIDE_SNAPSHOT_REQUIRES_CURRENT_VENDOR_DOCS`
: the toolkit major is newer/older than the embedded table. The tool refuses to guess.

## Required next gates

Before claiming CUDA readiness for a real application:

1. verify the exact toolkit release and its current minimum-driver requirements in NVIDIA release notes;
2. verify that the target GPU architecture remains supported by the toolkit/driver family;
3. verify framework/backend requirements;
4. compile/run a pinned CUDA sample or exact target workload in a separately governed acceptance step;
5. record success/failure evidence and relevant versions.

## Safety and recovery

If the precheck identifies an old driver, that is **not permission to update it**. Driver changes can affect displays, compute workloads, kernel integration and remote access. Any mutation belongs behind SafeFix preflight, explicit approval, recovery planning, post-change attestation and rollback evidence.

## Completion gaps

`P-024` remains **IN PROGRESS**. Completion requires a dedicated public distribution surface, versioned source refresh mechanism for NVIDIA compatibility data, Windows/Linux fixtures, representative supported/unsupported architecture acceptance, exact-workload validation, accessibility/multilingual review, release/tag evidence, known limitations and canonical completion evidence.
