# Universal System Doctor — bounded psutil adapter acceptance

**Roadmap:** F-02 Universal System Doctor  
**Status:** IN PROGRESS  
**Scope:** hosted/non-production read-only acceptance

## Search-before-build ruling

The project should not recreate a cross-platform system-utilization library. `psutil` is an established cross-platform Python library for retrieving CPU, memory, disk, network and sensor/utilization information. F-02 therefore uses a deliberately narrow adapter around a tiny allowlisted subset rather than implementing operating-system-specific collectors for these generic capacity facts.

Primary upstream documentation: https://psutil.readthedocs.io/

This does not displace deeper specialist sources. osquery remains useful for structured cross-platform inventory, smartmontools for supported storage SMART/NVMe diagnostics, Windows CIM for Windows management data, and vendor tools for device-specific truth.

## Bounded collection surface

The adapter calls only:

- `psutil.cpu_count(logical=True)`;
- `psutil.virtual_memory()`;
- `psutil.disk_usage()` for the current filesystem root.

It retains only:

- OS family and architecture;
- logical CPU count;
- total/available memory;
- total/free storage;
- adapter and psutil version;
- hard-false privacy/mutation declarations.

It does **not** call psutil user, process, connection or network-interface enumeration APIs. It does not inspect process command lines, environment values, credentials, hostnames, user documents, or browser data.

## Mapping into F-02 evidence fusion

The adapter converts its bounded source record into the merged F-02 observation contract. Every generated CPU/memory/storage observation references the exact SHA-256 of the same retained bounded source evidence.

Headroom policy is intentionally explicit and simple:

- `<5%` available/free → `REVIEW`;
- `5%..<10%` → `NOTICE`;
- `>=10%` → `OK`;
- invalid/unavailable capacity → `UNKNOWN`.

These thresholds are **attention thresholds**, not hardware-failure thresholds. They do not prove root cause and do not authorize cleanup, package removal, disk mutation, service changes or any other repair.

## Real hosted acceptance

The dedicated workflow installs pinned `psutil==7.2.2` on disposable GitHub-hosted:

- Ubuntu 24.04;
- Windows 2025;
- macOS 15.

For each runner it:

1. runs the adapter contract tests against the real psutil runtime;
2. produces a sanitized bounded source record;
3. maps it into the F-02 observation contract;
4. runs the conflict/uncertainty-aware fusion engine;
5. requires all privacy/mutation/overclaim flags to remain false;
6. uploads only the sanitized acceptance record with short retention.

## Evidence semantics

A green matrix establishes only that the pinned psutil adapter can execute the narrow collection/mapping contract on those disposable hosted runner images at that workflow commit.

It does **not** establish:

- physical-device hardware health;
- vendor-specific diagnostics;
- sensor correctness;
- driver correctness;
- root cause;
- production readiness;
- safe repair authority;
- long-term compatibility with future runner images or psutil versions;
- accessibility conformance or real-user acceptance;
- F-02 completion.

## Privacy/security review

The source code is tested for absence of sensitive psutil enumeration surfaces and execution/network primitives. The acceptance artifact does contain coarse machine-capacity values from the disposable hosted runner, so it is classified as public CI evidence only; the same artifact policy should not automatically be applied to a personal or production machine.

Future physical-device adapters must decide whether exact capacity values are necessary for public evidence or should remain local/private.

## Next F-02 gates

1. Add at least one deeper specialist adapter, preferably a bounded osquery or storage-health path, without raw dumps.
2. Bind each retained source artifact to F-05 Universal Evidence provenance/trust records.
3. Exercise real troubleshooting cases where recommendation and verification semantics are assessed against known outcomes.
4. Add beginner/manual and assistive-technology acceptance through F-06.
5. Publish a reusable versioned distribution only after license/release/handover requirements are satisfied.

F-02 remains **IN PROGRESS**.
