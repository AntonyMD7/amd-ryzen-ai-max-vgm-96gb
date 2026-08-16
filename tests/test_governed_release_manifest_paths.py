import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from governed_release_manifest import ManifestError, safe_relpath


def test_dot_prefixed_repository_paths_are_valid():
    assert safe_relpath(".github/actions/governed-release/action.yml", field="path") == ".github/actions/governed-release/action.yml"
    assert safe_relpath(".changeset/example.md", field="path") == ".changeset/example.md"


@pytest.mark.parametrize(
    "value",
    [
        "./README.md",
        "../secret.md",
        "docs/../secret.md",
        "docs/./README.md",
        "/absolute/path.md",
        "docs//README.md",
    ],
)
def test_actual_traversal_or_current_directory_segments_are_refused(value: str):
    with pytest.raises(ManifestError):
        safe_relpath(value, field="path")
