#!/usr/bin/env python3
"""Evaluate normalized signature/provenance observations against an exact trust profile.

This module does not perform cryptography, contact Sigstore, query Rekor, fetch
TUF roots, validate OIDC tokens, or establish SLSA conformance. It is a policy
layer that consumes results from a separately trusted verifier and refuses to
turn cryptographic identity into artifact quality or semantic truth.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
PROFILE_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")
ALLOWED_TIMESTAMP_SOURCES = {"SIGSTORE_TSA", "REKOR_V2_TSA"}
FORBIDDEN_EXACT_IDENTITY_TOKENS = ("*", "?", "regex:")


class TrustPolicyError(ValueError):
    pass


def _require_bool(value: object, field: str) -> bool:
    if not isinstance(value, bool):
        raise TrustPolicyError(f"{field} must be boolean")
    return value


def _require_exact_text(value: object, field: str, max_len: int = 500) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise TrustPolicyError(f"{field} must be a non-empty bounded string")
    text = value.strip()
    lowered = text.lower()
    if any(token in lowered for token in FORBIDDEN_EXACT_IDENTITY_TOKENS):
        raise TrustPolicyError(f"{field} must be exact; wildcard/regex policy is not accepted")
    return text


def validate_profile(profile: dict[str, Any]) -> None:
    expected_top = {"schema_version", "profile_id", "artifact", "signer", "transparency", "timestamp", "provenance", "claims"}
    if set(profile) != expected_top:
        raise TrustPolicyError(f"trust profile fields must be exactly {sorted(expected_top)}")
    if profile.get("schema_version") != "0.1":
        raise TrustPolicyError("unsupported trust-profile schema_version")
    if not isinstance(profile.get("profile_id"), str) or not PROFILE_ID.fullmatch(profile["profile_id"]):
        raise TrustPolicyError("invalid profile_id")

    artifact = profile.get("artifact")
    if not isinstance(artifact, dict) or set(artifact) != {"sha256"}:
        raise TrustPolicyError("artifact must contain only sha256")
    if not isinstance(artifact["sha256"], str) or not SHA256.fullmatch(artifact["sha256"]):
        raise TrustPolicyError("artifact.sha256 must be lowercase SHA-256")

    signer = profile.get("signer")
    if not isinstance(signer, dict) or set(signer) != {"mode", "exact_identity", "exact_oidc_issuer"}:
        raise TrustPolicyError("signer fields are invalid")
    if signer.get("mode") != "SIGSTORE_KEYLESS":
        raise TrustPolicyError("v0.1 supports SIGSTORE_KEYLESS policy only")
    _require_exact_text(signer.get("exact_identity"), "signer.exact_identity", 300)
    issuer = _require_exact_text(signer.get("exact_oidc_issuer"), "signer.exact_oidc_issuer", 300)
    if not issuer.startswith("https://"):
        raise TrustPolicyError("signer.exact_oidc_issuer must use https://")

    transparency = profile.get("transparency")
    if not isinstance(transparency, dict) or set(transparency) != {"required"}:
        raise TrustPolicyError("transparency must contain only required")
    _require_bool(transparency.get("required"), "transparency.required")

    timestamp = profile.get("timestamp")
    if not isinstance(timestamp, dict) or set(timestamp) != {"required", "accepted_sources"}:
        raise TrustPolicyError("timestamp fields are invalid")
    timestamp_required = _require_bool(timestamp.get("required"), "timestamp.required")
    sources = timestamp.get("accepted_sources")
    if not isinstance(sources, list) or any(source not in ALLOWED_TIMESTAMP_SOURCES for source in sources):
        raise TrustPolicyError("timestamp.accepted_sources contains an unsupported source")
    if len(sources) != len(set(sources)):
        raise TrustPolicyError("timestamp.accepted_sources must be unique")
    if timestamp_required and not sources:
        raise TrustPolicyError("timestamp.required=true requires at least one accepted source")

    provenance = profile.get("provenance")
    if not isinstance(provenance, dict) or set(provenance) != {"builder_id_required", "allowed_builder_ids"}:
        raise TrustPolicyError("provenance fields are invalid")
    builder_required = _require_bool(provenance.get("builder_id_required"), "provenance.builder_id_required")
    builders = provenance.get("allowed_builder_ids")
    if not isinstance(builders, list):
        raise TrustPolicyError("provenance.allowed_builder_ids must be an array")
    exact_builders = [_require_exact_text(value, "provenance.allowed_builder_ids[]") for value in builders]
    if len(exact_builders) != len(set(exact_builders)):
        raise TrustPolicyError("provenance.allowed_builder_ids must be unique")
    if builder_required and not builders:
        raise TrustPolicyError("builder_id_required=true requires allowed_builder_ids")

    claims = profile.get("claims")
    if not isinstance(claims, dict) or set(claims) != {"artifact_goodness_inferred", "semantic_truth_inferred"}:
        raise TrustPolicyError("claims fields are invalid")
    if claims.get("artifact_goodness_inferred") is not False or claims.get("semantic_truth_inferred") is not False:
        raise TrustPolicyError("trust profile must not infer artifact goodness or semantic truth")


def validate_observation(observation: dict[str, Any]) -> None:
    expected = {
        "artifact_sha256",
        "cryptographic_signature_verified",
        "certificate_identity",
        "certificate_oidc_issuer",
        "transparency_verified",
        "timestamp_verified",
        "timestamp_source",
        "provenance_verified",
        "builder_id",
        "verifier",
    }
    if set(observation) != expected:
        raise TrustPolicyError(f"verification observation fields must be exactly {sorted(expected)}")
    digest = observation.get("artifact_sha256")
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        raise TrustPolicyError("observation.artifact_sha256 must be lowercase SHA-256")
    for field in ("cryptographic_signature_verified", "transparency_verified", "timestamp_verified", "provenance_verified"):
        _require_bool(observation.get(field), f"observation.{field}")
    for field in ("certificate_identity", "certificate_oidc_issuer", "verifier"):
        if not isinstance(observation.get(field), str) or len(observation[field]) > 500:
            raise TrustPolicyError(f"observation.{field} must be a bounded string")
    source = observation.get("timestamp_source")
    if source not in ALLOWED_TIMESTAMP_SOURCES | {"NONE"}:
        raise TrustPolicyError("observation.timestamp_source is unsupported")
    builder = observation.get("builder_id")
    if builder is not None and (not isinstance(builder, str) or len(builder) > 500):
        raise TrustPolicyError("observation.builder_id must be null or a bounded string")


def evaluate(profile: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    validate_profile(profile)
    validate_observation(observation)

    checks: dict[str, bool] = {
        "artifact_digest_exact": observation["artifact_sha256"] == profile["artifact"]["sha256"],
        "cryptographic_signature_verified": observation["cryptographic_signature_verified"] is True,
        "certificate_identity_exact": observation["certificate_identity"] == profile["signer"]["exact_identity"],
        "certificate_oidc_issuer_exact": observation["certificate_oidc_issuer"] == profile["signer"]["exact_oidc_issuer"],
    }

    if profile["transparency"]["required"]:
        checks["transparency_requirement"] = observation["transparency_verified"] is True
    else:
        checks["transparency_requirement"] = True

    if profile["timestamp"]["required"]:
        checks["timestamp_requirement"] = (
            observation["timestamp_verified"] is True
            and observation["timestamp_source"] in set(profile["timestamp"]["accepted_sources"])
        )
    else:
        checks["timestamp_requirement"] = True

    if profile["provenance"]["builder_id_required"]:
        checks["builder_identity_requirement"] = (
            observation["provenance_verified"] is True
            and observation["builder_id"] in set(profile["provenance"]["allowed_builder_ids"])
        )
    else:
        checks["builder_identity_requirement"] = True

    failed = sorted(name for name, passed in checks.items() if not passed)
    satisfied = not failed
    return {
        "schema_version": "0.1",
        "profile_id": profile["profile_id"],
        "policy_status": "POLICY_SATISFIED" if satisfied else "POLICY_REJECTED",
        "checks": checks,
        "failed_checks": failed,
        "cryptographic_policy_satisfied": satisfied,
        "artifact_goodness_proven": False,
        "semantic_truth_proven": False,
        "slsa_level_proven": None,
        "verifier_observation_trusted_by_this_module": False,
        "network_contact_performed": False,
        "cryptography_performed": False,
        "artifact_execution_performed": False,
    }


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TrustPolicyError(f"{path} must contain a JSON object")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", type=Path)
    parser.add_argument("observation", type=Path)
    args = parser.parse_args(argv)
    result = evaluate(load_json(args.profile), load_json(args.observation))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["cryptographic_policy_satisfied"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
