from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "ollama_runtime_footprint_acceptance.py"

spec = importlib.util.spec_from_file_location("ollama_runtime_footprint_acceptance", SCRIPT)
assert spec and spec.loader
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

MODEL = "smollm:135m"
DIGEST = "a" * 64
LICENSE = "Apache License Version 2.0 synthetic fixture"


def fake_request(base: str, method: str, path: str, payload=None):
    assert base == "http://127.0.0.1:11434"
    if path == "/api/tags":
        assert method == "GET" and payload is None
        return {"models": [{"model": MODEL, "digest": DIGEST, "size": 92_000_000}]}
    if path == "/api/show":
        assert method == "POST" and payload == {"model": MODEL, "verbose": False}
        return {
            "license": LICENSE,
            "capabilities": ["completion"],
            "details": {
                "format": "gguf",
                "family": "llama",
                "parameter_size": "135M",
                "quantization_level": "Q4_0",
            },
            "model_info": {
                "smollm.context_length": 2048,
                "smollm.embedding_length": 576,
            },
        }
    if path == "/api/generate":
        assert method == "POST"
        assert payload["model"] == MODEL
        assert payload["stream"] is False
        assert payload["keep_alive"] == "5m"
        assert payload["options"]["num_ctx"] == 2048
        return {
            "response": "READY",
            "done": True,
            "done_reason": "stop",
            "total_duration": 2_000_000_000,
            "load_duration": 1_000_000_000,
            "prompt_eval_count": 5,
            "prompt_eval_duration": 500_000_000,
            "eval_count": 2,
            "eval_duration": 250_000_000,
        }
    if path == "/api/ps":
        assert method == "GET" and payload is None
        return {
            "models": [{
                "name": MODEL,
                "model": MODEL,
                "digest": DIGEST,
                "size": 123_000_000,
                "size_vram": 0,
                "context_length": 2048,
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "parameter_size": "135M",
                    "quantization_level": "Q4_0",
                },
            }]
        }
    raise AssertionError(path)


def test_runtime_footprint_retains_hashes_metrics_not_sensitive_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe, "_json_request", fake_request)
    result = probe.probe(
        "http://127.0.0.1:11434",
        model=MODEL,
        num_ctx=2048,
        allow_inference=True,
    )
    assert result["runtime_footprint"]["exact_model_loaded"] is True
    assert result["runtime_footprint"]["digest_matches_installed"] is True
    assert result["runtime_footprint"]["context_length"] == 2048
    assert result["runtime_footprint"]["requested_context_observed_exactly"] is True
    assert result["runtime_footprint"]["size_vram_bytes"] == 0
    assert result["show_metadata"]["license_metadata_present"] is True
    assert result["show_metadata"]["license_text_retained"] is False
    assert len(result["show_metadata"]["license_text_sha256"]) == 64
    assert result["inference"]["response_text_retained"] is False
    assert len(result["inference"]["response_sha256"]) == 64
    assert result["inference"]["prompt_tokens_per_second_observed"] == 10.0
    assert result["inference"]["eval_tokens_per_second_observed"] == 8.0
    serialized = json.dumps(result)
    assert "READY" not in serialized
    assert LICENSE not in serialized
    assert result["claims"]["license_compatibility_verified"] is False
    assert result["claims"]["upstream_model_provenance_verified"] is False
    assert result["claims"]["accelerator_support_verified"] is False
    assert result["claims"]["performance_characterized"] is False
    assert result["claims"]["model_quality_verified"] is False
    assert result["claims"]["production_ready"] is False
    assert result["claims"]["roadmap_complete"] is False
    assert all(value is False for value in result["safety"].values())


def test_explicit_inference_authority_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe, "_json_request", fake_request)
    with pytest.raises(probe.OllamaAcceptanceError, match="allow-inference"):
        probe.probe("http://127.0.0.1:11434", model=MODEL, allow_inference=False)


@pytest.mark.parametrize("num_ctx", [0, 255, 131_073, 10_000_000])
def test_context_request_is_bounded(monkeypatch: pytest.MonkeyPatch, num_ctx: int) -> None:
    monkeypatch.setattr(probe, "_json_request", fake_request)
    with pytest.raises(probe.OllamaAcceptanceError, match="num_ctx"):
        probe.probe("http://127.0.0.1:11434", model=MODEL, num_ctx=num_ctx, allow_inference=True)


def test_non_loopback_endpoint_is_rejected_before_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(probe, "_json_request", lambda *args, **kwargs: pytest.fail("request should not run"))
    with pytest.raises(probe.OllamaAcceptanceError, match="loopback"):
        probe.probe("https://example.com", model=MODEL, allow_inference=True)


def test_missing_exact_model_fails_before_inference(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(base, method, path, payload=None):
        if path == "/api/tags":
            return {"models": [{"model": "other:latest", "digest": DIGEST, "size": 1}]}
        pytest.fail(f"unexpected path after missing model: {path}")

    monkeypatch.setattr(probe, "_json_request", missing)
    with pytest.raises(probe.OllamaAcceptanceError, match="exact requested model"):
        probe.probe("http://127.0.0.1:11434", model=MODEL, allow_inference=True)


def test_loaded_digest_mismatch_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def mismatched(base, method, path, payload=None):
        value = fake_request(base, method, path, payload)
        if path == "/api/ps":
            value["models"][0]["digest"] = "b" * 64
        return value

    monkeypatch.setattr(probe, "_json_request", mismatched)
    with pytest.raises(probe.OllamaAcceptanceError, match="digest does not match"):
        probe.probe("http://127.0.0.1:11434", model=MODEL, allow_inference=True)


def test_ps_requires_one_exact_loaded_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def duplicate(base, method, path, payload=None):
        value = fake_request(base, method, path, payload)
        if path == "/api/ps":
            value["models"].append(dict(value["models"][0]))
        return value

    monkeypatch.setattr(probe, "_json_request", duplicate)
    with pytest.raises(probe.OllamaAcceptanceError, match="exact requested model"):
        probe.probe("http://127.0.0.1:11434", model=MODEL, allow_inference=True)


def test_show_metadata_is_allowlisted_and_bounded() -> None:
    details = probe._safe_details({
        "format": "x" * 500,
        "family": 123,
        "parameter_size": "135M",
        "quantization_level": "Q4_0",
        "unexpected": "secret",
    })
    assert set(details) == {"format", "family", "parameter_size", "quantization_level"}
    assert len(details["format"]) == 120
    assert details["family"] is None
    assert "unexpected" not in details


def test_source_has_no_model_mutation_endpoints() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    for forbidden in ("/api/pull", "/api/create", "/api/copy", "/api/delete", "/api/push"):
        assert forbidden not in source
