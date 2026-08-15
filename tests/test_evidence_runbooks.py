from __future__ import annotations

import copy
import json
from pathlib import Path
import sys

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from runbook_generator import PlanError, render_markdown, validate_plan


def load_example():
    return json.loads((ROOT / "examples/automation-plan-readonly-v0.1.json").read_text())


def load_schema():
    return json.loads((ROOT / "schemas/automation-plan-v0.1.schema.json").read_text())


def test_readonly_example_validates_and_renders() -> None:
    plan = load_example()
    validate_plan(plan, load_schema())
    text = render_markdown(plan)
    assert "validated plan" in text
    assert "does **not** prove" in text
    assert "Secret values allowed in evidence: **NO**" in text


def test_readonly_plan_rejects_mutating_step() -> None:
    plan = load_example()
    plan["steps"][1]["classification"] = "MUTATING"
    with pytest.raises(PlanError, match="READ_ONLY plan contains"):
        validate_plan(plan, load_schema())


def make_mutating_plan():
    plan = copy.deepcopy(load_example())
    plan["plan_id"] = "mutating-example-001"
    plan["mode"] = "MUTATING"
    plan["steps"] = [
        {
            "id": "discover",
            "phase": "DISCOVER",
            "description": "Observe current state.",
            "classification": "READ_ONLY",
            "command_ref": "read-only-probe",
            "expected_evidence": ["pre-state"],
            "timeout_seconds": 30,
            "idempotency": "IDEMPOTENT"
        },
        {
            "id": "preflight",
            "phase": "PREFLIGHT",
            "description": "Verify recovery and scope.",
            "classification": "READ_ONLY",
            "command_ref": "preflight-check",
            "expected_evidence": ["recovery-ready"],
            "timeout_seconds": 30,
            "idempotency": "IDEMPOTENT"
        },
        {
            "id": "approve",
            "phase": "APPROVE",
            "description": "Record explicit approval.",
            "classification": "HUMAN_GATE",
            "command_ref": None,
            "expected_evidence": ["authorization reference"],
            "timeout_seconds": None,
            "idempotency": "NOT_IDEMPOTENT"
        },
        {
            "id": "mutate",
            "phase": "MUTATE",
            "description": "Perform one bounded change.",
            "classification": "MUTATING",
            "command_ref": "bounded-change-adapter",
            "expected_evidence": ["change result"],
            "timeout_seconds": 30,
            "idempotency": "UNKNOWN"
        },
        {
            "id": "attest",
            "phase": "ATTEST",
            "description": "Re-read state independently.",
            "classification": "READ_ONLY",
            "command_ref": "read-only-probe",
            "expected_evidence": ["post-state"],
            "timeout_seconds": 30,
            "idempotency": "IDEMPOTENT"
        }
    ]
    plan["rollback"] = {
        "required": True,
        "established": True,
        "procedure_ref": "docs/RECOVERY.md",
        "prechange_backup_ref": "sanitized-backup-pointer"
    }
    plan["approval"] = {
        "required": True,
        "present": True,
        "authorization_ref": "OWNER-APPROVAL-example"
    }
    return plan


def test_mutating_plan_requires_recovery_in_schema() -> None:
    plan = make_mutating_plan()
    plan["rollback"]["established"] = False
    errors = list(jsonschema.Draft202012Validator(load_schema()).iter_errors(plan))
    assert errors


def test_mutating_plan_requires_approval_in_schema() -> None:
    plan = make_mutating_plan()
    plan["approval"]["present"] = False
    errors = list(jsonschema.Draft202012Validator(load_schema()).iter_errors(plan))
    assert errors


def test_mutating_plan_requires_lifecycle_order() -> None:
    plan = make_mutating_plan()
    plan["steps"][1], plan["steps"][3] = plan["steps"][3], plan["steps"][1]
    with pytest.raises(PlanError, match="out of order"):
        validate_plan(plan, load_schema())


def test_mutating_plan_is_still_only_rendered_not_executed() -> None:
    plan = make_mutating_plan()
    validate_plan(plan, load_schema())
    text = render_markdown(plan)
    assert "Approval recorded: **YES**" in text
    assert "Recovery established: **YES**" in text
    assert "does **not** prove any command was executed" in text
