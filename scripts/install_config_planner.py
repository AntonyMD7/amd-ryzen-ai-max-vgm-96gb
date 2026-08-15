#!/usr/bin/env python3
"""Create reviewable installation/configuration plans without executing changes."""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class PlanError(ValueError):
    pass


SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9._+-]{0,79}$")
SAFE_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,79}$")
HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")


def _safe_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise PlanError(f"{field} must be a bounded machine identifier")
    return value


def installation_plan(data: dict[str, Any]) -> dict[str, Any]:
    package = _safe_id(data.get("package"), "package")
    platform = _safe_id(data.get("platform"), "platform")
    authority = _safe_id(data.get("source_authority"), "source_authority")
    version = data.get("version")
    digest = data.get("sha256")
    recovery_ready = data.get("recovery_ready")
    approval_granted = data.get("approval_granted")

    if not isinstance(version, str) or not SAFE_VERSION.fullmatch(version):
        raise PlanError("version must be explicit and bounded")
    if not isinstance(digest, str) or not HEX64.fullmatch(digest):
        raise PlanError("sha256 must be an explicit 64-character hexadecimal digest")
    if not isinstance(recovery_ready, bool) or not isinstance(approval_granted, bool):
        raise PlanError("recovery_ready and approval_granted must be booleans")

    ready = recovery_ready and approval_granted
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-019",
        "mode": "PLAN_ONLY",
        "package": package,
        "platform": platform,
        "source_authority": authority,
        "version": version,
        "sha256": digest.lower(),
        "disposition": "REVIEWABLE_MUTATION_PLAN" if ready else "BLOCKED_PRECONDITIONS",
        "gates": {
            "version_pinned": True,
            "artifact_digest_supplied": True,
            "recovery_ready": recovery_ready,
            "approval_granted": approval_granted,
            "all_required_gates_satisfied": ready,
        },
        "execution": {
            "command_emitted": False,
            "package_installed": False,
            "network_contacted": False,
            "service_changed": False,
            "configuration_changed": False,
        },
        "next_gate": "Use the current platform/vendor installation authority, independently verify artifact identity, then execute only through a separately governed SafeFix mutation adapter.",
    }


def configuration_audit(data: dict[str, Any]) -> dict[str, Any]:
    facts = data.get("facts")
    rules = data.get("rules")
    if not isinstance(facts, dict) or not all(isinstance(k, str) and isinstance(v, bool) for k, v in facts.items()):
        raise PlanError("facts must be an object of boolean values")
    if not isinstance(rules, list) or len(rules) > 200:
        raise PlanError("rules must be a bounded list")

    findings = []
    for rule in rules:
        if not isinstance(rule, dict):
            raise PlanError("each rule must be an object")
        rule_id = _safe_id(rule.get("id"), "rule.id")
        fact = _safe_id(rule.get("fact"), "rule.fact")
        expected = rule.get("expected")
        severity = rule.get("severity")
        if not isinstance(expected, bool):
            raise PlanError("rule.expected must be boolean")
        if severity not in {"info", "review", "high"}:
            raise PlanError("rule.severity must be info, review, or high")
        if fact not in facts:
            findings.append({"rule_id": rule_id, "fact": fact, "state": "UNKNOWN", "severity": severity})
        elif facts[fact] == expected:
            findings.append({"rule_id": rule_id, "fact": fact, "state": "PASS", "severity": severity})
        else:
            findings.append({"rule_id": rule_id, "fact": fact, "state": "REVIEW", "severity": severity})

    return {
        "schema_version": "0.1",
        "roadmap_id": "P-020",
        "mode": "READ_ONLY_POLICY_EVALUATION",
        "summary": {
            "pass": sum(item["state"] == "PASS" for item in findings),
            "review": sum(item["state"] == "REVIEW" for item in findings),
            "unknown": sum(item["state"] == "UNKNOWN" for item in findings),
        },
        "findings": findings,
        "privacy": {
            "only_boolean_fact_values_accepted": True,
            "raw_configuration_returned": False,
            "secret_values_accepted": False,
        },
        "semantics": {
            "policy_is_vendor_authority": False,
            "pass_is_security_guarantee": False,
            "audit_mutates_configuration": False,
        },
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    if mode == "installation":
        return installation_plan(data)
    if mode == "configuration_audit":
        return configuration_audit(data)
    raise PlanError("mode must be installation or configuration_audit")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    args = parser.parse_args()
    with open(args.request, encoding="utf-8") as handle:
        request = json.load(handle)
    print(json.dumps(evaluate(request), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
