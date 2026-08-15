from copy import deepcopy

import pytest

from scripts.system_support_planner import PlanningError, make_plan


def test_windows_repair_emits_verification_only_commands():
    request = {"platform": "windows", "area": "windows_repair", "observations": {"booted": True}}
    original = deepcopy(request)

    result = make_plan(request)

    assert request == original
    assert result["roadmap_id"] == "P-003"
    assert result["disposition"] == "READ_ONLY_PREFLIGHT"
    assert "sfc /verifyonly" in result["read_only_checks"]
    assert all("/scannow" not in command.lower() for command in result["read_only_checks"])
    assert all("/restorehealth" not in command.lower() for command in result["read_only_checks"])
    assert result["safety"]["commands_executed"] is False
    assert result["safety"]["repair_performed"] is False


def test_linux_repair_is_observation_only():
    result = make_plan({"platform": "linux", "area": "linux_repair", "observations": {"booted": True}})

    assert result["roadmap_id"] == "P-004"
    assert result["read_only_checks"] == [
        "systemctl --failed --no-pager",
        "journalctl -p err -b --no-pager --lines=100",
    ]
    assert result["evidence_semantics"]["plan_is_diagnostic_proof"] is False


@pytest.mark.parametrize(
    ("area", "expected_id"),
    [
        ("driver", "P-005"),
        ("bios_uefi", "P-006"),
        ("network", "P-007"),
        ("peripheral", "P-008"),
        ("compatibility", "P-009"),
        ("firmware", "P-010"),
    ],
)
def test_canonical_roadmap_mapping(area, expected_id):
    result = make_plan({"platform": "linux", "area": area, "observations": {}})
    assert result["roadmap_id"] == expected_id


def test_bios_and_windows_firmware_fail_to_vendor_guidance_without_guessing():
    bios = make_plan({"platform": "windows", "area": "bios_uefi", "observations": {}})
    firmware = make_plan({"platform": "windows", "area": "firmware", "observations": {}})

    assert bios["disposition"] == "VENDOR_GUIDANCE_REQUIRED"
    assert bios["read_only_checks"] == []
    assert firmware["disposition"] == "VENDOR_GUIDANCE_REQUIRED"
    assert firmware["read_only_checks"] == []


def test_linux_firmware_discovers_but_never_updates():
    result = make_plan({"platform": "linux", "area": "firmware", "observations": {"fwupd_present": True}})

    assert result["read_only_checks"] == ["fwupdmgr get-devices --json"]
    assert all("update" not in command.lower() for command in result["read_only_checks"])
    assert all("refresh" not in command.lower() for command in result["read_only_checks"])
    assert result["safety"]["firmware_updated"] is False


def test_network_plan_contains_no_modify_add_or_delete_commands():
    for platform in ("windows", "linux"):
        result = make_plan({"platform": platform, "area": "network", "observations": {}})
        joined = "\n".join(result["read_only_checks"]).lower()
        assert "connection modify" not in joined
        assert "connection add" not in joined
        assert "connection delete" not in joined
        assert result["safety"]["network_changed"] is False


def test_only_boolean_observation_names_are_retained():
    result = make_plan(
        {
            "platform": "windows",
            "area": "driver",
            "observations": {"device_manager_has_warning": True, "network_available": False},
        }
    )

    assert result["observed_fact_names"] == ["device_manager_has_warning", "network_available"]
    assert result["observed_true_count"] == 1
    assert result["safety"]["raw_logs_returned"] is False
    assert result["safety"]["free_text_echoed"] is False


def test_free_text_observations_fail_closed():
    with pytest.raises(PlanningError):
        make_plan(
            {
                "platform": "windows",
                "area": "driver",
                "observations": {"error": "PCI\\VEN_1234 secret-like-machine-data"},
            }
        )


def test_cross_platform_repair_area_mismatch_fails_closed():
    with pytest.raises(PlanningError):
        make_plan({"platform": "linux", "area": "windows_repair", "observations": {}})
    with pytest.raises(PlanningError):
        make_plan({"platform": "windows", "area": "linux_repair", "observations": {}})


def test_unknown_platform_and_area_fail_closed():
    with pytest.raises(PlanningError):
        make_plan({"platform": "macos", "area": "network", "observations": {}})
    with pytest.raises(PlanningError):
        make_plan({"platform": "linux", "area": "repair_everything", "observations": {}})


def test_plan_never_claims_proof_or_mutation_authority():
    result = make_plan({"platform": "windows", "area": "compatibility", "observations": {}})

    assert set(result["evidence_semantics"].values()) == {False}
    assert result["safety"]["mutation_allowed"] is False
    assert result["safety"]["reboot_requested"] is False
