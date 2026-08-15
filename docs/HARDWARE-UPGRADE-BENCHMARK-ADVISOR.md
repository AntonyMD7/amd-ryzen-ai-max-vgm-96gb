# Hardware Upgrade & Benchmark Advisor

Status: **IN PROGRESS reference implementation** for:

- `P-011 RAM Upgrade Assistant`
- `P-012 GPU Upgrade Assistant`
- `P-013 SSD/Storage Upgrade Assistant`
- `P-014 Thermal/Power Diagnostic Assistant`
- `P-015 Benchmark Result Interpreter`

## Design decision

This layer does not probe a computer, recommend a product, run a benchmark, alter firmware or install hardware. It interprets **explicit normalized facts** and identifies what still needs authoritative verification.

That boundary matters because compatibility depends on exact OEM/device, board, firmware, electrical, mechanical, operating-system and workload details. A simple arithmetic pass must not be presented as proof that a part will work.

## Search before build

Existing specialist ecosystems remain the engines where appropriate:

- **Memtest86+** is an established open-source memory tester. This project does not build a competing memory-stress engine.
- **smartmontools** provides `smartctl`/`smartd` for SMART-based storage monitoring. This project does not create another disk-health database or SMART parser in this tranche.
- **Phoronix Test Suite** is an established cross-platform automated benchmark framework. This project does not duplicate its benchmark execution/catalog system.
- OEM/vendor specifications and QVL/compatibility documentation remain authoritative for upgrade eligibility.

The new value here is a conservative interpretation layer that can sit above authoritative evidence without turning incomplete facts into a purchase or safety guarantee.

## Modes

### RAM (`P-011`)

Compares installed capacity, desired capacity, caller-supplied vendor maximum and basic slot availability. It still requires memory generation/type, module topology, firmware/OEM support and post-install memory testing.

### GPU (`P-012`)

Checks only caller-supplied PSU requirement, PSU capacity, connector verification and physical-fit verification. PCIe support, case clearance details, cooling, OS/driver support and OEM restrictions remain separate gates.

### Storage (`P-013`)

Checks explicit interface, form-factor and available-slot facts. It does not infer lane sharing, boot support, thermal requirements, endurance, health or migration safety.

### Thermal/power (`P-014`)

Compares an observed value only to a **caller-supplied vendor/declared limit**. It deliberately contains no universal temperature or power threshold table. Sensor provenance, ambient conditions and workload still matter.

### Benchmark interpretation (`P-015`)

Computes simple relative arithmetic only when workload, software and settings are declared comparable. If a material field differs, ranking is refused. A single result is not statistical evidence; repeat count/variance and hardware/software identity remain required.

## Safety and privacy

The module:

- performs no hardware probe;
- runs no benchmark;
- changes no setting or firmware;
- recommends no purchase;
- reads no serial, UUID, username, path, credential or network identity;
- accepts only the normalized facts needed for each calculation;
- makes no stability, compatibility or performance guarantee.

## Beginner experience

A future UI can ask small, concrete questions rather than exposing users to raw specification jargon. For example:

> Your current information passes the basic capacity check, but that does **not** prove compatibility. Verify the manufacturer's memory specification and module type before buying anything.

## Engineering experience

Example benchmark input:

```json
{
  "kind": "benchmark",
  "candidate_value": 80,
  "baseline_value": 100,
  "higher_is_better": false,
  "same_workload": true,
  "same_software": true,
  "same_settings": true
}
```

The output preserves the raw relative change and a direction-aware improvement value while keeping `result_is_performance_guarantee: false`.

## Completion gaps

Before any mapped project can be marked COMPLETE, it still needs the relevant roadmap completion gates, including broader hardware fixtures, authoritative-source adapters, beginner distribution, real-world acceptance, security/privacy/accessibility review, multilingual consideration, versioned release evidence, known limitations and a canonical completion record. Hardware installation also requires a separate recovery/safety procedure appropriate to the device.
