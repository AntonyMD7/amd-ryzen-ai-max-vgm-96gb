# Community Safety Standard

This project welcomes beginners, enthusiasts, system integrators, developers, and engineers. The same repository serves all of them, but contributions must preserve a professional safety boundary.

## Core rule

Every procedure must make it obvious whether it is:

- read-only discovery;
- prerequisite verification;
- mutating configuration;
- reboot/recovery handling;
- post-change attestation.

A contributor must not hide a mutating operation inside a script presented as diagnostics.

## Beginner usability standard

Beginner-facing instructions should:

- explain the goal before the command;
- state whether the step changes anything;
- show the expected output pattern;
- provide a stop condition;
- avoid assuming prior knowledge of ADLX, ctypes, vtables, WDAC, or VBS;
- define technical terms when first used.

## Engineering standard

Technical contributions should:

- cite the interface or API being used;
- preserve exact return codes where available;
- distinguish observed fact from inference;
- use semantic target matching rather than menu-position assumptions;
- fail closed when state is ambiguous;
- preserve pre/post evidence;
- avoid weakening Windows security controls as a convenience shortcut;
- preserve at-most-once semantics for `SetOption`.

## Evidence levels

Use one of these labels when reporting results:

- `VERIFIED` — full live discovery plus post-change attestation.
- `DISCOVERY-ONLY` — read-only enumeration only.
- `COMMUNITY-REPORTED` — useful report not yet checked against the complete evidence contract.
- `UNSUPPORTED/NO-TARGET` — VGM or the requested target was not exposed.
- `UNKNOWN` — insufficient evidence.

## Redaction standard

Before posting logs, remove:

- SSH private keys;
- API keys and tokens;
- passwords;
- private hostnames and infrastructure details you do not want public;
- personally identifying account data;
- unrelated application data.

Hardware model, driver version, Windows build, ADLX version, and VGM option values are generally useful technical evidence.

## No “works on my machine” shortcuts

A successful reference platform does not make a hard-coded option index portable. Community scripts must discover live values and prove that the requested target exists on the current machine.

## Review philosophy

Safety-sensitive changes should be reviewed for two questions independently:

1. Does the code do what it claims?
2. Could a beginner misunderstand the boundary and accidentally mutate the system?

Both must pass.
