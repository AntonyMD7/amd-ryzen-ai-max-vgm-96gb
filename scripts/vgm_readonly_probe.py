"""AMD ADLX VGM read-only discovery probe.

This utility deliberately performs discovery only. It does not bind or invoke
IADLXVariableGraphicsMemory::SetOption.

The full field-tested ABI walk and evidence are documented in
../docs/VERIFIED_SEQUENCE.md. This compact public script focuses on runtime
identity and export validation so users can establish a safe baseline before
adapting the ABI-specific enumeration to their installed ADLX release.
"""

from __future__ import annotations

import ctypes
import hashlib
import os
import sys
from pathlib import Path


def find_adlx() -> Path:
    root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    candidates = list(
        (root / "System32" / "DriverStore" / "FileRepository").glob(
            "**/amdadlx64.dll"
        )
    )
    if not candidates:
        raise FileNotFoundError("amdadlx64.dll not found in DriverStore")
    return max(candidates, key=lambda p: p.stat().st_mtime_ns)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    if sys.platform != "win32":
        print("PLATFORM_GATE=FAIL|REASON=Windows_required")
        return 2

    path = find_adlx()
    print(f"ADLX_DLL={path}")
    print(f"ADLX_SHA256={sha256(path)}")

    dll = ctypes.CDLL(str(path))
    print("ADLX_DLL_LOAD=PASS")

    required = (
        "ADLXQueryVersion",
        "ADLXQueryFullVersion",
        "ADLXInitialize",
        "ADLXTerminate",
    )
    for name in required:
        try:
            getattr(dll, name)
        except AttributeError:
            print(f"EXPORT_{name}=MISSING")
            return 3
        else:
            print(f"EXPORT_{name}=FOUND")

    query = dll.ADLXQueryVersion
    query.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
    query.restype = ctypes.c_int
    version = ctypes.c_char_p()
    rc = query(ctypes.byref(version))
    print(f"ADLX_QUERY_VERSION_RC={rc}")
    if version.value:
        print(f"ADLX_QUERY_VERSION={version.value.decode(errors='replace')}")

    full = dll.ADLXQueryFullVersion
    full.argtypes = [ctypes.POINTER(ctypes.c_uint64)]
    full.restype = ctypes.c_int
    value = ctypes.c_uint64()
    rc2 = full(ctypes.byref(value))
    print(f"ADLX_QUERY_FULL_VERSION_RC={rc2}")
    print(f"ADLX_QUERY_FULL_VERSION={value.value}")

    # Safety contract: no initialization is necessary for this baseline probe,
    # and the mutating SetOption interface is never obtained or called.
    print("ADLX_INITIALIZE_CALLED=FALSE")
    print("SETOPTION_BOUND=FALSE")
    print("SETOPTION_CALLED=FALSE")
    print("VGM_CHANGED=FALSE")
    print("READONLY_PROBE_COMPLETE=TRUE")
    return 0 if rc == 0 and rc2 == 0 else 4


if __name__ == "__main__":
    raise SystemExit(main())
