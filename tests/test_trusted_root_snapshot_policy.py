import copy
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from trusted_root_snapshot_policy import SnapshotPolicyError, evaluate, validate_record

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "trusted-root-snapshot-synthetic-v0.1.json"
SCHEMA = ROOT / "schemas" / "trusted-root-snapshot-v0.1.schema.json"


def record():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def test_example_matches_json_schema_and_strict_contract():
    data = record()
    jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8"))).validate(data)
    validate_record(data)


def test_within_local_refresh_window_is_narrow_pass():
    result = evaluate(record(), as_of=utc("2026-08-15T12:00:00Z"))
    assert result["policy_status"] == "ARCHIVE_POLICY_SATISFIED"
    assert result["local_refresh_status"] == "WITHIN_LOCAL_REFRESH_WINDOW"
    assert result["previous_snapshot_link_status"] == "NOT_DECLARED"
    assert result["trusted_root_current_proven"] is False
    assert result["future_revocation_awareness_proven"] is False
    assert result["cryptography_performed"] is False
    assert result["network_contact_performed"] is False
    assert result["roadmap_completion_proven"] is False


def test_overdue_local_refresh_window_fails_closed():
    result = evaluate(record(), as_of=utc("2026-08-22T08:00:01Z"))
    assert result["policy_status"] == "ARCHIVE_POLICY_REJECTED"
    assert result["local_refresh_status"] == "LOCAL_REFRESH_OVERDUE"


def test_as_of_before_acquisition_is_rejected():
    with pytest.raises(SnapshotPolicyError, match="predates snapshot acquisition"):
        evaluate(record(), as_of=utc("2026-08-15T07:59:59Z"))


def test_refresh_due_cannot_exceed_declared_max_age():
    data = record()
    data["refresh_policy"]["refresh_due_at"] = "2026-08-22T08:00:01Z"
    with pytest.raises(SnapshotPolicyError, match="exceeds the declared max_age_hours"):
        validate_record(data)


def test_truth_boundary_claims_must_remain_false():
    data = record()
    data["claims"]["trusted_root_current_proven"] = True
    with pytest.raises(SnapshotPolicyError, match="trusted_root_current_proven"):
        validate_record(data)


def test_source_uri_rejects_embedded_credentials():
    data = record()
    data["source"]["source_uri"] = "https://user:secret@example.invalid/root"
    with pytest.raises(SnapshotPolicyError, match="without embedded credentials"):
        validate_record(data)


def test_previous_record_hash_link_can_be_verified_exactly():
    previous = b'{"snapshot":"previous"}\n'
    data = record()
    data["refresh_policy"]["previous_snapshot_record_sha256"] = hashlib.sha256(previous).hexdigest()
    result = evaluate(data, as_of=utc("2026-08-15T12:00:00Z"), previous_record_bytes=previous)
    assert result["previous_snapshot_link_status"] == "VERIFIED"
    assert result["policy_status"] == "ARCHIVE_POLICY_SATISFIED"


def test_previous_record_hash_mismatch_rejects_policy():
    previous = b'{"snapshot":"expected"}\n'
    data = record()
    data["refresh_policy"]["previous_snapshot_record_sha256"] = hashlib.sha256(previous).hexdigest()
    result = evaluate(data, as_of=utc("2026-08-15T12:00:00Z"), previous_record_bytes=b"tampered\n")
    assert result["previous_snapshot_link_status"] == "MISMATCH"
    assert result["policy_status"] == "ARCHIVE_POLICY_REJECTED"


def test_supplied_previous_record_requires_declared_hash():
    with pytest.raises(SnapshotPolicyError, match="no previous hash is declared"):
        evaluate(record(), as_of=utc("2026-08-15T12:00:00Z"), previous_record_bytes=b"unexpected")
