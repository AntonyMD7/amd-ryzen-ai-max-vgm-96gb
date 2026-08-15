import pytest

from scripts.install_config_planner import PlanError, evaluate


DIGEST = "a" * 64


def test_installation_plan_blocks_without_recovery_and_approval():
    result = evaluate({
        "mode": "installation",
        "package": "example-tool",
        "platform": "linux",
        "source_authority": "vendor-repo",
        "version": "1.2.3",
        "sha256": DIGEST,
        "recovery_ready": False,
        "approval_granted": True,
    })
    assert result["roadmap_id"] == "P-019"
    assert result["disposition"] == "BLOCKED_PRECONDITIONS"
    assert result["execution"]["package_installed"] is False
    assert result["execution"]["command_emitted"] is False


def test_installation_plan_is_still_plan_only_when_gates_pass():
    result = evaluate({
        "mode": "installation",
        "package": "example-tool",
        "platform": "windows",
        "source_authority": "vendor",
        "version": "2026.08",
        "sha256": DIGEST.upper(),
        "recovery_ready": True,
        "approval_granted": True,
    })
    assert result["disposition"] == "REVIEWABLE_MUTATION_PLAN"
    assert result["sha256"] == DIGEST
    assert set(result["execution"].values()) == {False}


def test_installation_requires_explicit_version_digest_and_bounded_ids():
    base = {
        "mode": "installation",
        "package": "tool",
        "platform": "linux",
        "source_authority": "vendor",
        "version": "1.0",
        "sha256": DIGEST,
        "recovery_ready": True,
        "approval_granted": True,
    }
    for key, bad in (("sha256", "nope"), ("version", ""), ("package", "tool; rm -rf /")):
        broken = dict(base)
        broken[key] = bad
        with pytest.raises(PlanError):
            evaluate(broken)


def test_configuration_audit_uses_boolean_facts_only():
    result = evaluate({
        "mode": "configuration_audit",
        "facts": {"secure_boot_enabled": True, "guest_account_disabled": False},
        "rules": [
            {"id": "secure-boot", "fact": "secure_boot_enabled", "expected": True, "severity": "high"},
            {"id": "guest-off", "fact": "guest_account_disabled", "expected": True, "severity": "review"},
            {"id": "disk-encryption", "fact": "disk_encryption_enabled", "expected": True, "severity": "high"},
        ],
    })
    assert result["roadmap_id"] == "P-020"
    assert result["summary"] == {"pass": 1, "review": 1, "unknown": 1}
    assert result["privacy"]["raw_configuration_returned"] is False
    assert result["semantics"]["audit_mutates_configuration"] is False


def test_configuration_audit_does_not_treat_unknown_as_pass():
    result = evaluate({
        "mode": "configuration_audit",
        "facts": {},
        "rules": [{"id": "r1", "fact": "known_good", "expected": True, "severity": "info"}],
    })
    assert result["findings"][0]["state"] == "UNKNOWN"
    assert result["summary"]["pass"] == 0


def test_free_text_configuration_values_fail_closed():
    with pytest.raises(PlanError):
        evaluate({
            "mode": "configuration_audit",
            "facts": {"password": "secret"},
            "rules": [],
        })


def test_bad_rule_or_unknown_mode_fails_closed():
    with pytest.raises(PlanError):
        evaluate({
            "mode": "configuration_audit",
            "facts": {"x": True},
            "rules": [{"id": "r1", "fact": "x", "expected": True, "severity": "critical"}],
        })
    with pytest.raises(PlanError):
        evaluate({"mode": "execute_everything"})
