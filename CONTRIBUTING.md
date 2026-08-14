# Contributing

Contributions from other AMD Ryzen AI Max systems are welcome, especially evidence that improves compatibility knowledge without weakening safety gates.

## Useful reports

Please include, where available:

- exact system/vendor/model;
- physical unified-memory capacity;
- Windows build;
- AMD graphics-driver version;
- ADLX runtime version;
- whether VGM reports supported;
- complete **read-only** available-option enumeration;
- pre-change current option;
- post-reboot ADLX current option;
- post-reboot Windows-visible memory;
- post-reboot driver GPU-memory value.

## Redact before posting

Never publish SSH private keys, access tokens, passwords, private IP infrastructure you do not intend to disclose, Tailscale auth material, personal email addresses, machine serial numbers, or unrelated logs containing sensitive information.

## Engineering rules

1. Discovery and mutation must remain separate.
2. Never assume an option ordinal identifies the same allocation on another platform.
3. Match the target semantically.
4. Do not disable Windows security controls as a convenience workaround.
5. Do not automatically retry `SetOption` after a connection loss.
6. A write path should enforce a maximum call count and durable evidence.
7. Post-reboot state, not transport behavior during reboot, determines success.

If you propose a mutating helper, make the mutation conspicuous, guarded, opt-in, and independently auditable.
