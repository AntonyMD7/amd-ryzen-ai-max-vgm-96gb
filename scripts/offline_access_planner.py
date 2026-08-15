#!/usr/bin/env python3
"""Metadata-only reference primitives for offline/low-bandwidth access.

No content is downloaded, synchronized, translated, indexed, served, compressed
or written. The tool plans package/sync/evidence behavior over explicit metadata.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class OfflinePlanError(ValueError):
    pass


SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE.fullmatch(value):
        raise OfflinePlanError(f"{name} must be a bounded identifier")
    return value


def _digest(value: Any, name: str = "sha256") -> str:
    if not isinstance(value, str) or not HEX64.fullmatch(value):
        raise OfflinePlanError(f"{name} must be a SHA-256 hex digest")
    return value.lower()


def _nonneg(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OfflinePlanError(f"{name} must be a non-negative integer")
    return value


def knowledge_package(data: dict[str, Any]) -> dict[str, Any]:
    package_id = _id(data.get("package_id"), "package_id")
    version = _id(data.get("version"), "version")
    digest = _digest(data.get("sha256"))
    license_id = data.get("license_id")
    if license_id is not None:
        license_id = _id(license_id, "license_id")
    provenance = data.get("provenance_documented")
    if not isinstance(provenance, bool):
        raise OfflinePlanError("provenance_documented must be boolean")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-101",
        "package_id": package_id,
        "version": version,
        "sha256": digest,
        "license_id": license_id,
        "status": "REVIEW_REQUIRED" if not license_id or not provenance else "METADATA_PREFLIGHT_PASSES",
        "requirements": ["immutable source", "offline-readable index", "license/provenance", "update manifest", "integrity verification", "size disclosed"],
        "execution": {"content_downloaded": False, "package_written": False, "server_started": False},
        "semantics": {"content_accuracy_verified": False, "redistribution_rights_proven": False},
    }


def low_bandwidth_web(data: dict[str, Any]) -> dict[str, Any]:
    initial_bytes = _nonneg(data.get("initial_payload_bytes"), "initial_payload_bytes")
    js_bytes = _nonneg(data.get("javascript_bytes"), "javascript_bytes")
    works_without_js = data.get("core_task_without_js")
    caches_core = data.get("core_assets_cacheable")
    if not isinstance(works_without_js, bool) or not isinstance(caches_core, bool):
        raise OfflinePlanError("core_task_without_js and core_assets_cacheable must be boolean")
    findings = []
    if initial_bytes > 500_000:
        findings.append("INITIAL_PAYLOAD_REVIEW")
    if js_bytes > 250_000:
        findings.append("JAVASCRIPT_BUDGET_REVIEW")
    if not works_without_js:
        findings.append("NO_SCRIPT_CORE_PATH_MISSING")
    if not caches_core:
        findings.append("CORE_CACHE_STRATEGY_MISSING")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-102",
        "findings": findings,
        "status": "REVIEW_REQUIRED" if findings else "REFERENCE_BUDGET_PREFILTER_PASSES",
        "note": "Byte budgets are project policy examples, not universal web standards.",
        "execution": {"url_fetched": False, "browser_opened": False, "cache_written": False},
    }


def reference_manifest(data: dict[str, Any]) -> dict[str, Any]:
    kind = data.get("kind")
    roadmap = {"education": "P-103", "emergency": "P-104"}.get(kind)
    if roadmap is None:
        raise OfflinePlanError("kind must be education or emergency")
    source_id = _id(data.get("source_id"), "source_id")
    version = _id(data.get("version"), "version")
    reviewed_at = _id(data.get("reviewed_at"), "reviewed_at")
    return {
        "schema_version": "0.1",
        "roadmap_id": roadmap,
        "kind": kind,
        "source_id": source_id,
        "version": version,
        "reviewed_at": reviewed_at,
        "requirements": ["authoritative source", "version/date visible offline", "limitations", "update/replacement path", "no hidden network dependency"],
        "semantics": {"reference_content_included": False, "currency_or_accuracy_certified": False},
    }


def translation_pack(data: dict[str, Any]) -> dict[str, Any]:
    model_or_ruleset = _id(data.get("engine_id"), "engine_id")
    source_language = _id(data.get("source_language"), "source_language")
    target_language = _id(data.get("target_language"), "target_language")
    digest = _digest(data.get("artifact_sha256"), "artifact_sha256")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-105",
        "engine_id": model_or_ruleset,
        "source_language": source_language,
        "target_language": target_language,
        "artifact_sha256": digest,
        "requirements": ["local execution", "human validation path", "critical-term glossary", "source text preservation", "model/ruleset license review"],
        "execution": {"translation_run": False, "artifact_downloaded": False},
        "semantics": {"translation_quality_certified": False},
    }


def offline_rag(data: dict[str, Any]) -> dict[str, Any]:
    corpus_id = _id(data.get("corpus_id"), "corpus_id")
    document_count = _nonneg(data.get("document_count"), "document_count")
    embedding_engine = _id(data.get("embedding_engine"), "embedding_engine")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-106",
        "corpus_id": corpus_id,
        "document_count": document_count,
        "embedding_engine": embedding_engine,
        "requirements": ["local corpus boundary", "chunk provenance", "index version", "retrieval citations", "insufficient-evidence refusal", "offline rebuild procedure"],
        "execution": {"documents_read": False, "embeddings_created": False, "index_written": False, "model_called": False},
    }


def distribution_plan(data: dict[str, Any]) -> dict[str, Any]:
    total_bytes = _nonneg(data.get("total_bytes"), "total_bytes")
    chunk_bytes = _nonneg(data.get("chunk_bytes"), "chunk_bytes")
    if chunk_bytes <= 0:
        raise OfflinePlanError("chunk_bytes must be > 0")
    chunk_count = (total_bytes + chunk_bytes - 1) // chunk_bytes if total_bytes else 0
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-107",
        "total_bytes": total_bytes,
        "chunk_bytes": chunk_bytes,
        "chunk_count": chunk_count,
        "requirements": ["per-chunk digest", "manifest digest", "resume support", "version pin", "atomic activation after verification"],
        "execution": {"content_compressed": False, "chunks_written": False, "network_used": False},
        "semantics": {"compression_ratio_predicted": False},
    }


def sync_plan(data: dict[str, Any]) -> dict[str, Any]:
    local_revision = _id(data.get("local_revision"), "local_revision")
    remote_revision = _id(data.get("remote_revision"), "remote_revision")
    same_base = data.get("same_known_base")
    local_changed = data.get("local_changed")
    remote_changed = data.get("remote_changed")
    if not all(isinstance(v, bool) for v in (same_base, local_changed, remote_changed)):
        raise OfflinePlanError("sync state flags must be booleans")
    if not same_base:
        disposition = "RECONCILIATION_REQUIRED_UNKNOWN_BASE"
    elif local_changed and remote_changed:
        disposition = "CONFLICT_REQUIRES_POLICY_OR_HUMAN_REVIEW"
    elif local_changed:
        disposition = "LOCAL_AHEAD_PROPOSE_PUSH"
    elif remote_changed:
        disposition = "REMOTE_AHEAD_PROPOSE_PULL"
    else:
        disposition = "NO_CHANGE"
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-108",
        "local_revision": local_revision,
        "remote_revision": remote_revision,
        "disposition": disposition,
        "requirements": ["content digests", "atomic writes", "conflict retention", "retry/idempotency", "do not use timestamp alone as authority"],
        "execution": {"sync_run": False, "local_written": False, "remote_written": False},
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    fn = {
        "knowledge_package": knowledge_package,
        "low_bandwidth_web": low_bandwidth_web,
        "reference_manifest": reference_manifest,
        "translation_pack": translation_pack,
        "offline_rag": offline_rag,
        "distribution": distribution_plan,
        "sync": sync_plan,
    }.get(mode)
    if fn is None:
        raise OfflinePlanError("unsupported mode")
    return fn(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(evaluate(request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
