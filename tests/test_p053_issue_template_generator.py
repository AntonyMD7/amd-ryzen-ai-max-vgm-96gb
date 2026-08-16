from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "issue_template_generator.py"
spec = importlib.util.spec_from_file_location("p053_generator", MODULE_PATH)
assert spec and spec.loader
gen = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = gen
spec.loader.exec_module(gen)


def base_spec(kind="bug"):
    return {
        "name": "Bug report",
        "description": "Report a reproducible public bug",
        "kind": kind,
        "title_prefix": "[BUG]",
        "project_context": "the example public project",
        "include_environment": True,
    }


def test_deterministic_bundle_and_required_privacy_controls():
    first = gen.build(base_spec())
    second = gen.build(base_spec())
    assert first["bundle_sha256"] == second["bundle_sha256"]
    form = first["files"][gen.FORM_FILENAME]
    assert 'type: checkboxes' in form
    assert 'Privacy and scope confirmation' in form
    assert 'required: true' in form
    assert first["files"][gen.CONFIG_FILENAME] == "blank_issues_enabled: false\ncontact_links: []\n"
    assert all(v is False for v in first["claims"].values())


@pytest.mark.parametrize("kind", ["bug", "feature", "support"])
def test_supported_presets_generate_distinct_actionable_fields(kind):
    data = base_spec(kind)
    data["title_prefix"] = f"[{kind.upper()}]"
    out = gen.build(data)["files"][gen.FORM_FILENAME]
    assert f'name: "{data["name"]}"' in out
    assert 'id: privacy' in out
    if kind == "bug":
        assert 'id: steps' in out and 'id: actual' in out
    elif kind == "feature":
        assert 'id: outcome' in out and 'id: alternatives' in out
    else:
        assert 'id: question' in out and 'id: attempted' in out


@pytest.mark.parametrize(
    "field,value",
    [
        ("description", "token=github_pat_12345678901234567890"),
        ("project_context", "password: CorrectHorseBatteryStaple"),
        ("name", "-----BEGIN PRIVATE KEY-----"),
    ],
)
def test_secret_like_spec_values_fail_closed(field, value):
    data = base_spec()
    data[field] = value
    with pytest.raises(gen.SafetyRefusal):
        gen.build(data)


def test_yaml_metacharacters_are_quoted_not_injected():
    data = base_spec()
    data["name"] = "Bug: [safe] # not-a-comment"
    data["description"] = "Line-like value: true"
    form = gen.build(data)["files"][gen.FORM_FILENAME]
    assert 'name: "Bug: [safe] # not-a-comment"' in form
    assert 'description: "Line-like value: true"' in form


def test_unknown_keys_and_bad_kind_fail_closed():
    data = base_spec()
    data["labels"] = ["security"]
    with pytest.raises(gen.InputError):
        gen.build(data)
    data = base_spec()
    data["kind"] = "arbitrary"
    with pytest.raises(gen.InputError):
        gen.build(data)


def test_output_write_is_bounded_to_two_known_files(tmp_path):
    result = gen.build(base_spec())
    output = tmp_path / "generated"
    written = gen.write_bundle(result, output)
    assert {p.name for p in written} == {gen.FORM_FILENAME, gen.CONFIG_FILENAME}
    assert sorted(p.name for p in output.iterdir()) == [gen.CONFIG_FILENAME, gen.FORM_FILENAME]
    assert result["claims"]["repository_mutated"] is False


def test_unsafe_existing_output_symlink_fails_closed(tmp_path):
    result = gen.build(base_spec())
    output = tmp_path / "generated"
    output.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("unchanged", encoding="utf-8")
    (output / gen.FORM_FILENAME).symlink_to(outside)
    with pytest.raises(gen.SafetyRefusal):
        gen.write_bundle(result, output)
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_environment_field_can_be_deliberately_omitted():
    data = base_spec()
    data["include_environment"] = False
    form = gen.build(data)["files"][gen.FORM_FILENAME]
    assert 'id: environment' not in form
