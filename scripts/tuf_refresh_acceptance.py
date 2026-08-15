#!/usr/bin/env python3
"""Run a bounded authenticated TUF refresh against the Sigstore public-good repo.

This is an F-05 supporting-acceptance utility. It bootstraps python-tuf from an
explicit root file, refreshes top-level metadata, downloads and verifies the
Sigstore trusted_root.json target, and emits sanitized evidence. It performs
network reads only and does not alter user devices or production systems.

A successful run proves only that this exact client/tool/version completed the
TUF workflow from the supplied bootstrap root at run time. It does not prove
future freshness, revocation awareness, resistance to every TUF attack, artifact
semantic goodness, production readiness, or DAIS roadmap completion.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any

DEFAULT_METADATA_URL = "https://tuf-repo-cdn.sigstore.dev/"
DEFAULT_TARGET_URL = "https://tuf-repo-cdn.sigstore.dev/targets/"
DEFAULT_TARGET = "trusted_root.json"


class TufRefreshAcceptanceError(ValueError):
    pass


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()  # noqa: S324 - Git object identity, not security digest


def _load_json_bytes(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data)
    except json.JSONDecodeError as exc:
        raise TufRefreshAcceptanceError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise TufRefreshAcceptanceError(f"{label} must contain a JSON object")
    return value


def validate_bootstrap(
    bootstrap: bytes,
    *,
    expected_git_blob_sha1: str,
    expected_root_version: int,
) -> dict[str, Any]:
    observed_blob = git_blob_sha1(bootstrap)
    if observed_blob != expected_git_blob_sha1:
        raise TufRefreshAcceptanceError(
            f"bootstrap Git blob mismatch: expected {expected_git_blob_sha1}, observed {observed_blob}"
        )
    obj = _load_json_bytes(bootstrap, "bootstrap root")
    signed = obj.get("signed")
    if not isinstance(signed, dict) or signed.get("_type") != "root":
        raise TufRefreshAcceptanceError("bootstrap is not TUF root metadata")
    if signed.get("version") != expected_root_version:
        raise TufRefreshAcceptanceError(
            f"bootstrap root version mismatch: expected {expected_root_version}, observed {signed.get('version')}"
        )
    return obj


def _positive_count(value: object, field: str) -> int:
    if not isinstance(value, list) or not value:
        raise TufRefreshAcceptanceError(f"verified target has no {field}")
    return len(value)


def run_refresh(
    *,
    bootstrap_path: Path,
    metadata_dir: Path,
    target_dir: Path,
    expected_git_blob_sha1: str,
    expected_root_version: int,
    metadata_base_url: str = DEFAULT_METADATA_URL,
    target_base_url: str = DEFAULT_TARGET_URL,
    target_name: str = DEFAULT_TARGET,
) -> dict[str, Any]:
    bootstrap = bootstrap_path.read_bytes()
    bootstrap_obj = validate_bootstrap(
        bootstrap,
        expected_git_blob_sha1=expected_git_blob_sha1,
        expected_root_version=expected_root_version,
    )

    metadata_dir.mkdir(parents=True, exist_ok=True)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Lazy import keeps pure contract tests independent of the optional network client dependency.
    from tuf.ngclient import Updater

    updater = Updater(
        metadata_dir=str(metadata_dir),
        metadata_base_url=metadata_base_url,
        target_dir=str(target_dir),
        target_base_url=target_base_url,
        bootstrap=bootstrap,
    )
    updater.refresh()

    current_root_path = metadata_dir / "root.json"
    current_root = _load_json_bytes(current_root_path.read_bytes(), "refreshed root")
    current_signed = current_root.get("signed")
    if not isinstance(current_signed, dict) or current_signed.get("_type") != "root":
        raise TufRefreshAcceptanceError("refreshed root is malformed")
    refreshed_root_version = current_signed.get("version")
    if not isinstance(refreshed_root_version, int) or refreshed_root_version <= expected_root_version:
        raise TufRefreshAcceptanceError(
            "authenticated refresh did not advance beyond the pinned bootstrap root version"
        )

    target_info = updater.get_targetinfo(target_name)
    if target_info is None:
        raise TufRefreshAcceptanceError(f"verified TUF target not found: {target_name}")
    downloaded = Path(updater.download_target(target_info))
    target_bytes = downloaded.read_bytes()
    target_obj = _load_json_bytes(target_bytes, target_name)

    media_type = target_obj.get("mediaType")
    if not isinstance(media_type, str) or not media_type.startswith("application/vnd.dev.sigstore.trustedroot.v"):
        raise TufRefreshAcceptanceError("verified target is not a supported Sigstore TrustedRoot JSON media type")

    ca_count = _positive_count(target_obj.get("certificateAuthorities"), "certificateAuthorities")
    tlog_count = _positive_count(target_obj.get("tlogs"), "tlogs")
    tsa_count = _positive_count(target_obj.get("timestampAuthorities"), "timestampAuthorities")

    return {
        "schema_version": "0.1",
        "evidence_type": "universal-evidence-tuf-refresh-supporting-acceptance",
        "tooling": {
            "client": "python-tuf",
            "client_version": importlib.metadata.version("tuf"),
        },
        "bootstrap": {
            "root_version": bootstrap_obj["signed"]["version"],
            "git_blob_sha1": git_blob_sha1(bootstrap),
            "sha256": hashlib.sha256(bootstrap).hexdigest(),
        },
        "refresh": {
            "metadata_base_url": metadata_base_url,
            "target_base_url": target_base_url,
            "refreshed_root_version": refreshed_root_version,
            "authenticated_root_chain_advanced": True,
            "top_level_refresh_succeeded": True,
        },
        "verified_target": {
            "name": target_name,
            "sha256": hashlib.sha256(target_bytes).hexdigest(),
            "size_bytes": len(target_bytes),
            "media_type": media_type,
            "certificate_authority_count": ca_count,
            "transparency_log_count": tlog_count,
            "timestamp_authority_count": tsa_count,
            "download_verified_by_tuf_metadata": True,
        },
        "scope": {
            "network_reads_performed": True,
            "user_device_mutation_performed": False,
            "production_mutation_performed": False,
            "credential_input_required": False,
        },
        "claims": {
            "future_trusted_root_freshness_proven": False,
            "future_revocation_awareness_proven": False,
            "all_tuf_attack_classes_exercised": False,
            "independent_security_review_completed": False,
            "artifact_semantic_goodness_proven": False,
            "production_readiness_proven": False,
            "roadmap_completion_proven": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-root", type=Path, required=True)
    parser.add_argument("--metadata-dir", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--expected-git-blob-sha1", required=True)
    parser.add_argument("--expected-root-version", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evidence = run_refresh(
        bootstrap_path=args.bootstrap_root,
        metadata_dir=args.metadata_dir,
        target_dir=args.target_dir,
        expected_git_blob_sha1=args.expected_git_blob_sha1,
        expected_root_version=args.expected_root_version,
    )
    rendered = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
