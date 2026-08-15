#!/usr/bin/env python3
"""Evidence-first runbook generator v0.1.

Validates a machine-readable automation plan then renders reviewable Markdown.
It never executes plan commands or mutations. A runbook is a plan, not evidence that
any step happened.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "automation-plan-v0.1.schema.json"


class PlanError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_plan(plan: dict[str, Any], schema: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(schema).validate(plan)
    phases = [step["phase"] for step in plan["steps"]]
    if "DISCOVER" not in phases:
        raise PlanError("plan must include a DISCOVER phase")
    if "ATTEST" not in phases:
        raise PlanError("plan must include an ATTEST phase")

    mutating_steps = [step for step in plan["steps"] if step["classification"] == "MUTATING"]
    if plan["mode"] == "READ_ONLY" and mutating_steps:
        raise PlanError("READ_ONLY plan contains a MUTATING step")
    if plan["mode"] == "MUTATING" and not mutating_steps:
        raise PlanError("MUTATING plan has no explicitly MUTATING step")

    phase_index = {phase: index for index, phase in enumerate(phases)}
    if plan["mode"] == "MUTATING":
        for required in ("PREFLIGHT", "APPROVE", "MUTATE", "ATTEST"):
            if required not in phases:
                raise PlanError(f"mutating plan requires {required} phase")
        if not (phase_index["PREFLIGHT"] < phase_index["APPROVE"] < phase_index["MUTATE"] < phase_index["ATTEST"]):
            raise PlanError("mutating lifecycle phases are out of order")


def _safe_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# {plan['title']}",
        "",
        f"**Plan ID:** `{plan['plan_id']}`  ",
        f"**Mode:** `{plan['mode']}`  ",
        f"**Environment:** `{plan['scope']['environment']}`  ",
        f"**Subject:** `{plan['scope']['subject']}`  ",
        f"**Roadmap:** {', '.join(f'`{item}`' for item in plan['roadmap_ids'])}",
        "",
        "> This document is a validated plan. It does **not** prove any command was executed or any change succeeded.",
        "",
    ]

    if plan["mode"] == "MUTATING":
        lines.extend([
            "## Mutation gate",
            "",
            f"- Approval recorded: **{'YES' if plan['approval']['present'] else 'NO'}**",
            f"- Authorization reference: `{plan['approval']['authorization_ref']}`",
            f"- Recovery established: **{'YES' if plan['rollback']['established'] else 'NO'}**",
            f"- Rollback procedure: `{plan['rollback']['procedure_ref']}`",
            "",
        ])

    exclusions = plan["scope"].get("explicit_exclusions", [])
    if exclusions:
        lines.extend(["## Explicit exclusions", ""])
        lines.extend(f"- {item}" for item in exclusions)
        lines.append("")

    lines.extend([
        "## Steps",
        "",
        "| # | Phase | Classification | Description | Command/reference | Expected evidence |",
        "|---:|---|---|---|---|---|",
    ])
    for index, step in enumerate(plan["steps"], start=1):
        command = step["command_ref"] or "—"
        expected = "; ".join(step["expected_evidence"]) or "—"
        lines.append(
            f"| {index} | {_safe_cell(step['phase'])} | {_safe_cell(step['classification'])} | "
            f"{_safe_cell(step['description'])} | `{_safe_cell(command)}` | {_safe_cell(expected)} |"
        )

    lines.extend(["", "## Acceptance", ""])
    for item in plan["acceptance"]:
        marker = "REQUIRED" if item["required"] else "OPTIONAL"
        lines.append(f"- **{marker} — {item['id']}**: {item['description']}")

    lines.extend([
        "",
        "## Evidence contract",
        "",
        f"- Schema: `{plan['evidence']['schema_ref']}`",
        f"- Retention: `{plan['evidence']['retention']}`",
        "- Secret values allowed in evidence: **NO**",
        "",
        "## Known limitations",
        "",
    ])
    lines.extend(f"- {item}" for item in plan["limitations"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an automation plan and render a non-executing Markdown runbook")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    plan = load_json(args.plan)
    schema = load_json(args.schema)
    validate_plan(plan, schema)
    rendered = render_markdown(plan)
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
