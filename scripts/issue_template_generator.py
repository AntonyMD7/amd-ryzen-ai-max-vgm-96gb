#!/usr/bin/env python3
"""DAIS P-053 Issue Template Generator.

Generates a bounded GitHub Issue Form + template chooser configuration from a
small JSON product-support spec. No GitHub API or network access is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

VERSION = "0.8.0"
FORM_FILENAME = "dais-support.yml"
CONFIG_FILENAME = "config.yml"
ALLOWED_KINDS = {"bug", "feature", "support"}
SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]{1,40}$")
SENSITIVE = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s]{8,}"),
)


class InputError(ValueError):
    pass


class SafetyRefusal(RuntimeError):
    pass


def _text(value: Any, name: str, limit: int, *, multiline: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        raise InputError(f"{name} is required")
    if len(text) > limit:
        raise InputError(f"{name} exceeds {limit} characters")
    if "\x00" in text or "\r" in text:
        raise InputError(f"{name} contains unsupported control characters")
    if not multiline and ("\n" in text or "\t" in text):
        raise InputError(f"{name} must be single-line")
    if any(p.search(text) for p in SENSITIVE):
        raise SafetyRefusal(f"{name} appears to contain sensitive material")
    return text


def _yaml_scalar(text: str) -> str:
    # JSON strings are valid YAML double-quoted scalars and avoid indentation/injection ambiguity.
    return json.dumps(text, ensure_ascii=False)


def _spec(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise InputError("spec must be a JSON object")
    unexpected = sorted(set(raw) - {"name", "description", "kind", "title_prefix", "project_context", "include_environment"})
    if unexpected:
        raise InputError("unsupported spec keys: " + ", ".join(unexpected))
    kind = _text(raw.get("kind", "support"), "kind", 20).lower()
    if kind not in ALLOWED_KINDS:
        raise InputError("kind must be bug, feature, or support")
    name = _text(raw.get("name"), "name", 100)
    description = _text(raw.get("description"), "description", 200)
    prefix = _text(raw.get("title_prefix", f"[{kind.upper()}]"), "title_prefix", 40)
    context = _text(raw.get("project_context", "Public open-source project"), "project_context", 300)
    include_environment = raw.get("include_environment", kind in {"bug", "support"})
    if not isinstance(include_environment, bool):
        raise InputError("include_environment must be boolean")
    return {
        "name": name,
        "description": description,
        "kind": kind,
        "title_prefix": prefix,
        "project_context": context,
        "include_environment": include_environment,
    }


def _field(field_type: str, field_id: str, label: str, description: str, *, required: bool = True, placeholder: str = "") -> list[str]:
    if not SAFE_ID.fullmatch(field_id):
        raise AssertionError(field_id)
    lines = [
        f"  - type: {field_type}",
        f"    id: {field_id}",
        "    attributes:",
        f"      label: {_yaml_scalar(label)}",
        f"      description: {_yaml_scalar(description)}",
    ]
    if placeholder:
        lines.append(f"      placeholder: {_yaml_scalar(placeholder)}")
    if required:
        lines.extend(["    validations:", "      required: true"])
    return lines


def render_form(spec: dict[str, Any]) -> str:
    lines = [
        f"name: {_yaml_scalar(spec['name'])}",
        f"description: {_yaml_scalar(spec['description'])}",
        f"title: {_yaml_scalar(spec['title_prefix'] + ' ')}",
        "body:",
        "  - type: markdown",
        "    attributes:",
        f"      value: {_yaml_scalar('Thanks for helping improve ' + spec['project_context'] + '. Please use public/synthetic examples and never post passwords, tokens, private keys, private repository content, personal/medical data, or other sensitive information.')}",
    ]
    if spec["kind"] == "bug":
        lines += _field("textarea", "problem", "What happened?", "Describe the reproducible problem in plain language.", placeholder="What did you observe?")
        lines += _field("textarea", "steps", "Reproduction steps", "Use the smallest safe public/synthetic reproduction you can.", placeholder="1. ...\n2. ...")
        lines += _field("textarea", "expected", "Expected behavior", "What did you expect to happen?")
        lines += _field("textarea", "actual", "Actual behavior", "What happened instead? Do not paste secrets or private logs.")
    elif spec["kind"] == "feature":
        lines += _field("textarea", "problem", "Problem to solve", "Describe the user problem before proposing implementation details.")
        lines += _field("textarea", "outcome", "Desired outcome", "What useful result should a successful solution provide?")
        lines += _field("textarea", "alternatives", "Existing alternatives", "What existing tools/workarounds have you considered?", required=False)
    else:
        lines += _field("textarea", "question", "What do you need help with?", "Describe the goal and where you are blocked using public/synthetic details.")
        lines += _field("textarea", "attempted", "What have you tried?", "Include safe, reproducible steps without credentials or private content.", required=False)
    if spec["include_environment"]:
        lines += _field("input", "environment", "Environment", "OS/runtime/tool versions only. Do not include usernames, hostnames, IPs, serial numbers, credentials, or private paths.", required=False, placeholder="Example: Ubuntu 24.04; Python 3.12")
    lines.extend([
        "  - type: checkboxes",
        "    id: privacy",
        "    attributes:",
        f"      label: {_yaml_scalar('Privacy and scope confirmation')}",
        "      options:",
        f"        - label: {_yaml_scalar('I removed credentials, private repository content, personal/medical data, private network details, and other sensitive information.')}",
        "          required: true",
        f"        - label: {_yaml_scalar('I searched existing issues or documentation for the same problem where practical.')}",
        "          required: true",
    ])
    return "\n".join(lines) + "\n"


def render_config() -> str:
    return "blank_issues_enabled: false\ncontact_links: []\n"


def build(raw: Any) -> dict[str, Any]:
    spec = _spec(raw)
    form = render_form(spec)
    config = render_config()
    digest_input = (FORM_FILENAME + "\0" + form + CONFIG_FILENAME + "\0" + config).encode("utf-8")
    return {
        "schema_version": "0.1",
        "tool": "DAIS Issue Template Generator",
        "tool_version": VERSION,
        "kind": spec["kind"],
        "files": {FORM_FILENAME: form, CONFIG_FILENAME: config},
        "bundle_sha256": hashlib.sha256(digest_input).hexdigest(),
        "claims": {
            "github_schema_officially_validated": False,
            "issue_quality_guaranteed": False,
            "privacy_guaranteed": False,
            "repository_mutated": False,
        },
    }


def write_bundle(result: dict[str, Any], output: Path) -> list[Path]:
    output = output.resolve(strict=False)
    if output.exists() and output.is_symlink():
        raise SafetyRefusal("output directory may not be a symlink")
    output.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise SafetyRefusal("output directory may not be a symlink")
    written = []
    for name, content in result["files"].items():
        target = output / name
        if target.exists() and (target.is_symlink() or not target.is_file()):
            raise SafetyRefusal(f"refusing unsafe existing output: {name}")
        target.write_text(content, encoding="utf-8", newline="\n")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="Print metadata JSON; generated YAML content is omitted")
    args = parser.parse_args(argv)
    try:
        raw = json.loads(args.spec.read_text(encoding="utf-8"))
        result = build(raw)
        written: list[Path] = []
        if args.output:
            written = write_bundle(result, args.output)
        meta = {k: v for k, v in result.items() if k != "files"}
        meta["written_files"] = [p.name for p in written]
        if args.json or not args.output:
            print(json.dumps(meta, indent=2, sort_keys=True))
        else:
            print(f"P053_GENERATED={len(written)}")
            print(f"P053_BUNDLE_SHA256={result['bundle_sha256']}")
        return 0
    except (OSError, json.JSONDecodeError, InputError, SafetyRefusal) as exc:
        print(f"P053_REFUSAL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
