# Troubleshooting

This document starts with the safest interpretation: **unknown state is not failure and is not permission to retry a mutation**.

## ADLX reports VGM unsupported

Stop. Do not attempt to force the procedure. Capture your hardware model, AMD driver version, ADLX version, and read-only probe output and open an issue.

## There is no 96/32 option

Stop. Do not substitute another option automatically. Firmware, driver, product SKU, or platform policy may differ from the reference machine.

## More than one 96/32 target matches

Stop. Treat the target as ambiguous until the interfaces and option metadata are understood.

## My option number is not 12

That is acceptable. Option numbers are not portable contracts. Match by semantic values (`Custom`, `96`, `32`).

## Windows blocks a locally compiled helper

Do not disable security controls by default. On the reference machine, Code Integrity correctly blocked an unsigned helper. The successful path used an existing trusted Python runtime together with the signed AMD ADLX DLL.

## SSH disappears after SetOption

If the write returned success and reboot was initiated, do not retry `SetOption`. Wait for the machine to return, then run read-only post-reboot attestation.

## SSH says connection timed out after reboot

Check in this order:

1. whether the machine has finished booting;
2. whether Tailscale shows it online;
3. whether the host answers a Tailscale ping;
4. whether TCP port 22 is open;
5. whether SSH login succeeds.

None of those checks should invoke `SetOption`.

## The orchestrator is stuck waiting after the machine is already reachable

A stale SSH child process or transport loop may be blocking the orchestration shell. Inspect the process tree first. If you terminate only the stale transport process, do not restart the mutation stage. Run a fresh read-only attestation instead.

## Task Manager shows about 95.8 GB, not 96 GB

That can be normal. Windows UI display and API unit conventions differ. Confirm with AMD ADLX and driver-reported memory as well.

## Windows shows only about 31.8 GB RAM after the change

That is expected for the 96/32 target on a 128 GB unified-memory system. The 96 GB graphics carve-out leaves about 32 GB for Windows.

## ADLX read-only probe says its old “64/64 preflight” failed after the upgrade

That can be expected if the probe contains a transition-specific gate that expects the old state. The important post-change values are the **current** option fields. A post-reboot verifier should judge `Custom / 96 / 32`, not require the former `64 / 64` source state.

## ADLXTerminate returns a non-zero code during reboot sequencing

Do not infer that `SetOption` failed solely from a later terminate result if the recorded `SetOption` return code was successful and the reboot had begun. Post-reboot attestation is the deciding evidence.

## I lost remote access entirely

Use local console access or your preplanned recovery path. Do not repeatedly power-cycle or repeat the VGM write unless you first establish the actual current state.

## I want to report a new platform

Sanitize your evidence and include:

- exact hardware model;
- physical memory size;
- Windows build;
- AMD driver version;
- ADLX version;
- VGM support status;
- complete enumerated option values;
- current option before/after, if applicable;
- whether recovery services remained available;
- whether Task Manager agreed with ADLX after reboot.
