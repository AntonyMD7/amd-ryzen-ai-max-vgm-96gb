#!/usr/bin/env python3
"""DAIS Beginner-Safe PR Creator.

P-052 reference implementation. Planning is network-free. Creation is deliberately
limited to same-repository *draft* pull requests and requires an explicit plan-hash
lease plus confirmation. The tool never pushes branches, requests reviewers,
marks a PR ready, merges, closes, or edits an existing non-draft PR.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

VERSION = "0.7.0"
API_ROOT = "https://api.github.com"
SCHEMA_VERSION = "0.2"
CONFIRMATION = "CREATE_DRAFT_PR"
ALLOWED_CREATE_EVENTS = {"push", "workflow_dispatch"}
REQUIRED_CHECKS = (
    "tests_run",
    "ci_expected",
    "secrets_reviewed",
    "scope_reviewed",
    "rollback_considered",
)
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
REF_RE = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
SENSITIVE_PATTERNS = (
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret|token)\s*[:=]\s*[^\s]{8,}"),
)


class InputError(ValueError):
    """Invalid caller input."""


class SafetyRefusal(RuntimeError):
    """Requested action crosses the product safety boundary."""


class ApiFailure(RuntimeError):
    """GitHub API failed without exposing response bodies or credentials."""


def _clean_text(value: Any, name: str, *, max_len: int, multiline: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        raise InputError(f"{name} is required")
    if len(text) > max_len:
        raise InputError(f"{name} exceeds {max_len} characters")
    if "\x00" in text or "\r" in text:
        raise InputError(f"{name} contains unsupported control characters")
    if not multiline and ("\n" in text or "\t" in text):
        raise InputError(f"{name} must be single-line")
    for char in text:
        if ord(char) < 32 and char not in {"\n", "\t"}:
            raise InputError(f"{name} contains unsupported control characters")
    if any(pattern.search(text) for pattern in SENSITIVE_PATTERNS):
        raise SafetyRefusal(f"{name} appears to contain sensitive material; remove it before creating public PR text")
    return text


def _validate_repo(value: Any) -> str:
    repo = _clean_text(value, "repository", max_len=200)
    if not REPO_RE.fullmatch(repo):
        raise InputError("repository must be owner/name using the bounded public GitHub name grammar")
    return repo


def _validate_ref(value: Any, name: str) -> str:
    ref = _clean_text(value, name, max_len=120)
    if not REF_RE.fullmatch(ref):
        raise InputError(f"{name} contains unsupported ref characters")
    if ref.startswith("/") or ref.endswith("/") or "//" in ref or ".." in ref or ":" in ref or "@{" in ref:
        raise InputError(f"{name} is outside the bounded branch-name grammar")
    if ref.endswith(".lock") or ref == "@":
        raise InputError(f"{name} is outside the bounded branch-name grammar")
    return ref


def _normalize_checks(checks: Any) -> dict[str, bool]:
    if not isinstance(checks, dict):
        raise InputError("checks must be an object")
    unexpected = sorted(set(checks) - set(REQUIRED_CHECKS))
    if unexpected:
        raise InputError("checks contains unsupported keys: " + ", ".join(unexpected))
    return {key: checks.get(key) is True for key in REQUIRED_CHECKS}


def _plan_core(data: dict[str, Any]) -> dict[str, Any]:
    repository = _validate_repo(data.get("repository"))
    title = _clean_text(data.get("title"), "title", max_len=180)
    summary = _clean_text(data.get("summary"), "summary", max_len=4000, multiline=True)
    base = _validate_ref(data.get("base"), "base")
    head = _validate_ref(data.get("head"), "head")
    if base == head:
        raise InputError("head must differ from base")
    checks = _normalize_checks(data.get("checks", {}))
    failed = [key for key in REQUIRED_CHECKS if not checks[key]]
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": "DAIS Beginner-Safe PR Creator",
        "tool_version": VERSION,
        "repository": repository,
        "title": title,
        "summary": summary,
        "base": base,
        "head": head,
        "checks": checks,
        "failed_checks": failed,
        "decision": "READY_FOR_DRAFT_CREATE" if not failed else "BLOCKED_UNTIL_SAFETY_CHECKS_COMPLETE",
        "draft_only": True,
    }


def _canonical_bytes(core: dict[str, Any]) -> bytes:
    return json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _pr_body(core: dict[str, Any]) -> str:
    checks = core["checks"]
    lines = [
        "## Summary",
        core["summary"],
        "",
        "## Safety / verification",
    ]
    for key in REQUIRED_CHECKS:
        lines.append(f"- [{'x' if checks[key] else ' '}] {key.replace('_', ' ')}")
    lines.extend([
        "",
        "---",
        "Created as a **draft** by DAIS Beginner-Safe PR Creator. Review and normal repository governance remain required.",
    ])
    return "\n".join(lines) + "\n"


def build_plan(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise InputError("input must be an object")
    core = _plan_core(data)
    digest = hashlib.sha256(_canonical_bytes(core)).hexdigest()
    return {
        **core,
        "plan_sha256": digest,
        "pull_request": {
            "title": core["title"],
            "body": _pr_body(core),
            "base": core["base"],
            "head": core["head"],
            "draft": True,
            "maintainer_can_modify": False,
        },
        "execution": {
            "network_request_performed": False,
            "branch_pushed": False,
            "pull_request_created": False,
            "review_requested": False,
            "merge_performed": False,
        },
    }


def _safe_api_error(status: int | None, operation: str) -> ApiFailure:
    return ApiFailure(f"GitHub API {operation} failed" + (f" with HTTP {status}" if status is not None else ""))


def github_request(method: str, path: str, token: str, payload: dict[str, Any] | None = None) -> Any:
    if not path.startswith("/") or "//" in path:
        raise SafetyRefusal("internal API path is invalid")
    url = API_ROOT + path
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": f"dais-beginner-safe-pr/{VERSION}",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=20) as response:  # noqa: S310 - URL is hard-coded to api.github.com
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except HTTPError as exc:
        raise _safe_api_error(exc.code, method) from None
    except (URLError, TimeoutError, OSError, json.JSONDecodeError):
        raise _safe_api_error(None, method) from None


def _ref_path(repository: str, branch: str) -> str:
    return f"/repos/{repository}/git/ref/heads/{quote(branch, safe='/')}"


def create_draft_pr(
    plan: dict[str, Any],
    *,
    expected_plan_sha256: str,
    confirmation: str,
    token: str,
    environment: dict[str, str],
    request_fn: Callable[[str, str, str, dict[str, Any] | None], Any] = github_request,
) -> dict[str, Any]:
    if plan.get("decision") != "READY_FOR_DRAFT_CREATE" or plan.get("failed_checks"):
        raise SafetyRefusal("all safety checks must pass before draft creation")
    actual_hash = str(plan.get("plan_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", expected_plan_sha256 or "") or expected_plan_sha256 != actual_hash:
        raise SafetyRefusal("expected plan hash does not match the reviewed plan")
    if confirmation != CONFIRMATION:
        raise SafetyRefusal(f"explicit confirmation must equal {CONFIRMATION}")
    if not token:
        raise SafetyRefusal("a repository-scoped GitHub token is required only for create mode")

    repository = str(plan["repository"])
    if environment.get("GITHUB_REPOSITORY") != repository:
        raise SafetyRefusal("cross-repository creation is refused; repository must equal GITHUB_REPOSITORY")
    event_name = environment.get("GITHUB_EVENT_NAME", "")
    if event_name not in ALLOWED_CREATE_EVENTS:
        raise SafetyRefusal("create mode is allowed only from push or workflow_dispatch; privileged/untrusted event contexts are refused")

    base = str(plan["base"])
    head = str(plan["head"])
    # Require both branches to exist in the same repository before any mutation.
    request_fn("GET", _ref_path(repository, base), token, None)
    request_fn("GET", _ref_path(repository, head), token, None)

    owner = repository.split("/", 1)[0]
    query = urlencode({"state": "open", "base": base, "head": f"{owner}:{head}", "per_page": 10})
    existing = request_fn("GET", f"/repos/{repository}/pulls?{query}", token, None)
    if not isinstance(existing, list):
        raise ApiFailure("GitHub API returned an unexpected open-PR response shape")
    if len(existing) > 1:
        raise SafetyRefusal("multiple matching open pull requests require human review")
    if existing:
        pr = existing[0]
        if pr.get("draft") is not True:
            raise SafetyRefusal("a matching non-draft pull request already exists; this tool will not alter it")
        return {
            "status": "EXISTING_DRAFT_REUSED",
            "created": False,
            "plan_sha256": actual_hash,
            "pr_number": int(pr["number"]),
            "pr_url": str(pr["html_url"]),
            "draft": True,
            "repository": repository,
        }

    payload = dict(plan["pull_request"])
    if payload.get("draft") is not True or payload.get("maintainer_can_modify") is not False:
        raise SafetyRefusal("internal draft-only payload invariant failed")
    created = request_fn("POST", f"/repos/{repository}/pulls", token, payload)
    if not isinstance(created, dict) or created.get("draft") is not True:
        raise ApiFailure("GitHub API did not confirm creation of a draft pull request")
    if created.get("base", {}).get("ref") != base or created.get("head", {}).get("ref") != head:
        raise ApiFailure("GitHub API returned a pull request outside the reviewed branch scope")
    return {
        "status": "DRAFT_CREATED",
        "created": True,
        "plan_sha256": actual_hash,
        "pr_number": int(created["number"]),
        "pr_url": str(created["html_url"]),
        "draft": True,
        "repository": repository,
    }


def _bool_env(name: str) -> bool:
    value = os.environ.get(name, "").strip().lower()
    if value not in {"true", "false"}:
        raise InputError(f"{name} must be true or false")
    return value == "true"


def _input_from_env() -> dict[str, Any]:
    return {
        "repository": os.environ.get("INPUT_REPOSITORY", ""),
        "title": os.environ.get("INPUT_TITLE", ""),
        "summary": os.environ.get("INPUT_SUMMARY", ""),
        "base": os.environ.get("INPUT_BASE", ""),
        "head": os.environ.get("INPUT_HEAD", ""),
        "checks": {
            "tests_run": _bool_env("INPUT_TESTS_RUN"),
            "ci_expected": _bool_env("INPUT_CI_EXPECTED"),
            "secrets_reviewed": _bool_env("INPUT_SECRETS_REVIEWED"),
            "scope_reviewed": _bool_env("INPUT_SCOPE_REVIEWED"),
            "rollback_considered": _bool_env("INPUT_ROLLBACK_CONSIDERED"),
        },
    }


def _write_outputs(values: dict[str, Any]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    safe = {
        "decision": values.get("decision", values.get("status", "")),
        "plan-sha256": values.get("plan_sha256", ""),
        "pr-number": values.get("pr_number", ""),
        "pr-url": values.get("pr_url", ""),
        "created": str(values.get("created", False)).lower(),
    }
    with Path(output_path).open("a", encoding="utf-8") as handle:
        for key, value in safe.items():
            handle.write(f"{key}={value}\n")


def action_main() -> int:
    try:
        plan = build_plan(_input_from_env())
        mode = os.environ.get("INPUT_MODE", "plan").strip().lower()
        if mode not in {"plan", "create"}:
            raise InputError("mode must be plan or create")
        if mode == "plan":
            result = plan
        else:
            result = create_draft_pr(
                plan,
                expected_plan_sha256=os.environ.get("INPUT_EXPECTED_PLAN_SHA256", ""),
                confirmation=os.environ.get("INPUT_CONFIRMATION", ""),
                token=os.environ.get("INPUT_GITHUB_TOKEN", ""),
                environment=dict(os.environ),
            )
        _write_outputs(result)
        print(json.dumps({k: v for k, v in result.items() if k not in {"pull_request", "summary"}}, sort_keys=True))
        return 0
    except (InputError, SafetyRefusal, ApiFailure) as exc:
        print(f"SAFE_PR_REFUSAL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(action_main())
