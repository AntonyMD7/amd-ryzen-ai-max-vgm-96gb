from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tuf_refresh_acceptance import TufRefreshAcceptanceError, git_blob_sha1, validate_bootstrap


def root_bytes(version: int = 5) -> bytes:
    return json.dumps(
        {
            "signed": {
                "_type": "root",
                "spec_version": "1.0",
                "version": version,
                "expires": "2030-01-01T00:00:00Z",
                "keys": {},
                "roles": {},
                "consistent_snapshot": True,
            },
            "signatures": [],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def expected_git_blob(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def test_git_blob_identity_matches_git_object_formula():
    data = b"DAIS F-05 TUF bootstrap fixture\n"
    assert git_blob_sha1(data) == expected_git_blob(data)


def test_bootstrap_validation_requires_exact_git_blob_and_root_version():
    data = root_bytes(5)
    result = validate_bootstrap(
        data,
        expected_git_blob_sha1=expected_git_blob(data),
        expected_root_version=5,
    )
    assert result["signed"]["_type"] == "root"
    assert result["signed"]["version"] == 5


def test_bootstrap_validation_fails_closed_on_blob_mismatch():
    data = root_bytes(5)
    with pytest.raises(TufRefreshAcceptanceError, match="Git blob mismatch"):
        validate_bootstrap(
            data,
            expected_git_blob_sha1="0" * 40,
            expected_root_version=5,
        )


def test_bootstrap_validation_fails_closed_on_root_version_mismatch():
    data = root_bytes(6)
    with pytest.raises(TufRefreshAcceptanceError, match="root version mismatch"):
        validate_bootstrap(
            data,
            expected_git_blob_sha1=expected_git_blob(data),
            expected_root_version=5,
        )


def test_bootstrap_validation_rejects_non_root_json():
    data = json.dumps({"signed": {"_type": "targets", "version": 5}}).encode()
    with pytest.raises(TufRefreshAcceptanceError, match="not TUF root metadata"):
        validate_bootstrap(
            data,
            expected_git_blob_sha1=expected_git_blob(data),
            expected_root_version=5,
        )
