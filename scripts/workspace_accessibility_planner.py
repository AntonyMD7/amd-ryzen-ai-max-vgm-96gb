#!/usr/bin/env python3
"""Offline least-privilege plans for productivity/API integrations.

This reference module never contacts Google, a browser, mail, calendar, Drive,
Docs, Sheets, Forms or any third-party API. It classifies intended operations so
future adapters can request the smallest appropriate scope and explicit approval.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class WorkspacePlanError(ValueError):
    pass


SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE.fullmatch(value):
        raise WorkspacePlanError(f"{name} must be a bounded identifier")
    return value


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise WorkspacePlanError(f"{name} must be boolean")
    return value


def _base(roadmap_id: str, surface: str) -> dict[str, Any]:
    return {
        "schema_version": "0.1",
        "roadmap_id": roadmap_id,
        "surface": surface,
        "execution": {
            "api_called": False,
            "content_read": False,
            "content_written": False,
            "message_sent": False,
            "calendar_event_changed": False,
            "browser_permission_granted": False,
        },
    }


def drive_organization(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-077", "drive")
    action = data.get("action")
    if action not in {"inventory", "propose_folder", "propose_move", "propose_rename"}:
        raise WorkspacePlanError("unsupported Drive planning action")
    out.update({
        "action": action,
        "required_access_class": "METADATA_READ" if action == "inventory" else "METADATA_READ_PLUS_EXPLICIT_WRITE_APPROVAL",
        "requirements": ["use stable file IDs", "do not infer ownership from filenames", "preserve shared-drive semantics", "dry-run before mutation"],
    })
    return out


def docs_knowledge(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-078", "docs")
    source_count = data.get("authorized_source_count")
    if isinstance(source_count, bool) or not isinstance(source_count, int) or source_count < 0:
        raise WorkspacePlanError("authorized_source_count must be non-negative integer")
    out.update({
        "authorized_source_count": source_count,
        "required_access_class": "EXPLICIT_DOCUMENT_READ_ALLOWLIST",
        "requirements": ["document allowlist", "provenance per chunk", "no write-back by default", "insufficient-evidence refusal"],
    })
    return out


def sheets_workflow(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-079", "sheets")
    operation = data.get("operation")
    if operation not in {"read_range", "append_proposal", "update_proposal"}:
        raise WorkspacePlanError("unsupported Sheets planning operation")
    out.update({
        "operation": operation,
        "required_access_class": "READ" if operation == "read_range" else "READ_PLUS_EXPLICIT_WRITE_APPROVAL",
        "requirements": ["explicit spreadsheet ID", "explicit A1/range contract", "schema validation", "idempotency key for writes"],
    })
    return out


def gmail_workflow(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-080", "gmail")
    operation = data.get("operation")
    if operation not in {"search", "read", "draft_proposal", "send_proposal", "label_proposal"}:
        raise WorkspacePlanError("unsupported Gmail planning operation")
    mutation = operation in {"draft_proposal", "send_proposal", "label_proposal"}
    out.update({
        "operation": operation,
        "required_access_class": "READ" if not mutation else "EXPLICIT_MUTATION_APPROVAL",
        "requirements": ["recipient resolution before send", "show exact message before send", "no automatic send from generated text", "retain message/thread provenance"],
    })
    return out


def calendar_coordination(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-081", "calendar")
    operation = data.get("operation")
    if operation not in {"availability", "list_events", "create_proposal", "update_proposal", "delete_proposal"}:
        raise WorkspacePlanError("unsupported Calendar planning operation")
    mutation = operation.endswith("proposal")
    out.update({
        "operation": operation,
        "required_access_class": "READ_OR_FREEBUSY" if not mutation else "READ_PLUS_EXPLICIT_EVENT_MUTATION_APPROVAL",
        "requirements": ["resolve timezone", "resolve attendees", "show exact local start/end", "check conflicts before mutation"],
    })
    return out


def plain_language_layer(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-082", "workspace_plain_language")
    complexity = data.get("source_complexity")
    if complexity not in {"low", "medium", "high"}:
        raise WorkspacePlanError("source_complexity must be low, medium, or high")
    out.update({
        "source_complexity": complexity,
        "requirements": ["preserve dates/numbers/names", "do not omit material risk", "offer original wording", "mark uncertainty", "support beginner and engineer views"],
        "semantics": {"transformation_performed": False, "meaning_preserved_verified": False},
    })
    return out


def forms_accessibility(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-083", "forms")
    checks = {}
    for key in ("plain_labels", "one_idea_per_question", "required_fields_explained", "error_recovery_explained", "keyboard_path_considered", "language_declared"):
        checks[key] = _bool(data.get(key), key)
    missing = [key for key, value in checks.items() if not value]
    out.update({"checks": checks, "missing": missing, "status": "REVIEW" if missing else "CHECKLIST_PASSES_REVIEW_STILL_REQUIRED"})
    return out


def browser_extension(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-084", "browser_extension")
    permissions = data.get("permissions")
    if not isinstance(permissions, list) or len(permissions) > 50:
        raise WorkspacePlanError("permissions must be a bounded list")
    normalized = [_id(value, "permission") for value in permissions]
    broad = [p for p in normalized if p in {"<all_urls>", "tabs", "history", "webRequest", "cookies", "clipboardRead"}]
    out.update({
        "permissions": normalized,
        "broad_or_sensitive_permissions": broad,
        "status": "SECURITY_REVIEW_REQUIRED" if broad else "LEAST_PRIVILEGE_REVIEW",
        "requirements": ["justify every permission", "avoid remote code", "document data flow", "provide uninstall/recovery path"],
    })
    return out


def addon_starter(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-085", "workspace_addon")
    hosts = data.get("hosts")
    if not isinstance(hosts, list) or not hosts or len(hosts) > 10:
        raise WorkspacePlanError("hosts must be a bounded non-empty list")
    allowed = {"gmail", "calendar", "drive", "docs", "sheets", "slides"}
    if any(host not in allowed for host in hosts):
        raise WorkspacePlanError("unsupported host")
    out.update({
        "hosts": sorted(set(hosts)),
        "requirements": ["declare OAuth scopes", "use card/iframe UI per current platform rules", "privacy policy", "test per host", "separate read from mutation actions"],
        "deployment": {"addon_created": False, "cloud_project_changed": False, "marketplace_published": False},
    })
    return out


def api_democratization(data: dict[str, Any]) -> dict[str, Any]:
    out = _base("P-086", "api_wrapper")
    api_id = _id(data.get("api_id"), "api_id")
    auth = data.get("auth")
    if auth not in {"none", "api_key", "oauth2", "service_account", "other_review"}:
        raise WorkspacePlanError("unsupported auth class")
    write_capable = _bool(data.get("write_capable"), "write_capable")
    out.update({
        "api_id": api_id,
        "auth_class": auth,
        "write_capable": write_capable,
        "required_control": "EXPLICIT_WRITE_APPROVAL_AND_IDEMPOTENCY" if write_capable else "READ_ONLY_RATE_LIMITED_ADAPTER",
        "requirements": ["official API schema", "least privilege", "bounded retries", "pagination", "rate-limit handling", "redacted logs", "version/provenance"],
    })
    return out


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    functions = {
        "drive": drive_organization,
        "docs": docs_knowledge,
        "sheets": sheets_workflow,
        "gmail": gmail_workflow,
        "calendar": calendar_coordination,
        "plain_language": plain_language_layer,
        "forms": forms_accessibility,
        "browser_extension": browser_extension,
        "addon": addon_starter,
        "api_wrapper": api_democratization,
    }
    fn = functions.get(mode)
    if fn is None:
        raise WorkspacePlanError("unsupported mode")
    return fn(data)


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
