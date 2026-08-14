# Technical Notes

## AMD ADLX source basis

The reference investigation used AMD's public ADLX SDK and its `VariableGraphicsMemory` sample. The inspected source revision was recorded during the session so the ABI assumptions could be tied to a concrete source state.

The important principle is to derive interface layout from the ADLX headers corresponding to the runtime/API being used rather than copying undocumented offsets from an internet post.

## ADLX call chain

The AMD sample establishes the conceptual chain:

```text
ADLXInitialize
  → IADLXSystem
  → QueryInterface("IADLXSystem3")
  → IADLXSystem3::GetVariableGraphicsMemory
  → IADLXVariableGraphicsMemory
```

From the VGM interface:

```text
IsSupported
GetDefaultOption
GetOption
GetAvailableOptions
SetOption
```

The safe discovery phase uses every method above **except SetOption**.

## Why semantic target matching matters

The reference platform exposed the desired target as option 12, but an implementation that blindly calls `At_OptionList(..., 11, ...)` is unnecessarily fragile.

A safer algorithm is:

```text
for each available option:
    read Name
    read Mode
    read MemoryCarved
    read MemoryRemaining

select only if:
    Name == "Custom"
    MemoryCarved == 96
    MemoryRemaining == 32

require exactly one match
```

The ordinal can then be logged for evidence, but it is not the identity of the target.

## Windows x64 calling convention

On 64-bit Windows the platform uses the unified x64 calling convention. The reference ctypes implementation modeled ADLX interface methods using `WINFUNCTYPE` and the exported initialization functions with normal ctypes DLL bindings.

## Application Control

A locally compiled helper may be rejected on a system enforcing user-mode Code Integrity. This is expected security behavior.

Do not respond by automatically disabling Smart App Control or WDAC. Better approaches include using a properly trusted/signed binary or an already-authorized runtime while loading the vendor-signed ADLX library.

The reference system preserved:

- User-mode Code Integrity enforcement
- VBS
- active Code Integrity policies
- AMD's signed driver/runtime chain

## `SetOption` is the boundary

Treat `IADLXVariableGraphicsMemory::SetOption` as a transaction boundary.

Everything before it should be repeatable and read-only. Everything after it should assume the state may already have changed, even if the transport fails.

A robust implementation therefore records a durable attempt marker *before* invoking the method and records the returned result immediately afterward.

## Reboot semantics

The VGM allocation became authoritative after reboot on the reference machine. A reboot disrupts remote SSH and Tailscale availability temporarily. A remote orchestrator must distinguish:

```text
transaction accepted → reboot → connection lost
```

from:

```text
transaction never reached
```

Those are fundamentally different recovery cases.

## Post-state sources

Use several independent observations where possible:

1. ADLX current option — vendor API semantic state.
2. Windows `TotalVisibleMemorySize` — OS-visible system memory.
3. AMD driver's `HardwareInformation.qwMemorySize` — driver-exposed GPU memory.
4. Task Manager — human-visible independent confirmation.

Agreement among these sources is substantially stronger than relying on a single UI screenshot.

## Units

Expect small visual differences such as `96 GB` in ADLX/driver output versus approximately `95.8 GB` in Task Manager. Different APIs/UI layers may use decimal labels, binary quantities, reservations, or rounded display values.
