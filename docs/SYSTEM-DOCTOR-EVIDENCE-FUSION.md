# Universal System Doctor — bounded diagnostic evidence fusion v0.1

**Roadmap:** F-02 Universal System Doctor  
**State:** IN PROGRESS  
**Architecture:** `Detect → Inspect → Explain → Recommend → Verify`  
**Default authority:** non-mutating

## Why this layer exists

The existing System Doctor baseline already performs a deliberately shallow privacy-safe read-only collection and has hosted Linux/Windows/macOS acceptance. The next gap is not another monolithic machine probe. Mature ecosystems already expose many system facts:

- **osquery** exposes operating-system instrumentation through SQL-like tables across Linux, Windows and macOS: https://www.osquery.io/
- **psutil** exposes cross-platform CPU, memory, disk, network and sensor/utilization information to Python: https://psutil.readthedocs.io/
- **smartmontools / smartctl** provides SMART and NVMe health/identity information for supported storage devices: https://www.smartmontools.org/
- **Windows CIM / Get-CimInstance** provides structured Windows management information, including operating-system and hardware classes: https://learn.microsoft.com/powershell/module/cimcmdlets/get-ciminstance

Universal System Doctor should therefore **wrap bounded evidence from specialist sources** and preserve provenance, uncertainty and conflicts instead of recreating every diagnostic engine.

## This tranche

`system_doctor_evidence_fusion.py` consumes a strict observation case containing only bounded semantic keys plus provenance metadata. It does not execute any probe itself.

Each observation records:

- a domain such as storage, memory, driver or network;
- `OK`, `NOTICE`, `REVIEW`, or `UNKNOWN`;
- a bounded confidence class;
- non-free-text summary/recommendation/verification keys;
- an adapter/tool/version label;
- exact source-evidence SHA-256;
- collection timestamp.

The output preserves the source evidence digests and produces domain-level states and a deterministic result digest.

## Conflict and uncertainty rules

The fusion layer is intentionally conservative:

1. `OK + REVIEW` or `OK + NOTICE` from independent supplied observations becomes `CONFLICT_REQUIRES_REVIEW`.
2. Conflicts are never resolved by majority vote.
3. `UNKNOWN` by itself remains `UNKNOWN`.
4. `OK + UNKNOWN` becomes `PARTIAL_UNKNOWN`, never `OK`.
5. A recommendation is a **semantic plan key**, never an executable command or permission to repair.
6. A verification key describes what evidence should be obtained after a future action; this module does not perform that action.

## Privacy and safety boundary

The schema is deliberately hostile to raw diagnostic dumps. Extra fields are refused, and the runtime rejects obvious email addresses, IPv4 literals, user-home paths, credential-bearing URLs and common credential prefixes in the few free-form source labels that remain.

The fusion module contains no subprocess, shell, package-manager, service-manager, network, reboot, driver, firmware or file-mutation executor. It does not inspect the live system.

This is important because upstream tools can expose highly identifying or sensitive fields. An adapter must perform its own allowlisting/redaction **before** a public observation is eligible for fusion.

## Beginner view

A future beginner interface can translate the stable semantic keys into language such as:

> “Two checks disagree about the driver state. Nothing was changed. Use the vendor diagnostic before deciding what to fix.”

The key property is that the beginner is not shown false certainty.

## Engineer view

An engineer can inspect:

- exact observation IDs;
- source adapter/tool/version;
- exact SHA-256 of retained source evidence;
- domain fusion state;
- preserved conflict membership;
- verification keys;
- deterministic result SHA-256;
- hard-false mutation and overclaim flags.

## Acceptance in this tranche

Hosted unit/schema tests require:

- the synthetic case to validate against Draft 2020-12 JSON Schema;
- conflict preservation;
- UNKNOWN non-promotion;
- `OK + UNKNOWN → PARTIAL_UNKNOWN`;
- duplicate observation-ID rejection;
- malformed evidence-digest rejection;
- sensitive-literal rejection;
- unreviewed-field rejection;
- absence of execution/network primitives;
- deterministic identical-input output.

The synthetic example intentionally contains a driver conflict and an unknown memory-health observation so CI exercises fail-honest behavior rather than a green-only happy path.

## What a PASS does **not** prove

A passing test means only that this interpretation contract behaves as specified against its test inputs. It does **not** prove:

- that a source tool is correct;
- that source evidence is authentic merely because a digest is supplied;
- physical hardware health;
- root cause;
- vendor-driver correctness;
- production readiness;
- safe repair authority;
- accessibility conformance;
- multilingual real-user acceptance;
- F-02 completion.

## Next F-02 depth gates

1. Add narrow adapters that transform real upstream outputs into the bounded observation contract without retaining sensitive fields.
2. Exercise at least one real specialist source per supported OS family in disposable/non-production acceptance.
3. Bind source observations into F-05 Universal Evidence records rather than treating a naked SHA-256 as trust.
4. Add manual beginner usability and assistive-technology acceptance through F-06.
5. Validate recommendation/verification semantics against real troubleshooting cases without auto-repair.
6. Publish a versioned distribution and final completion record only after the canonical roadmap contract is satisfied.

F-02 therefore remains **IN PROGRESS**.
