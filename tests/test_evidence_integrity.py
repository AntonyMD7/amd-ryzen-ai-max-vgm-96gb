from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_integrity import EvidenceIntegrityError, create_sidecar, verify_sidecar


def _raw_example() -> bytes:
    return (ROOT / "examples" / "universal-evidence-readonly-example.json").read_bytes()


def _record() -> dict:
    return json.loads(_raw_example())


def test_example_creates_schema_valid_fail_honest_sidecar() -> None:
    sidecar = create_sidecar(_raw_example())
    schema = json.loads((ROOT / "schemas" / "universal-evidence-integrity-v0.2.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(sidecar)
    assert sidecar["checks"] == {
        "schema_validation": "PASS",
        "semantic_consistency": "PASS",
        "privacy_prefilter": "PASS",
    }
    assert sidecar["normalization"]["rfc8785_jcs_conformance_claimed"] is False
    assert sidecar["normalization"]["signature_format"] is False
    assert all(value is False for value in sidecar["trust"].values())


def test_exact_sidecar_verification_succeeds_without_claiming_trust() -> None:
    raw = _raw_example()
    sidecar = create_sidecar(raw)
    result = verify_sidecar(raw, sidecar)
    assert result["status"] == "INTEGRITY_VERIFIED_NOT_TRUST_VERIFIED"
    assert result["exact_bytes_match"] is True
    assert result["normalized_content_match"] is True
    assert result["signature_verified"] is False
    assert result["producer_identity_verified"] is False
    assert result["evidence_truth_verified"] is False


def test_reformatting_changes_exact_byte_binding_even_when_semantics_match() -> None:
    raw = _raw_example()
    sidecar = create_sidecar(raw)
    reformatted = json.dumps(json.loads(raw), sort_keys=True, separators=(",", ":")).encode("utf-8")
    assert reformatted != raw
    with pytest.raises(EvidenceIntegrityError, match="exact_bytes_sha256"):
        verify_sidecar(reformatted, sidecar)


def test_semantic_tampering_is_detected() -> None:
    raw = _raw_example()
    sidecar = create_sidecar(raw)
    record = json.loads(raw)
    record["result"]["summary"] = "tampered summary"
    tampered = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with pytest.raises(EvidenceIntegrityError, match="integrity digest mismatch"):
        verify_sidecar(tampered, sidecar)


def test_duplicate_json_keys_are_rejected_before_schema_validation() -> None:
    raw = b'{"schema_version":"0.1","schema_version":"0.1"}'
    with pytest.raises(EvidenceIntegrityError, match="duplicate JSON object key"):
        create_sidecar(raw)


def test_privacy_prefilter_rejects_private_network_or_secret_material() -> None:
    for value in [
        "private endpoint 100.65.97.31",
        "lan 192.168.1.10",
        "token ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890",
        "owner@example.com",
        "/home/alice/private/output.json",
    ]:
        record = _record()
        record["result"]["summary"] = value
        raw = (json.dumps(record, indent=2) + "\n").encode("utf-8")
        with pytest.raises(EvidenceIntegrityError, match="privacy prefilter"):
            create_sidecar(raw)


def test_mutation_semantic_guards_add_to_schema_guards() -> None:
    record = _record()
    record["evidence_type"] = "mutation"
    raw = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    with pytest.raises(EvidenceIntegrityError, match="MUTATING"):
        create_sidecar(raw)

    record = _record()
    record["operation"]["intended_change"] = "should not exist in read-only evidence"
    raw = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    with pytest.raises(EvidenceIntegrityError, match="READ_ONLY"):
        create_sidecar(raw)


def test_artifact_hash_can_be_bound_and_reverified(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.txt"
    artifact.write_bytes(b"original artifact\n")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    record = _record()
    record["artifacts"] = [{"name": "artifact.txt", "sha256": digest, "media_type": "text/plain"}]
    raw = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")

    sidecar = create_sidecar(raw, artifact_root=tmp_path)
    binding = sidecar["artifact_bindings"][0]
    assert binding["verified_from_root"] is True
    assert binding["observed_sha256"] == digest
    result = verify_sidecar(raw, sidecar, artifact_root=tmp_path)
    assert result["artifact_bindings_match"] is True

    artifact.write_bytes(b"changed artifact\n")
    with pytest.raises(EvidenceIntegrityError, match="artifact digest mismatch"):
        verify_sidecar(raw, sidecar, artifact_root=tmp_path)


def test_artifact_path_escape_is_refused(tmp_path: Path) -> None:
    outside = tmp_path.parent / f"{tmp_path.name}-outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    record = _record()
    digest = hashlib.sha256(outside.read_bytes()).hexdigest()
    record["artifacts"] = [{"name": "../" + outside.name, "sha256": digest, "media_type": "text/plain"}]
    raw = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    with pytest.raises(EvidenceIntegrityError, match="unsafe artifact name"):
        create_sidecar(raw, artifact_root=tmp_path)


def test_sidecar_tampering_is_rejected_by_schema_or_digest() -> None:
    raw = _raw_example()
    sidecar = create_sidecar(raw)
    altered = deepcopy(sidecar)
    altered["trust"]["signature_verified"] = True
    with pytest.raises(EvidenceIntegrityError, match="sidecar schema"):
        verify_sidecar(raw, altered)

    altered = deepcopy(sidecar)
    altered["hashes"]["exact_bytes_sha256"] = "0" * 64
    with pytest.raises(EvidenceIntegrityError, match="integrity digest mismatch"):
        verify_sidecar(raw, altered)


def test_integrity_tool_has_no_signer_network_or_mutation_executor() -> None:
    source = (ROOT / "scripts" / "evidence_integrity.py").read_text(encoding="utf-8")
    for forbidden in ["import requests", "urllib", "subprocess", "os.system(", "shell=True", "private_key", "signing_key"]:
        assert forbidden not in source
