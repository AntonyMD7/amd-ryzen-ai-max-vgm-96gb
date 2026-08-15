# Cross-Platform System Support Planner

Status: **reference implementation / IN PROGRESS evidence**, not a repair engine.

Roadmap scope:

- `P-003` Windows Repair Assistant
- `P-004` Linux Repair Assistant
- `P-005` Driver Detection & Resolution Assistant
- `P-006` BIOS/UEFI Guided Configuration Assistant
- `P-007` Wi-Fi/Bluetooth/Network Troubleshooter
- `P-008` Printer & Peripheral Troubleshooter
- `P-009` Hardware Compatibility Detector
- `P-010` Firmware Compatibility Checker

## Why this layer exists

Users often arrive with a symptom and are immediately given a chain of commands that mixes inspection, repair, package installation and rebooting. That makes it difficult for a beginner to understand what is merely being observed and what will change the machine.

`system_support_planner.py` establishes a narrower first step: classify the support area and return a **bounded read-only preflight plan** or a **vendor-guidance-required** outcome. It never executes the commands it displays.

A generated plan is not diagnostic proof, compatibility proof, a successful repair, or authorization to mutate a system.

## Search before build: adopt authoritative engines

This project does not try to replace established operating-system, vendor or community tooling.

### Windows integrity

Microsoft's System File Checker and DISM remain the authoritative Windows servicing tools. The reference catalog uses `sfc /verifyonly` and DISM `/CheckHealth` / `/ScanHealth` for inspection. It deliberately excludes repair switches such as `sfc /scannow` and DISM `/RestoreHealth` from this discovery-only layer.

### Linux diagnostics

Distribution documentation plus systemd's `systemctl` and `journalctl` remain the primary interpretation authorities for service/boot failures. The planner emits bounded inspection examples only.

### Hardware and drivers

Operating-system and hardware-vendor documentation remains authoritative. On Linux, projects such as `linuxhw/hw-probe` are useful community evidence sources when their privacy and upload behavior fit the user's policy; this planner does not duplicate their hardware database.

### Firmware

`fwupd` and LVFS are established Linux firmware ecosystems on supported devices. The reference plan may suggest `fwupdmgr get-devices --json` as discovery, but it never emits `update` or `refresh`. Firmware applicability and installation remain vendor/tool decisions requiring separate review and recovery planning.

### Networking

Windows networking cmdlets and NetworkManager's `nmcli` are established platform interfaces. Because `nmcli` can also mutate connections, this catalog contains only fixed status commands and rejects mutation-like catalog entries.

### BIOS / UEFI

There is no safe universal BIOS mutation command. Firmware menus, names, defaults, dependencies and recovery behavior differ by OEM/device. The planner therefore returns `VENDOR_GUIDANCE_REQUIRED` instead of inventing a generic configuration recipe.

## Safety architecture

```text
user selects platform + support area
                |
                v
        validate bounded input
                |
                v
     choose fixed inspection catalog
                |
          +-----+-----+
          |           |
          v           v
 READ_ONLY_PREFLIGHT  VENDOR_GUIDANCE_REQUIRED
          |           |
          +-----+-----+
                v
      return reviewable plan only
                |
                v
      separate evidence collection
                |
                v
 vendor/OS interpretation + SafeFix gate
                |
                v
   mutation only in a later governed lane
```

The public reference layer:

- executes no command;
- accepts no arbitrary shell input;
- accepts only boolean observation facts instead of raw logs/free text;
- returns no raw logs, serials, UUIDs, user paths or credential values;
- performs no driver/package installation;
- performs no firmware or BIOS change;
- performs no network change;
- does not reboot or request a reboot;
- does not infer that a zero exit code means a problem was fixed.

## Beginner experience

A future accessible front end should be able to present a choice such as:

> **What are you trying to check?** Windows health, Linux health, drivers, BIOS/UEFI, network, peripherals, compatibility or firmware.

Then it should explain each suggested inspection in plain language before any local collector is allowed to run it.

The current module is intentionally an engineering primitive. It is not yet the complete beginner application required by the master roadmap.

## Engineer experience

Example input:

```json
{
  "platform": "windows",
  "area": "driver",
  "observations": {
    "device_manager_has_warning": true,
    "network_available": true
  }
}
```

Run the planner locally:

```bash
python scripts/system_support_planner.py request.json
```

The command prints JSON containing the canonical roadmap ID, fixed read-only checks, upstream authorities, safety declarations and evidence semantics. It still executes none of the proposed checks.

## Privacy boundary

Do not feed full diagnostic logs, usernames, hostnames, IP addresses, serial numbers, UUIDs, device-instance identifiers, credentials, tokens or private paths into the planning request. The reference API intentionally retains only **fact names and boolean values**.

A future collector must define a separate schema and redaction contract for each evidence class rather than turning arbitrary logs into a public artifact.

## Accessibility and multilingual path

The planner's machine representation is deliberately compact so a presentation layer can render the same facts as:

1. plain-language beginner instructions;
2. intermediate risk/alternatives/results;
3. engineer-level command and evidence details.

Canonical field values should remain language-neutral identifiers; explanations can then be localized without changing the underlying evidence. This tranche ships English engineering documentation only and therefore does not claim multilingual completion.

## Recovery boundary

No recovery procedure is necessary for running the planner because it has no mutation path. If a later implementation proposes repair, installation, firmware configuration, BIOS changes, networking changes or reboot, it must enter the SafeFix lifecycle with explicit pre-state evidence, recovery, approval, bounded mutation and post-change attestation.

## Tests and CI

The repository test suite verifies:

- canonical roadmap mappings;
- Windows verification-only servicing commands;
- Linux observation-only repair preflight;
- vendor-guidance refusal for generic BIOS/UEFI and Windows firmware mutation;
- no Linux firmware update/refresh command;
- no networking modification command;
- non-mutation declarations;
- rejection of free-text observations;
- fail-closed platform/area mismatches;
- no proof/authorization overclaim.

The repository's existing Safety Checks workflow compiles all Python in `scripts/` and runs the full pytest suite on pull requests.

## What remains before any mapped item can be COMPLETE

Among other project-specific gates from the master roadmap:

- dedicated user-facing distribution where appropriate;
- broader Windows/Linux fixtures and version coverage;
- real-world acceptance on representative hardware;
- authoritative driver/firmware/compatibility adapters;
- accessible browser/voice surfaces;
- multilingual validation;
- explicit release/version record;
- independent security/privacy/accessibility review;
- evidence-backed repair paths, where appropriate, behind SafeFix recovery/approval controls;
- canonical completion records.

Until those gates are satisfied, `P-003` through `P-010` are at most **IN PROGRESS** reference work.