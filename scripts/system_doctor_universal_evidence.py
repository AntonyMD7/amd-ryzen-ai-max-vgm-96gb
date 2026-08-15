#!/usr/bin/env python3
"""Bind a bounded F-02 System Doctor acceptance record into F-05 Universal Evidence.

The binder is intentionally deterministic with respect to its explicit inputs. It
copies only the already-sanitized bounded source evidence, observation case, and
fused result into a caller-selected output directory, hashes the exact bytes, and
emits a Universal Evidence v0.1 envelope that references those artifacts.

It does not execute diagnostics, verify cryptographic signatures, establish source
truth, authorize repair, or infer production safety. Cryptographic identity/trust
is a separate verification step performed by established Sigstore tooling.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

VERSION = "0.1.0"
_COMMIT_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")


class BindingError(ValueError):
    """Fail-closed semantic input error."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require_false_map(value: Any, keys: tuple[str, ...], where: str) -> None:
    if not isinstance(value, dict):
        raise BindingError(f"{where}: expected object")
    for key in keys:
        if value.get(key) is not False:
            raise BindingError(f"{where}.{key}: must be false before public binding")


def validate_acceptance_record(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise BindingError("acceptance record must be an object")
    required = {
        "record_version",
        "source_evidence",
        "source_evidence_sha256",
        "observation_case",
        "fused_result",
        "acceptance_claims",
    }
    if set(record) != required:
        missing = required - set(record)
        extra = set(record) - required
        raise BindingError(f"acceptance record shape mismatch; missing={sorted(missing)} extra={sorted(extra)}")
    if record["record_version"] != "0.1":
        raise BindingError("unsupported acceptance record version")

    source = record["source_evidence"]
    case = record["observation_case"]
    fused = record["fused_result"]
    claims = record["acceptance_claims"]
    if not all(isinstance(item, dict) for item in (source, case, fused, claims)):
        raise BindingError("source/case/fused/claims must be objects")

    calculated_source = _sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    if record["source_evidence_sha256"] != calculated_source:
        raise BindingError("source evidence SHA-256 does not match canonical bounded source evidence")

    source_privacy = source.get("privacy")
    source_mutation = source.get("mutation")
    if not isinstance(source_privacy, dict) or not source_privacy or any(v is not False for v in source_privacy.values()):
        raise BindingError("source evidence privacy declarations must all be false")
    if not isinstance(source_mutation, dict) or not source_mutation or any(v is not False for v in source_mutation.values()):
        raise BindingError("source evidence mutation declarations must all be false")

    if claims.get("real_psutil_runtime_exercised") is not True:
        raise BindingError("real psutil runtime acceptance must be explicit")
    _require_false_map(
        claims,
        (
            "identity_data_collected",
            "network_data_collected",
            "process_data_collected",
            "mutation_performed",
            "physical_hardware_health_proven",
            "root_cause_proven",
            "production_safe_to_infer",
            "roadmap_complete",
        ),
        "acceptance_claims",
    )

    fused_claims = fused.get("claims")
    fused_mutation = fused.get("mutation")
    _require_false_map(
        fused_claims,
        (
            "root_cause_proven",
            "hardware_health_proven",
            "repair_authorized",
            "production_safe_to_infer",
            "roadmap_complete",
        ),
        "fused_result.claims",
    )
    if not isinstance(fused_mutation, dict) or not fused_mutation or any(v is not False for v in fused_mutation.values()):
        raise BindingError("fused_result.mutation declarations must all be false")

    if case.get("schema_version") != "0.1" or fused.get("schema_version") != "0.1":
        raise BindingError("F-02 case/fused schema version must be 0.1")
    if fused.get("case_id") != case.get("case_id"):
        raise BindingError("fused result case_id does not match observation case")

    case_source_digests = {
        item.get("source", {}).get("evidence_sha256")
        for item in case.get("observations", [])
        if isinstance(item, dict)
    }
    if case_source_digests != {calculated_source}:
        raise BindingError("every F-02 observation must bind to the exact bounded source evidence SHA-256")
    fused_source_digests = fused.get("source_evidence_sha256")
    if fused_source_digests != [calculated_source]:
        raise BindingError("fused result must retain exactly the bounded source evidence SHA-256")

    return record


def build_binding(
    record: Any,
    *,
    output_dir: Path,
    source_commit: str,
    evidence_id: str,
) -> dict[str, Any]:
    record = validate_acceptance_record(record)
    if not _COMMIT_RE.fullmatch(source_commit):
        raise BindingError("source_commit must be a 7..40 hex Git commit")
    if not _ID_RE.fullmatch(evidence_id):
        raise BindingError("evidence_id must be a bounded portable identifier of at least 8 characters")

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "bounded-source-evidence.json": record["source_evidence"],
        "f02-observation-case.json": record["observation_case"],
        "f02-fused-result.json": record["fused_result"],
    }
    artifact_entries: list[dict[str, str]] = []
    for name, value in artifacts.items():
        payload = _canonical_bytes(value)
        (output_dir / name).write_bytes(payload)
        artifact_entries.append(
            {
                "name": name,
                "sha256": _sha256(payload),
                "media_type": "application/json",
            }
        )

    collected_at = record["observation_case"]["observations"][0]["source"]["collected_at"]
    envelope = {
        "schema_version": "0.1",
        "evidence_id": evidence_id,
        "evidence_type": "acceptance",
        "roadmap_ids": ["F-02", "F-05", "P-002", "P-212"],
        "subject": {
            "type": "workflow",
            "id": "universal-system-doctor-bounded-psutil-acceptance",
            "version": "0.1",
        },
        "operation": {
            "classification": "VERIFY",
            "name": "F02_F05_BOUNDED_EVIDENCE_BINDING",
            "intended_change": None,
            "authorization_ref": None,
            "tool": "system_doctor_universal_evidence.py",
            "tool_version": VERSION,
        },
        "observed_at_utc": collected_at,
        "pre_state": {
            "input_contract": "bounded F-02 psutil acceptance record v0.1",
            "source_evidence_sha256": record["source_evidence_sha256"],
        },
        "result": {
            "status": "PASS",
            "exit_code": 0,
            "summary": "Bounded F-02 acceptance artifacts were copied and hash-bound into Universal Evidence; no diagnostic truth or repair authority inferred.",
        },
        "post_state": {
            "f02_overall_state": record["fused_result"]["overall_state"],
            "root_cause_proven": False,
            "hardware_health_proven": False,
            "repair_authorized": False,
            "production_safe_to_infer": False,
            "roadmap_complete": False,
        },
        "artifacts": artifact_entries,
        "rollback": {
            "required": False,
            "established": False,
            "reference": None,
            "exercised": None,
        },
        "acceptance": [
            {
                "id": "F02_BOUNDED_SOURCE_HASH_CHAIN",
                "status": "PASS",
                "evidence_ref": "bounded-source-evidence.json",
            },
            {
                "id": "F02_OBSERVATION_CASE_RETAINED",
                "status": "PASS",
                "evidence_ref": "f02-observation-case.json",
            },
            {
                "id": "F02_CONFLICT_UNCERTAINTY_FUSION_RETAINED",
                "status": "PASS",
                "evidence_ref": "f02-fused-result.json",
            },
        ],
        "safety": {
            "secrets_redacted": True,
            "private_infrastructure_redacted": True,
            "human_approval_required": False,
            "approval_present": False,
        },
        "provenance": {
            "producer": "system_doctor_universal_evidence.py",
            "source_commit": source_commit,
            "upstream_refs": [
                "https://psutil.readthedocs.io/",
                "https://in-toto.io/docs/specs/",
                "https://slsa.dev/spec/v1.2/provenance",
            ],
        },
        "limitations": [
            "Universal Evidence schema validity and artifact hashes do not prove the diagnostic observations are true.",
            "The input source digest is a content binding, not producer authentication or cryptographic trust by itself.",
            "Sigstore identity/transparency/timestamp verification is a separate acceptance step.",
            "No repair was authorized or executed and no production/device safety can be inferred.",
            "Neither F-02 nor F-05 nor any mapped roadmap item is complete from this record alone.",
        ],
    }
    (output_dir / "universal-evidence.json").write_bytes(_canonical_bytes(envelope))
    return envelope


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind bounded System Doctor acceptance into Universal Evidence")
    parser.add_argument("acceptance_record", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--evidence-id", required=True)
    args = parser.parse_args()
    try:
        record = json.loads(args.acceptance_record.read_text(encoding="utf-8"))
        envelope = build_binding(
            record,
            output_dir=args.output_dir,
            source_commit=args.source_commit,
            evidence_id=args.evidence_id,
        )
    except (OSError, json.JSONDecodeError, BindingError, KeyError, IndexError, TypeError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, indent=2))
        return 2
    print(json.dumps({
        "status": "PASS",
        "universal_evidence": str(args.output_dir / "universal-evidence.json"),
        "artifact_count": len(envelope["artifacts"]),
        "production_safe_to_infer": False,
        "roadmap_complete": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
