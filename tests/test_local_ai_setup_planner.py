from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "local_ai_setup_planner.py"
spec = importlib.util.spec_from_file_location("local_ai_setup_planner", MODULE_PATH)
assert spec and spec.loader
planner = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = planner
spec.loader.exec_module(planner)


def signals(system: str, **tools: bool):
    base = {"ollama": False, "cmake": False, "git": True, "uv": False, "python": True}
    base.update(tools)
    return planner.Signals(system=system, machine="x86_64", python_version="3.12.0", tools=base)


def assert_plan_only(record):
    safety = record["safety"]
    assert record["planner"]["mode"] == "PLAN_ONLY"
    assert record["status"].endswith("PLAN_ONLY") or record["status"] == "PLAN_ONLY_NOT_INSTALLED_BY_THIS_TOOL"
    assert all(value is False for value in safety.values())
    serialized = str(record).lower()
    assert "curl -fssl" not in serialized
    assert "| sh" not in serialized
    assert "guaranteed" not in serialized


def test_ollama_linux_plan_is_non_executing_and_uses_official_authority():
    record = planner.build_plan("ollama", signals("linux"))
    assert_plan_only(record)
    assert record["authority"]["linux"].startswith("https://docs.ollama.com/")
    assert any("verify" in step.lower() for step in record["plan"]["verification"])


def test_ollama_windows_and_macos_have_platform_specific_paths():
    win = planner.build_plan("ollama", signals("windows"))
    mac = planner.build_plan("ollama", signals("macos"))
    assert_plan_only(win)
    assert_plan_only(mac)
    assert "windows" in win["authority"]
    assert "macos" in mac["authority"]
    assert any("installed-app" in step.lower() or "windows apps" in step.lower() for step in win["plan"]["recovery"])


def test_llama_cpp_reports_cmake_gap_without_installing_it():
    record = planner.build_plan("llama.cpp", signals("linux", cmake=False))
    assert_plan_only(record)
    assert record["authority"]["homepage"] == "https://github.com/ggml-org/llama.cpp"
    assert "CMake not detected" in record["plan"]["prerequisite_gaps"][0]


def test_vllm_native_windows_fails_honest():
    record = planner.build_plan("vllm", signals("windows"), "nvidia")
    assert_plan_only(record)
    assert record["status"] == "NATIVE_WINDOWS_NOT_RECOMMENDED_PLAN_ONLY"
    assert "wsl" in record["plan"]["steps"][0].lower()


def test_vllm_linux_does_not_embed_stale_install_command():
    record = planner.build_plan("vllm", signals("linux", uv=True), "amd")
    assert_plan_only(record)
    assert record["requested_accelerator"] == "amd"
    serialized = str(record)
    assert "pip install vllm" not in serialized
    assert "uv pip install" not in serialized
    assert "current upstream installation command" in serialized


def test_unknown_platform_fails_honest():
    record = planner.build_plan("ollama", signals("plan9"))
    assert_plan_only(record)
    assert record["status"] == "UNSUPPORTED_PLATFORM_PLAN_ONLY"


def test_canonical_backend_set_is_narrow():
    assert planner.BACKENDS == ("ollama", "llama.cpp", "vllm")
