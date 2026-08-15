#!/usr/bin/env python3
"""SafeFix v0.1 reference contract.

This module is deliberately non-executing. It models and validates a safe
engineering lifecycle but never runs a supplied command, edits a file, changes a
service, or performs a reboot. Projects can wrap this contract around their own
explicitly governed execution adapters.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Stage(str, Enum):
    DISCOVER = "DISCOVER"
    VERIFY = "VERIFY"
    PREFLIGHT = "PREFLIGHT"
    APPROVE = "APPROVE"
    MUTATE = "MUTATE"
    RESTART = "RESTART"
    ATTEST = "ATTEST"
    PUBLISH_EVIDENCE = "PUBLISH_EVIDENCE"


ALLOWED_TRANSITIONS = {
    Stage.DISCOVER: {Stage.VERIFY},
    Stage.VERIFY: {Stage.PREFLIGHT},
    Stage.PREFLIGHT: {Stage.APPROVE},
    Stage.APPROVE: {Stage.MUTATE},
    Stage.MUTATE: {Stage.RESTART, Stage.ATTEST},
    Stage.RESTART: {Stage.ATTEST},
    Stage.ATTEST: {Stage.PUBLISH_EVIDENCE},
    Stage.PUBLISH_EVIDENCE: set(),
}


class ContractError(ValueError):
    """Raised when a proposed SafeFix transition violates the contract."""


@dataclass(frozen=True)
class GateContext:
    recovery_established: bool = False
    approval_required: bool = False
    approval_present: bool = False
    mutation_performed: bool = False
    post_change_attested: bool = False
    evidence_ready: bool = False


def validate_transition(current: Stage, target: Stage, context: GateContext) -> None:
    """Validate one lifecycle transition without performing it."""
    if target not in ALLOWED_TRANSITIONS[current]:
        raise ContractError(f"transition not allowed: {current.value} -> {target.value}")

    if target is Stage.MUTATE:
        if not context.recovery_established:
            raise ContractError("mutation blocked: recovery is not established")
        if context.approval_required and not context.approval_present:
            raise ContractError("mutation blocked: required approval is absent")

    if target is Stage.RESTART and not context.mutation_performed:
        raise ContractError("restart blocked: no governed mutation has been recorded")

    if target is Stage.PUBLISH_EVIDENCE:
        if not context.post_change_attested:
            raise ContractError("publication blocked: post-change attestation is absent")
        if not context.evidence_ready:
            raise ContractError("publication blocked: evidence record is not ready")


def transition_path(restart_required: bool) -> list[Stage]:
    """Return the canonical path for documentation/UI use."""
    common = [Stage.DISCOVER, Stage.VERIFY, Stage.PREFLIGHT, Stage.APPROVE, Stage.MUTATE]
    if restart_required:
        common.append(Stage.RESTART)
    return common + [Stage.ATTEST, Stage.PUBLISH_EVIDENCE]


if __name__ == "__main__":
    print(" -> ".join(stage.value for stage in transition_path(restart_required=True)))
