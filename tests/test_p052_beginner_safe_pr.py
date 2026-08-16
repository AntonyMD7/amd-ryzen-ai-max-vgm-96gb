from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

MODULE_PATH = Path(__file__).parents[1] / ".github" / "actions" / "beginner-safe-pr" / "safe_pr.py"
spec = importlib.util.spec_from_file_location("p052_safe_pr", MODULE_PATH)
assert spec and spec.loader
safe_pr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = safe_pr
spec.loader.exec_module(safe_pr)


def ready_input() -> dict:
    return {
        "repository": "AntonyMD7/example",
        "title": "Improve beginner documentation",
        "summary": "Adds a clearer START-HERE path and documents rollback.",
        "base": "main",
        "head": "docs/beginner-path",
        "checks": {key: True for key in safe_pr.REQUIRED_CHECKS},
    }


def test_plan_is_deterministic_network_free_and_draft_only():
    first = safe_pr.build_plan(ready_input())
    second = safe_pr.build_plan(ready_input())
    assert first["plan_sha256"] == second["plan_sha256"]
    assert len(first["plan_sha256"]) == 64
    assert first["decision"] == "READY_FOR_DRAFT_CREATE"
    assert first["pull_request"]["draft"] is True
    assert first["pull_request"]["maintainer_can_modify"] is False
    assert all(value is False for value in first["execution"].values())


def test_plan_blocks_until_every_safety_check_passes():
    data = ready_input()
    data["checks"]["rollback_considered"] = False
    result = safe_pr.build_plan(data)
    assert result["decision"] == "BLOCKED_UNTIL_SAFETY_CHECKS_COMPLETE"
    assert result["failed_checks"] == ["rollback_considered"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("summary", "credential token=github_pat_12345678901234567890"),
        ("summary", "password: CorrectHorseBatteryStaple"),
        ("summary", "-----BEGIN PRIVATE KEY-----"),
        ("title", "leak ghp_123456789012345678901234567890"),
    ],
)
def test_public_pr_text_refuses_obvious_sensitive_literals(field: str, value: str):
    data = ready_input()
    data[field] = value
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.build_plan(data)


@pytest.mark.parametrize("ref", ["../main", "fork:branch", "/main", "main/", "a//b", "refs@{1}", "x.lock"])
def test_branch_grammar_fails_closed(ref: str):
    data = ready_input()
    data["head"] = ref
    with pytest.raises(safe_pr.InputError):
        safe_pr.build_plan(data)


def test_same_head_and_base_is_refused():
    data = ready_input()
    data["head"] = "main"
    with pytest.raises(safe_pr.InputError):
        safe_pr.build_plan(data)


def test_unexpected_check_key_is_refused():
    data = ready_input()
    data["checks"]["skip_review"] = True
    with pytest.raises(safe_pr.InputError):
        safe_pr.build_plan(data)


def test_create_requires_exact_plan_hash_and_confirmation_before_network():
    plan = safe_pr.build_plan(ready_input())
    calls: list = []

    def request(*args):
        calls.append(args)
        raise AssertionError("network must not be reached")

    env = {"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "workflow_dispatch"}
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256="0" * 64,
            confirmation=safe_pr.CONFIRMATION,
            token="test-token",
            environment=env,
            request_fn=request,
        )
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirmation="yes",
            token="test-token",
            environment=env,
            request_fn=request,
        )
    assert calls == []


def test_create_refuses_cross_repository_and_privileged_untrusted_event():
    plan = safe_pr.build_plan(ready_input())
    never = lambda *args: (_ for _ in ()).throw(AssertionError("network must not be reached"))
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirmation=safe_pr.CONFIRMATION,
            token="test-token",
            environment={"GITHUB_REPOSITORY": "AntonyMD7/other", "GITHUB_EVENT_NAME": "workflow_dispatch"},
            request_fn=never,
        )
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirmation=safe_pr.CONFIRMATION,
            token="test-token",
            environment={"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "pull_request_target"},
            request_fn=never,
        )


def test_create_only_posts_exact_draft_payload_after_read_only_preflight():
    plan = safe_pr.build_plan(ready_input())
    calls: list[tuple] = []

    def request(method, path, token, payload=None):
        calls.append((method, path, token, payload))
        if method == "GET" and "/git/ref/heads/" in path:
            return {"ref": path}
        if method == "GET" and "/pulls?" in path:
            return []
        if method == "POST" and path == "/repos/AntonyMD7/example/pulls":
            assert payload == plan["pull_request"]
            assert payload["draft"] is True
            assert payload["maintainer_can_modify"] is False
            return {
                "number": 17,
                "html_url": "https://github.com/AntonyMD7/example/pull/17",
                "draft": True,
                "base": {"ref": "main"},
                "head": {"ref": "docs/beginner-path"},
            }
        raise AssertionError((method, path))

    result = safe_pr.create_draft_pr(
        plan,
        expected_plan_sha256=plan["plan_sha256"],
        confirmation=safe_pr.CONFIRMATION,
        token="never-emit-this-token",
        environment={"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "workflow_dispatch"},
        request_fn=request,
    )
    assert result["status"] == "DRAFT_CREATED"
    assert result["created"] is True
    assert result["draft"] is True
    assert "never-emit-this-token" not in repr(result)
    assert [call[0] for call in calls] == ["GET", "GET", "GET", "POST"]


def test_existing_draft_is_idempotently_reused_without_post():
    plan = safe_pr.build_plan(ready_input())
    methods: list[str] = []

    def request(method, path, token, payload=None):
        methods.append(method)
        if "/git/ref/heads/" in path:
            return {"ref": path}
        if "/pulls?" in path:
            return [{"number": 9, "html_url": "https://github.com/AntonyMD7/example/pull/9", "draft": True}]
        raise AssertionError("POST must not occur")

    result = safe_pr.create_draft_pr(
        plan,
        expected_plan_sha256=plan["plan_sha256"],
        confirmation=safe_pr.CONFIRMATION,
        token="test-token",
        environment={"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "push"},
        request_fn=request,
    )
    assert result["status"] == "EXISTING_DRAFT_REUSED"
    assert result["created"] is False
    assert "POST" not in methods


def test_existing_non_draft_is_never_modified():
    plan = safe_pr.build_plan(ready_input())

    def request(method, path, token, payload=None):
        if "/git/ref/heads/" in path:
            return {"ref": path}
        if "/pulls?" in path:
            return [{"number": 9, "html_url": "https://github.com/AntonyMD7/example/pull/9", "draft": False}]
        raise AssertionError("mutation must not occur")

    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirmation=safe_pr.CONFIRMATION,
            token="test-token",
            environment={"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "push"},
            request_fn=request,
        )


def test_failed_checks_can_never_be_overridden_by_confirmation():
    data = ready_input()
    data["checks"]["tests_run"] = False
    plan = safe_pr.build_plan(data)
    with pytest.raises(safe_pr.SafetyRefusal):
        safe_pr.create_draft_pr(
            plan,
            expected_plan_sha256=plan["plan_sha256"],
            confirmation=safe_pr.CONFIRMATION,
            token="test-token",
            environment={"GITHUB_REPOSITORY": "AntonyMD7/example", "GITHUB_EVENT_NAME": "workflow_dispatch"},
            request_fn=lambda *args: None,
        )
