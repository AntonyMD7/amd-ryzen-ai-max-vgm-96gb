# Security and Safety Policy

Changing Variable Graphics Memory affects the memory available to Windows and normally requires a reboot. Treat it as a system configuration change, not a cosmetic preference.

## Before changing VGM

- save work and stop important workloads;
- establish a tested recovery path;
- verify the installed AMD runtime is trusted;
- enumerate supported options read-only;
- confirm the intended target exists exactly once;
- record the current state;
- keep a local/console recovery option where practical.

## Security controls

Do not disable Smart App Control, WDAC, Code Integrity, VBS, Secure Boot, antivirus, or endpoint controls solely to run an unsigned helper from this project.

The reference solution succeeded while preserving Windows Code Integrity enforcement.

## Transaction safety

A successful `SetOption` may be followed by an SSH disconnect because Windows is rebooting. Never interpret the disconnect alone as authorization to repeat the write.

Reconnect, read the current state, and decide from evidence.

## Reporting a security issue

Avoid putting credentials, private infrastructure data, or exploitable security findings into a public issue. Use GitHub's private vulnerability-reporting mechanism when enabled for this repository, or contact the maintainer privately through an appropriate verified channel.
