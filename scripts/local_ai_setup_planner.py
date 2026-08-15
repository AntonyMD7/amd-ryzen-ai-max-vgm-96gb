#!/usr/bin/env python3
"""Plan-only setup assistant for Ollama, llama.cpp, and vLLM.

This module deliberately performs no installation, download, service mutation,
model pull, driver change, package-manager invocation, or network request. It
turns a small set of local platform signals into a reviewable setup plan that
points users back to the upstream project's authoritative installation docs.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from dataclasses import dataclass
from typing import Any

VERSION = "0.1.0"

AUTHORITIES = {
    "ollama": {
        "homepage": "https://docs.ollama.com/quickstart",
        "linux": "https://docs.ollama.com/linux",
        "windows": "https://docs.ollama.com/windows",
        "macos": "https://docs.ollama.com/macos",
    },
    "llama.cpp": {
        "homepage": "https://github.com/ggml-org/llama.cpp",
        "models": "https://github.com/ggml-org/llama.cpp/blob/master/docs/models.md",
    },
    "vllm": {
        "homepage": "https://docs.vllm.ai/en/latest/",
        "quickstart": "https://docs.vllm.ai/en/latest/getting_started/quickstart/",
        "installation": "https://docs.vllm.ai/en/latest/getting_started/installation/",
    },
}

BACKENDS = tuple(AUTHORITIES)


@dataclass(frozen=True)
class Signals:
    system: str
    machine: str
    python_version: str
    tools: dict[str, bool]


def normalized_system(value: str | None = None) -> str:
    raw = (value or platform.system()).strip().lower()
    aliases = {
        "darwin": "macos",
        "mac": "macos",
        "macos": "macos",
        "windows": "windows",
        "win32": "windows",
        "linux": "linux",
    }
    return aliases.get(raw, raw or "unknown")


def collect_signals(system_override: str | None = None) -> Signals:
    return Signals(
        system=normalized_system(system_override),
        machine=platform.machine() or "unknown",
        python_version=platform.python_version(),
        tools={
            "ollama": shutil.which("ollama") is not None,
            "cmake": shutil.which("cmake") is not None,
            "git": shutil.which("git") is not None,
            "uv": shutil.which("uv") is not None,
            "python": bool(sys.executable),
        },
    )


def common_record(backend: str, signals: Signals) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "planner": {
            "name": "local_ai_setup_planner.py",
            "version": VERSION,
            "mode": "PLAN_ONLY",
        },
        "backend": backend,
        "detected": {
            "system": signals.system,
            "machine": signals.machine,
            "python_version": signals.python_version,
            "tool_presence": signals.tools,
        },
        "safety": {
            "network_requests_performed": False,
            "downloads_performed": False,
            "packages_installed": False,
            "services_changed": False,
            "drivers_changed": False,
            "models_downloaded": False,
            "configuration_changed": False,
            "commands_executed": False,
            "arbitrary_pipe_to_shell_emitted": False,
        },
        "authority": AUTHORITIES[backend],
        "status": "PLAN_ONLY_NOT_INSTALLED_BY_THIS_TOOL",
        "limitations": [
            "Upstream installation requirements can change after this planner release.",
            "A plan is not proof that the backend supports this exact hardware or workload.",
            "Successful installation is not proven until the installed backend and a pinned workload are verified.",
        ],
    }


def ollama_plan(signals: Signals) -> dict[str, Any]:
    record = common_record("ollama", signals)
    system = signals.system
    if system == "linux":
        steps = [
            "Open the official Ollama Linux installation page and review the current package/runtime requirements.",
            "Prefer the upstream documented manual/package path appropriate to the architecture; inspect any downloaded artifact before privileged extraction.",
            "If a GPU backend is intended, verify the current Ollama GPU support documentation and the vendor driver/runtime first.",
            "After installation by the user, verify the CLI version and local service health before downloading a model.",
        ]
        recovery = [
            "Record the pre-install package/service state.",
            "Use the current upstream uninstall instructions if rollback is required.",
            "Do not delete an existing model directory as part of a generic rollback.",
        ]
    elif system == "windows":
        steps = [
            "Review the official Ollama Windows requirements and installer documentation.",
            "Use the official installer or documented standalone package; do not substitute an unofficial repack.",
            "Verify the installed CLI and localhost API before downloading a model.",
        ]
        recovery = [
            "Use Windows Apps / installed-app removal or the current upstream uninstall path.",
            "Preserve model data unless the user explicitly chooses to remove it.",
        ]
    elif system == "macos":
        steps = [
            "Review the official Ollama macOS requirements and installation documentation.",
            "Use the official application package and confirm the CLI path only after the app is installed.",
            "Verify the CLI and local service before downloading a model.",
        ]
        recovery = [
            "Use the current upstream uninstall instructions for the application and CLI link.",
            "Preserve model data unless the user explicitly chooses to remove it.",
        ]
    else:
        steps = ["No supported platform-specific plan is available; consult the current upstream quickstart."]
        recovery = ["No mutation was performed by this planner."]
        record["status"] = "UNSUPPORTED_PLATFORM_PLAN_ONLY"

    record["plan"] = {
        "steps": steps,
        "verification": [
            "Confirm the installed Ollama version from the local CLI.",
            "Confirm the local API/service responds only on the intended interface.",
            "Run one intentionally small, pinned model before making hardware-performance claims.",
        ],
        "recovery": recovery,
    }
    return record


def llama_cpp_plan(signals: Signals) -> dict[str, Any]:
    record = common_record("llama.cpp", signals)
    record["plan"] = {
        "steps": [
            "Review the current ggml-org/llama.cpp README/build documentation for this operating system and accelerator backend.",
            "Choose an upstream release artifact or a source build; record the release/tag or commit before installation.",
            "For a source build, verify the required compiler/CMake toolchain and select only the accelerator flags appropriate to the machine.",
            "Use a local GGUF file or an explicitly selected model source; model acquisition is outside this planner.",
        ],
        "verification": [
            "Record `llama-cli --version` (or the corresponding current upstream binary name/version output).",
            "Run a small pinned GGUF workload locally and record backend selection plus exit status.",
            "Do not infer performance from build success alone.",
        ],
        "recovery": [
            "Keep source/build output isolated from system directories where practical.",
            "Rollback by removing the isolated build/release directory or reverting the package-manager transaction used by the user.",
        ],
    }
    if not signals.tools.get("cmake"):
        record["plan"]["prerequisite_gaps"] = ["CMake not detected in PATH; source-build readiness is not established."]
    return record


def vllm_plan(signals: Signals, accelerator: str) -> dict[str, Any]:
    record = common_record("vllm", signals)
    accelerator = accelerator.lower()
    record["requested_accelerator"] = accelerator
    if signals.system == "windows":
        record["status"] = "NATIVE_WINDOWS_NOT_RECOMMENDED_PLAN_ONLY"
        platform_note = "Use a supported Linux environment such as WSL only after verifying the accelerator is usable there; do not treat native Windows as an upstream-supported GPU install path."
    elif signals.system == "macos":
        platform_note = "Current upstream documentation describes Apple Silicon via vLLM-Metal and separate CPU support; follow the current Apple-specific page rather than CUDA/ROCm instructions."
    elif signals.system == "linux":
        platform_note = "Linux is the primary upstream platform; select the current vendor-specific installation path for the actual accelerator."
    else:
        platform_note = "Platform support is not established; stop at the upstream installation documentation."
        record["status"] = "UNSUPPORTED_PLATFORM_PLAN_ONLY"

    record["plan"] = {
        "steps": [
            platform_note,
            "Review the current vLLM quickstart and vendor-specific installation requirements, including Python, driver/runtime, architecture and glibc constraints.",
            "Create an isolated Python environment before installing vLLM; record Python and package versions.",
            "Use the current upstream installation command for the selected accelerator instead of a cached command embedded in this planner.",
            "Do not expose the vLLM server beyond loopback until authentication, network policy and intended data boundary are reviewed.",
        ],
        "verification": [
            "Import vLLM and record its installed version.",
            "Run a small pinned model/workload on the intended accelerator and retain the result.",
            "If serving, verify the bound address and authentication configuration before widening network exposure.",
        ],
        "recovery": [
            "Keep installation inside an isolated environment so rollback can remove that environment without touching system Python.",
            "Do not change GPU drivers automatically as part of an inference-backend rollback.",
        ],
    }
    return record


def build_plan(backend: str, signals: Signals, accelerator: str = "auto") -> dict[str, Any]:
    if backend == "ollama":
        return ollama_plan(signals)
    if backend == "llama.cpp":
        return llama_cpp_plan(signals)
    if backend == "vllm":
        return vllm_plan(signals, accelerator)
    raise ValueError(f"unsupported backend: {backend}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a non-executing local-AI backend setup plan")
    parser.add_argument("backend", choices=BACKENDS)
    parser.add_argument("--system", help="Testing/preview override: linux, windows, macos")
    parser.add_argument("--accelerator", default="auto", choices=("auto", "nvidia", "amd", "intel", "apple", "cpu"))
    args = parser.parse_args()
    plan = build_plan(args.backend, collect_signals(args.system), args.accelerator)
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
