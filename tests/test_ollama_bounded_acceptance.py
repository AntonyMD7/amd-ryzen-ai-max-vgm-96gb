from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
from threading import Thread

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from ollama_bounded_acceptance import OllamaAcceptanceError, probe


class Handler(BaseHTTPRequestHandler):
    seen: list[tuple[str, str]] = []

    def log_message(self, format, *args):  # noqa: A003
        return

    def _send(self, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        self.__class__.seen.append(("GET", self.path))
        if self.path == "/api/version":
            self._send({"version": "0.test"})
        elif self.path == "/api/tags":
            self._send({"models": [{"name": "test:latest", "model": "test:latest", "digest": "abc123", "size": 1234}]})
        else:
            self.send_error(404)

    def do_POST(self):  # noqa: N802
        self.__class__.seen.append(("POST", self.path))
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if self.path != "/api/generate":
            self.send_error(404)
            return
        assert payload == {
            "model": "test:latest",
            "prompt": "Reply with the single word READY.",
            "stream": False,
            "keep_alive": 0,
            "options": {"temperature": 0, "num_predict": 8},
        }
        self._send({
            "model": "test:latest",
            "response": "READY",
            "done": True,
            "done_reason": "stop",
            "total_duration": 100,
            "eval_count": 1,
        })


@pytest.fixture
def mock_ollama():
    Handler.seen = []
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()


def test_default_probe_is_inventory_only_and_retains_no_model_list(mock_ollama):
    result = probe(mock_ollama)
    assert result["runtime"] == {"name": "ollama", "version": "0.test"}
    assert result["installed_model_count"] == 1
    assert result["requested_model"] is None
    assert result["inference"]["performed"] is False
    assert Handler.seen == [("GET", "/api/version"), ("GET", "/api/tags")]
    serialized = json.dumps(result)
    assert "test:latest" not in serialized


def test_requested_model_presence_is_bound_to_exact_identifier(mock_ollama):
    result = probe(mock_ollama, model="test:latest")
    assert result["requested_model"]["present"] is True
    assert result["requested_model"]["digest"] == "abc123"
    assert result["claims"]["exact_model_inference_exercised"] is False
    assert Handler.seen == [("GET", "/api/version"), ("GET", "/api/tags")]


def test_explicit_inference_runs_fixed_bounded_generate_and_hashes_text(mock_ollama):
    result = probe(mock_ollama, model="test:latest", allow_inference=True)
    assert result["inference"]["performed"] is True
    assert result["inference"]["response_text_retained"] is False
    assert len(result["inference"]["response_sha256"]) == 64
    assert result["claims"]["performance_characterized"] is False
    assert Handler.seen == [
        ("GET", "/api/version"),
        ("GET", "/api/tags"),
        ("POST", "/api/generate"),
    ]


def test_non_loopback_endpoint_is_refused_before_network():
    with pytest.raises(OllamaAcceptanceError, match="loopback"):
        probe("https://example.com:11434")


def test_inference_requires_preinstalled_exact_model(mock_ollama):
    with pytest.raises(OllamaAcceptanceError, match="not already installed"):
        probe(mock_ollama, model="missing:latest", allow_inference=True)
    assert Handler.seen == [("GET", "/api/version"), ("GET", "/api/tags")]


def test_model_identifier_is_strictly_bounded(mock_ollama):
    with pytest.raises(OllamaAcceptanceError, match="identifier"):
        probe(mock_ollama, model="bad model;rm -rf /")


def test_source_has_no_model_mutation_endpoints():
    source = (ROOT / "scripts" / "ollama_bounded_acceptance.py").read_text(encoding="utf-8")
    for forbidden in ("/api/pull", "/api/create", "/api/delete", "/api/push", "/api/copy"):
        assert forbidden not in source
