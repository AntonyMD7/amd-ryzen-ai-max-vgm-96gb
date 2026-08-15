#!/usr/bin/env python3
"""F-03 Local AI Doctor: bounded Ollama acceptance probe.

The default path performs only GET /api/version and GET /api/tags against a
loopback Ollama endpoint. Optional exact-model inference requires an explicit
flag and uses POST /api/generate with a fixed tiny prompt, stream=false and
keep_alive=0. The probe never pulls, creates, copies, deletes or pushes models.
It retains hashes/metrics rather than generated response text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

VERSION = "0.3.0"
DEFAULT_BASE_URL = "http://127.0.0.1:11434"
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,199}(?::[A-Za-z0-9._-]{1,80})?$")


class OllamaAcceptanceError(RuntimeError):
    pass


def _base_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS:
        raise OllamaAcceptanceError("endpoint must be an explicit loopback HTTP Ollama URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise OllamaAcceptanceError("credentials/query/fragment are not permitted in endpoint")
    if parsed.path not in ("", "/"):
        raise OllamaAcceptanceError("endpoint must not contain an API path")
    return value.rstrip("/")


def _json_request(base: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if path not in {"/api/version", "/api/tags", "/api/generate"}:
        raise OllamaAcceptanceError("endpoint path is not allowlisted")
    data = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    request = Request(
        base + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json", "User-Agent": f"dais-local-ai-doctor/{VERSION}"},
    )
    try:
        with urlopen(request, timeout=8) as response:  # nosec B310: base is loopback-only and validated
            if response.status != 200:
                raise OllamaAcceptanceError(f"unexpected HTTP status {response.status}")
            body = response.read(2 * 1024 * 1024 + 1)
    except OSError as exc:
        raise OllamaAcceptanceError(f"Ollama loopback request failed: {exc.__class__.__name__}") from exc
    if len(body) > 2 * 1024 * 1024:
        raise OllamaAcceptanceError("Ollama response exceeded bounded size")
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OllamaAcceptanceError("Ollama response was not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise OllamaAcceptanceError("Ollama response must be a JSON object")
    return parsed


def probe(base_url: str = DEFAULT_BASE_URL, *, model: str | None = None, allow_inference: bool = False) -> dict[str, Any]:
    base = _base_url(base_url)
    if model is not None and not MODEL_RE.fullmatch(model):
        raise OllamaAcceptanceError("model identifier is invalid")
    if allow_inference and model is None:
        raise OllamaAcceptanceError("explicit model is required when inference is allowed")

    version_record = _json_request(base, "GET", "/api/version")
    tags_record = _json_request(base, "GET", "/api/tags")
    runtime_version = version_record.get("version")
    models = tags_record.get("models", [])
    if not isinstance(runtime_version, str) or not runtime_version.strip():
        raise OllamaAcceptanceError("Ollama version response is missing version")
    if not isinstance(models, list):
        raise OllamaAcceptanceError("Ollama tags response is missing models list")

    requested: dict[str, Any] | None = None
    if model is not None:
        for item in models:
            if not isinstance(item, dict):
                continue
            candidate = str(item.get("model") or item.get("name") or "")
            if candidate == model:
                digest = item.get("digest")
                requested = {
                    "model": model,
                    "present": True,
                    "digest": digest if isinstance(digest, str) and len(digest) <= 200 else None,
                    "size_bytes": item.get("size") if isinstance(item.get("size"), int) else None,
                }
                break
        if requested is None:
            requested = {"model": model, "present": False, "digest": None, "size_bytes": None}

    inference: dict[str, Any] = {
        "requested": bool(allow_inference),
        "performed": False,
        "response_text_retained": False,
        "response_sha256": None,
        "done": None,
        "done_reason": None,
        "total_duration_ns": None,
        "eval_count": None,
    }
    if allow_inference:
        assert model is not None
        if not requested or not requested["present"]:
            raise OllamaAcceptanceError("requested model is not already installed; download is forbidden")
        result = _json_request(
            base,
            "POST",
            "/api/generate",
            {
                "model": model,
                "prompt": "Reply with the single word READY.",
                "stream": False,
                "keep_alive": 0,
                "options": {"temperature": 0, "num_predict": 8},
            },
        )
        response_text = result.get("response")
        if not isinstance(response_text, str):
            raise OllamaAcceptanceError("generate response is missing response text")
        inference.update({
            "performed": True,
            "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
            "done": result.get("done") if isinstance(result.get("done"), bool) else None,
            "done_reason": result.get("done_reason") if isinstance(result.get("done_reason"), str) else None,
            "total_duration_ns": result.get("total_duration") if isinstance(result.get("total_duration"), int) else None,
            "eval_count": result.get("eval_count") if isinstance(result.get("eval_count"), int) else None,
        })

    return {
        "schema_version": "0.3",
        "evidence_type": "local-ai-doctor-ollama-bounded-acceptance",
        "probe": {"name": "ollama_bounded_acceptance.py", "version": VERSION},
        "transport": "LOOPBACK_HTTP_ONLY",
        "runtime": {"name": "ollama", "version": runtime_version},
        "installed_model_count": len(models),
        "requested_model": requested,
        "inference": inference,
        "claims": {
            "ollama_api_reachable": True,
            "exact_model_present": bool(requested and requested["present"]),
            "exact_model_inference_exercised": inference["performed"],
            "accelerator_support_verified": False,
            "model_quality_verified": False,
            "performance_characterized": False,
            "production_ready": False,
        },
        "safety": {
            "non_loopback_network_allowed": False,
            "model_download_allowed": False,
            "model_create_allowed": False,
            "model_delete_allowed": False,
            "model_push_allowed": False,
            "generated_text_retained": False,
            "configuration_changed": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded loopback Ollama acceptance probe")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model")
    parser.add_argument("--allow-inference", action="store_true")
    args = parser.parse_args()
    try:
        result = probe(args.base_url, model=args.model, allow_inference=args.allow_inference)
    except OllamaAcceptanceError as exc:
        print(json.dumps({"status": "REJECTED_OR_UNAVAILABLE", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
