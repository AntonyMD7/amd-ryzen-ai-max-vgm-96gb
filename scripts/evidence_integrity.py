#!/usr/bin/env python3
"""Universal Evidence v0.2 integrity sidecar helper.

This helper validates a DAIS Universal Evidence v0.1 JSON record, applies a small
set of semantic/privacy guards, and binds the exact evidence bytes plus a
project-defined sorted-JSON diagnostic representation to SHA-256 digests. When
an artifact root is explicitly supplied it can also verify declared artifact
hashes under that root.

This is *not* a digital-signature implementation. It does not establish producer
identity, trusted time, authorization truth, provenance truth, or external
attestation conformance. Future signing should prefer a reviewed standard such
as DSSE rather than treating this project's sorted JSON as a signature format.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable

import jsonschema

VERSION = "0.2.0"
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = ROOT / "schemas" / "universal-evidence-v0.1.schema.json"
MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024


class EvidenceIntegrityError(ValueError):
    pass


SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private-key-material", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----", re.I)),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("api-key-like", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("bearer-token", re.compile(r"\bbearer\s+[A-Za-z0-9._~-]{16,}\b", re.I)),
    ("email-address", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("mac-address", re.compile(r"\b(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2}\b", re.I)),
    ("private-ipv4-10", re.compile(r"\b10(?:\.\d{1,3}){3}\b")),
    ("private-ipv4-192", re.compile(r"\b192\.168(?:\.\d{1,3}){2}\b")),
    ("private-ipv4-172", re.compile(r"\b172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2}\b")),
    ("cgnat-ipv4", re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])(?:\.\d{1,3}){2}\b")),
    ("linux-user-path", re.compile(r"/home/[^/\s]+/", re.I)),
    ("macos-user-path", re.compile(r"/Users/[^/\s]+/", re.I)),
    ("windows-user-path", re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+\\", re.I)),
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _iter_strings(value: Any, path: str = "$") -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from _iter_strings(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_strings(item, f"{path}[{index}]")


def _parse_evidence_bytes(raw: bytes) -> dict[str, Any]:
    if len(raw) > MAX_EVIDENCE_BYTES:
        raise EvidenceIntegrityError("evidence exceeds size limit")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceIntegrityError("evidence must be UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise EvidenceIntegrityError("evidence must be a JSON object")
    return value


def _validate_schema(record: dict[str, Any]) -> None:
    schema = json.loads(EVIDENCE_SCHEMA.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda item: list(item.absolute_path))
    if errors:
        error = errors[0]
        path = "$" + "".join(
            f"[{part}]" if isinstance(part, int) else f".{part}"
            for part in error.absolute_path
        )
        raise EvidenceIntegrityError(f"schema validation failed at {path}: {error.message}")


def _validate_semantics(record: dict[str, Any]) -> None:
    evidence_type = record["evidence_type"]
    operation = record["operation"]
    classification = operation["classification"]
    result = record["result"]["status"]

    if evidence_type == "mutation" and classification != "MUTATING":
        raise EvidenceIntegrityError("mutation evidence requires MUTATING operation classification")
    if classification == "READ_ONLY" and operation.get("intended_change") is not None:
        raise EvidenceIntegrityError("READ_ONLY operation cannot declare an intended change")
    if classification == "MUTATING" and result == "PASS" and record.get("post_state") is None:
        raise EvidenceIntegrityError("successful MUTATING evidence requires a post_state")
    if result == "PASS" and any(item.get("status") == "FAIL" for item in record.get("acceptance", [])):
        raise EvidenceIntegrityError("overall PASS conflicts with failed acceptance evidence")


def _privacy_prefilter(record: dict[str, Any]) -> None:
    hits: list[str] = []
    for path, value in _iter_strings(record):
        for label, pattern in SENSITIVE_PATTERNS:
            if pattern.search(value):
                hits.append(f"{path}:{label}")
    if hits:
        raise EvidenceIntegrityError("public evidence privacy prefilter rejected: " + ", ".join(hits[:10]))


def _normalized_bytes(record: dict[str, Any]) -> bytes:
    # Project-local diagnostic normalization only. This is intentionally NOT
    # presented as RFC 8785/JCS conformance and must not become a signature format.
    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _safe_artifact_path(root: Path, name: str) -> Path:
    rel = Path(name)
    if rel.is_absolute() or not rel.parts or any(part in {"", ".", ".."} for part in rel.parts):
        raise EvidenceIntegrityError(f"unsafe artifact name: {name}")
    current = root
    for part in rel.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise EvidenceIntegrityError(f"symlink artifact path refused: {name}")
    resolved = (root / rel).resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise EvidenceIntegrityError(f"artifact escapes root: {name}") from exc
    if not resolved.is_file() or resolved.is_symlink():
        raise EvidenceIntegrityError(f"artifact is not a regular file: {name}")
    if resolved.stat().st_size > MAX_ARTIFACT_BYTES:
        raise EvidenceIntegrityError(f"artifact exceeds verification size limit: {name}")
    return resolved


def _artifact_bindings(record: dict[str, Any], artifact_root: Path | None) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    root = artifact_root.resolve(strict=True) if artifact_root is not None else None
    for artifact in record.get("artifacts", []):
        item: dict[str, Any] = {
            "name": artifact["name"],
            "declared_sha256": artifact["sha256"].lower(),
            "verified_from_root": None,
        }
        if root is not None:
            path = _safe_artifact_path(root, artifact["name"])
            actual = _sha256(path.read_bytes())
            if actual != artifact["sha256"].lower():
                raise EvidenceIntegrityError(f"artifact digest mismatch: {artifact['name']}")
            item["verified_from_root"] = True
            item["observed_sha256"] = actual
        bindings.append(item)
    return bindings


def create_sidecar(raw: bytes, *, artifact_root: Path | None = None) -> dict[str, Any]:
    record = _parse_evidence_bytes(raw)
    _validate_schema(record)
    _validate_semantics(record)
    _privacy_prefilter(record)
    normalized = _normalized_bytes(record)
    return {
        "schema_version": "0.2",
        "sidecar_type": "dais-universal-evidence-integrity",
        "evidence_id": record["evidence_id"],
        "evidence_schema_version": record["schema_version"],
        "hashes": {
            "exact_bytes_sha256": _sha256(raw),
            "dais_sorted_json_v0_1_sha256": _sha256(normalized),
        },
        "normalization": {
            "profile": "DAIS_SORTED_JSON_V0.1",
            "rfc8785_jcs_conformance_claimed": False,
            "signature_format": False,
        },
        "artifact_bindings": _artifact_bindings(record, artifact_root),
        "checks": {
            "schema_validation": "PASS",
            "semantic_consistency": "PASS",
            "privacy_prefilter": "PASS",
        },
        "trust": {
            "signature_present": False,
            "signature_verified": False,
            "producer_identity_verified": False,
            "trusted_timestamp_verified": False,
            "authorization_truth_verified": False,
            "provenance_truth_verified": False,
            "evidence_truth_verified": False,
        },
        "limitations": [
            "SHA-256 integrity can detect changed bytes but does not identify who produced the evidence.",
            "DAIS_SORTED_JSON_V0.1 is a project diagnostic normalization profile, not RFC 8785/JCS conformance.",
            "A future signing layer should use a reviewed typed-envelope/signature standard such as DSSE rather than treating this sidecar as a signature.",
            "Schema, semantic and privacy-prefilter success do not prove that reported observations are true.",
        ],
    }


def verify_sidecar(raw: bytes, sidecar: dict[str, Any], *, artifact_root: Path | None = None) -> dict[str, Any]:
    expected = create_sidecar(raw, artifact_root=artifact_root)
    if sidecar.get("sidecar_type") != "dais-universal-evidence-integrity":
        raise EvidenceIntegrityError("unknown sidecar type")
    if sidecar.get("evidence_id") != expected["evidence_id"]:
        raise EvidenceIntegrityError("evidence_id mismatch")
    supplied_hashes = sidecar.get("hashes", {})
    for name, digest in expected["hashes"].items():
        if supplied_hashes.get(name) != digest:
            raise EvidenceIntegrityError(f"integrity digest mismatch: {name}")

    supplied_bindings = sidecar.get("artifact_bindings", [])
    if len(supplied_bindings) != len(expected["artifact_bindings"]):
        raise EvidenceIntegrityError("artifact binding count mismatch")
    for supplied, current in zip(supplied_bindings, expected["artifact_bindings"]):
        if supplied.get("name") != current.get("name") or supplied.get("declared_sha256") != current.get("declared_sha256"):
            raise EvidenceIntegrityError("artifact binding mismatch")
        if artifact_root is not None and current.get("verified_from_root") is not True:
            raise EvidenceIntegrityError("artifact root verification was not completed")

    return {
        "status": "INTEGRITY_VERIFIED_NOT_TRUST_VERIFIED",
        "evidence_id": expected["evidence_id"],
        "exact_bytes_match": True,
        "normalized_content_match": True,
        "artifact_bindings_match": True,
        "signature_verified": False,
        "producer_identity_verified": False,
        "evidence_truth_verified": False,
    }


def _read_bytes(path: Path) -> bytes:
    data = path.read_bytes()
    if len(data) > MAX_EVIDENCE_BYTES:
        raise EvidenceIntegrityError("evidence exceeds size limit")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or verify a fail-honest Universal Evidence integrity sidecar")
    sub = parser.add_subparsers(dest="mode", required=True)

    create = sub.add_parser("create")
    create.add_argument("evidence", type=Path)
    create.add_argument("--artifact-root", type=Path)
    create.add_argument("--output", type=Path)

    verify = sub.add_parser("verify")
    verify.add_argument("evidence", type=Path)
    verify.add_argument("sidecar", type=Path)
    verify.add_argument("--artifact-root", type=Path)

    args = parser.parse_args()
    try:
        raw = _read_bytes(args.evidence)
        if args.mode == "create":
            result = create_sidecar(raw, artifact_root=args.artifact_root)
            text = json.dumps(result, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.write_text(text, encoding="utf-8")
            else:
                print(text, end="")
        else:
            sidecar = json.loads(args.sidecar.read_text(encoding="utf-8"))
            result = verify_sidecar(raw, sidecar, artifact_root=args.artifact_root)
            print(json.dumps(result, indent=2, sort_keys=True))
    except (OSError, json.JSONDecodeError, EvidenceIntegrityError) as exc:
        print(json.dumps({"status": "REJECTED", "reason": str(exc)}, indent=2, sort_keys=True))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
