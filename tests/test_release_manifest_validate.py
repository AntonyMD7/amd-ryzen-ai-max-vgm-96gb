from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "scripts" / "release_manifest_validate.py"
spec = importlib.util.spec_from_file_location("release_manifest_validate", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

MANIFEST = ROOT / "release" / "p025-v0.1.0.json"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_reviewed_manifest_is_valid():
    result = mod.validate_manifest(load_manifest(), ROOT)
    assert result["decision"] == "MANIFEST_VALID"
    assert result["roadmap_id"] == "P-025"
    assert result["tag"] == "v0.1.0"
    assert result["source_commit"] == "704f7bab429b1f67896b32bf90b99d3d0d9cd39c"
    assert result["release_publication_performed"] is False
    assert result["roadmap_completion_promoted"] is False


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("tag", "v0.1.1"),
        ("tag", "latest"),
        ("source_commit", "deadbeef"),
        ("source_commit", "a" * 40),
        ("roadmap_id", "P-051"),
        ("release_id", "other"),
        ("completion_record", "../secret.json"),
        ("notes_file", "docs/other.md"),
        ("publication_mode", "DIRECT_PUBLISH"),
        ("post_publish_exact_tag_verification_required", False),
        ("roadmap_completion_on_publish", True),
    ],
)
def test_manifest_drift_fails_closed(field, value):
    data = copy.deepcopy(load_manifest())
    data[field] = value
    with pytest.raises(mod.ManifestError):
        mod.validate_manifest(data, ROOT)


def test_extra_or_missing_fields_fail_closed():
    data = load_manifest()
    data["unexpected"] = True
    with pytest.raises(mod.ManifestError):
        mod.validate_manifest(data, ROOT)
    data = load_manifest()
    del data["title"]
    with pytest.raises(mod.ManifestError):
        mod.validate_manifest(data, ROOT)


def test_validator_has_no_network_or_release_executor():
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "gh release",
        "git push",
        "requests.",
        "urllib.request",
        "subprocess",
        "socket",
    )
    for token in forbidden:
        assert token not in source
