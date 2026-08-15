#!/usr/bin/env python3
"""F-03 Local AI Doctor: bounded exact-model runtime footprint acceptance.

This probe talks only to an explicitly validated loopback Ollama endpoint. It
requires the requested model to be already installed, performs one tiny explicit
inference to load that exact model, and then observes Ollama's /api/ps runtime
record plus bounded /api/show metadata.

Generated text and license text are hashed/length-counted but never retained. The
probe never pulls, creates, copies, deletes, pushes, or modifies a model. Runtime
footprint evidence is an observation of this exact acceptance run; it is not a
capacity guarantee, accelerator-support proof, license legal opinion, quality
assessment, performance characterization, or production-readiness claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from typing import Any
from urllib.request import Request, urlopen

from ollama_bounded_acceptance import (
    DEFAULT_BASE_URL,
    MODEL_RE,
    OllamaAcceptanceError,
    _base_url,
)

VERSION = "0.1.0"
_ALLOWED_PATHS = {"/api/tags", "/api/show", "/api/generate", "/api/ps"}
_MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def _json_request(base: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if path not in _ALLOWED_PATHS:
        raise OllamaAcceptanceError("endpoint path is not allowlisted for runtime-footprint acceptance")
    if method not in {"GET", "POST"}:
        raise OllamaAcceptanceError("HTTP method is not allowlisted")
    if (method == "GET") != (payload is None):
        raise OllamaAcceptanceError("GET must not carry a payload and POST must carry one")
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": f"dais-local-ai-doctor-footprint/{VERSION}"},
    )
    try:
        with urlopen(request, timeout=20) as response:  # nosec B310: _base_url enforces loopback HTTP only
            if response.status != 200:
                raise OllamaAcceptanceError(f"unexpected HTTP status {response.status}")
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except OSError as exc:
        raise OllamaAcceptanceError(f"Ollama loopback request failed: {exc.__class__.__name__}") from exc
    if len(body) > _MAX_RESPONSE_BYTES:
        raise OllamaAcceptanceError("Ollama response exceeded bounded size")
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OllamaAcceptanceError("Ollama response was not valid JSON") from exc
    if not isinstance(value, dict):
        raise OllamaAcceptanceError("Ollama response must be a JSON object")
    return value


def _exact_model(items: Any, model: str, where: str) -> dict[str, Any]:
    if not isinstance(items, list):
        raise OllamaAcceptanceError(f"{where} response is missing models list")
    matches = []
    for item in items:
        if not isinstance(item, dict):
            continue
        candidate = item.get("model") or item.get("name")
        if candidate == model:
            matches.append(item)
    if len(matches) != 1:
        raise OllamaAcceptanceError(f"{where} must contain exactly one exact requested model; found {len(matches)}")
    return matches[0]


def _safe_details(value: Any) -> dict[str, str | None]:
    if not isinstance(value, dict):
        return {"format": None, "family": None, "parameter_size": None, "quantization_level": None}
    out: dict[str, str | None] = {}
    for key in ("format", "family", "parameter_size", "quantization_level"):
        item = value.get(key)
        out[key] = item[:120] if isinstance(item, str) else None
    return out


def _bounded_capabilities(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result = []
    for item in value[:32]:
        if isinstance(item, str) and 1 <= len(item) <= 64 and item.replace("-", "").replace("_", "").isalnum():
            result.append(item)
    return sorted(set(result))


def _context_lengths(model_info: Any) -> list[int]:
    if not isinstance(model_info, dict):
        return []
    values: set[int] = set()
    for key, value in model_info.items():
        if isinstance(key, str) and key.endswith(".context_length") and isinstance(value, int) and 1 <= value <= 10_000_000:
            values.add(value)
    return sorted(values)


def _metric(value: Any) -> int | None:
    return value if isinstance(value, int) and value >= 0 else None


def _rate(count: int | None, duration_ns: int | None) -> float | None:
    if count is None or duration_ns is None or duration_ns <= 0:
        return None
    rate = count / (duration_ns / 1_000_000_000)
    return round(rate, 3) if math.isfinite(rate) else None


def probe(
    base_url: str = DEFAULT_BASE_URL,
    *,
    model: str,
    num_ctx: int = 2048,
    allow_inference: bool = False,
) -> dict[str, Any]:
    base = _base_url(base_url)
    if not MODEL_RE.fullmatch(model):
        raise OllamaAcceptanceError("model identifier is invalid")
    if not allow_inference:
        raise OllamaAcceptanceError("explicit --allow-inference is required for runtime-footprint acceptance")
    if not isinstance(num_ctx, int) or not 256 <= num_ctx <= 131_072:
        raise OllamaAcceptanceError("num_ctx must be between 256 and 131072")

    tags = _json_request(base, "GET", "/api/tags")
    installed = _exact_model(tags.get("models"), model, "tags")
    installed_digest = installed.get("digest")
    if not isinstance(installed_digest, str) or not 32 <= len(installed_digest) <= 200:
        raise OllamaAcceptanceError("installed model digest is missing or malformed")
    installed_size = _metric(installed.get("size"))

    show = _json_request(base, "POST", "/api/show", {"model": model, "verbose": False})
    license_text = show.get("license")
    if not isinstance(license_text, str):
        license_text = ""
    license_bytes = license_text.encode("utf-8")
    capabilities = _bounded_capabilities(show.get("capabilities"))
    advertised_context_lengths = _context_lengths(show.get("model_info"))

    generated = _json_request(
        base,
        "POST",
        "/api/generate",
        {
            "model": model,
            "prompt": "Reply with the single word READY.",
            "stream": False,
            "keep_alive": "5m",
            "options": {"temperature": 0, "num_predict": 8, "num_ctx": num_ctx},
        },
    )
    response_text = generated.get("response")
    if not isinstance(response_text, str):
        raise OllamaAcceptanceError("generate response is missing response text")

    running = _json_request(base, "GET", "/api/ps")
    loaded = _exact_model(running.get("models"), model, "ps")
    loaded_digest = loaded.get("digest")
    if loaded_digest != installed_digest:
        raise OllamaAcceptanceError("loaded model digest does not match installed model digest")

    runtime_size = _metric(loaded.get("size"))
    size_vram = _metric(loaded.get("size_vram"))
    context_length = _metric(loaded.get("context_length"))
    if runtime_size is None or size_vram is None or context_length is None or context_length <= 0:
        raise OllamaAcceptanceError("runtime footprint response is missing size/size_vram/context_length")

    prompt_eval_count = _metric(generated.get("prompt_eval_count"))
    prompt_eval_duration = _metric(generated.get("prompt_eval_duration"))
    eval_count = _metric(generated.get("eval_count"))
    eval_duration = _metric(generated.get("eval_duration"))

    return {
        "schema_version": "0.1",
        "evidence_type": "local-ai-doctor-ollama-runtime-footprint-acceptance",
        "probe": {"name": "ollama_runtime_footprint_acceptance.py", "version": VERSION},
        "transport": "LOOPBACK_HTTP_ONLY",
        "requested_model": {
            "model": model,
            "digest": installed_digest,
            "installed_size_bytes": installed_size,
        },
        "show_metadata": {
            "details": _safe_details(show.get("details")),
            "capabilities": capabilities,
            "advertised_context_lengths": advertised_context_lengths,
            "license_metadata_present": bool(license_text.strip()),
            "license_text_length": len(license_text),
            "license_text_sha256": hashlib.sha256(license_bytes).hexdigest() if license_text else None,
            "license_text_retained": False,
        },
        "inference": {
            "performed": True,
            "requested_num_ctx": num_ctx,
            "response_text_retained": False,
            "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
            "done": generated.get("done") if isinstance(generated.get("done"), bool) else None,
            "done_reason": generated.get("done_reason") if isinstance(generated.get("done_reason"), str) else None,
            "total_duration_ns": _metric(generated.get("total_duration")),
            "load_duration_ns": _metric(generated.get("load_duration")),
            "prompt_eval_count": prompt_eval_count,
            "prompt_eval_duration_ns": prompt_eval_duration,
            "eval_count": eval_count,
            "eval_duration_ns": eval_duration,
            "prompt_tokens_per_second_observed": _rate(prompt_eval_count, prompt_eval_duration),
            "eval_tokens_per_second_observed": _rate(eval_count, eval_duration),
        },
        "runtime_footprint": {
            "exact_model_loaded": True,
            "digest_matches_installed": True,
            "size_bytes": runtime_size,
            "size_vram_bytes": size_vram,
            "context_length": context_length,
            "requested_num_ctx": num_ctx,
            "requested_context_observed_exactly": context_length == num_ctx,
            "details": _safe_details(loaded.get("details")),
        },
        "claims": {
            "exact_model_runtime_footprint_observed": True,
            "exact_model_digest_consistent": True,
            "license_metadata_observed": bool(license_text.strip()),
            "license_compatibility_verified": False,
            "upstream_model_provenance_verified": False,
            "accelerator_support_verified": False,
            "maximum_context_capacity_verified": False,
            "performance_characterized": False,
            "model_quality_verified": False,
            "production_ready": False,
            "roadmap_complete": False,
        },
        "safety": {
            "non_loopback_network_allowed": False,
            "model_download_allowed": False,
            "model_create_allowed": False,
            "model_copy_allowed": False,
            "model_delete_allowed": False,
            "model_push_allowed": False,
            "generated_text_retained": False,
            "license_text_retained": False,
            "configuration_changed": False,
        },
        "limitations": [
            "size_vram and context_length are Ollama observations for this exact loaded runtime instance, not universal hardware-capacity guarantees.",
            "Observed token rates are retained as run metrics only and do not constitute performance characterization.",
            "License metadata presence and hashing are not legal review or license-compatibility verification.",
            "Model digest consistency within Ollama does not establish upstream model provenance by itself.",
            "No accelerator-support, model-quality, production-readiness, or roadmap-completion claim is made.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded Ollama exact-model runtime footprint acceptance")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", required=True)
    parser.add_argument("--num-ctx", type=int, default=2048)
    parser.add_argument("--allow-inference", action="store_true")
    args = parser.parse_args()
    try:
        result = probe(
            args.base_url,
            model=args.model,
            num_ctx=args.num_ctx,
            allow_inference=args.allow_inference,
        )
    except OllamaAcceptanceError as exc:
        print(json.dumps({"status": "REJECTED_OR_UNAVAILABLE", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
