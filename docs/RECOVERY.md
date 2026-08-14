# Recovery and Remote-Safety Plan

A VGM change can reboot the machine and reduce Windows-visible memory. Recovery must be designed **before** mutation.

## Minimum recovery contract

Before any write, verify at least one working recovery path. For remote systems, two independent paths are preferable.

The reference case used:

- Tailscale for private network reachability;
- Windows OpenSSH for command access;
- local console access available through a trusted person on site.

## Required checks

Immediately before mutation, confirm:

```text
sshd      = Running / Automatic
Tailscale = Running / Automatic
```

If you use different tooling, verify the equivalent service and startup state.

## During reboot

Expected observations can include:

- SSH session termination;
- temporary Tailscale offline state;
- TCP 22 unavailable;
- the orchestration process waiting for return.

Do **not** equate any one of these with a failed VGM transaction.

## Recovery probe order

Once reboot has been initiated, use read-only checks only:

```text
1. Tailscale status
2. Tailscale ping
3. TCP port 22
4. SSH authentication
5. Windows/ADLX post-reboot attestation
```

## Critical anti-retry rule

If evidence shows:

```text
SETOPTION_CALL_COUNT_AFTER=1
SETOPTION_RC=0
SETOPTION_ACCEPTED=TRUE
```

then a lost SSH connection is **not authorization to call SetOption again**.

The next action is recovery/attestation, not mutation.

## If the orchestrator itself stalls

Inspect the process tree. A stale SSH process can leave a parent shell waiting even though the remote machine has rebooted.

Terminating a stale transport process is different from rerunning a VGM write. Preserve the transaction evidence, release only the stale transport if necessary, then attest the live machine.

## If the machine never returns remotely

Use local console access. Confirm:

- Windows boot status;
- network status;
- Tailscale service;
- OpenSSH service;
- current memory presentation.

Do not repeat the mutation until the current VGM state is known.

## Evidence preservation

Keep preflight, apply, and post-reboot evidence in separate files. Never overwrite the write evidence with a later retry attempt. A complete incident timeline is more valuable than a “clean” log.
