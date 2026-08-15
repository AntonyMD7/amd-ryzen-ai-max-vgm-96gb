import pytest

from scripts.accessibility_inclusion import AccessibilityError, evaluate


def test_voice_first_checklist_exposes_missing_fallbacks():
    result = evaluate({
        "mode": "checklist", "profile": "voice_first",
        "transcript_available": True, "text_fallback_available": False,
        "push_to_talk_or_clear_recording_state": True, "audio_retention_explained": True,
        "error_recovery_available": False,
    })
    assert result["roadmap_id"] == "P-088"
    assert set(result["missing"]) == {"text_fallback_available", "error_recovery_available"}
    assert result["semantics"]["accessibility_certified"] is False


def test_screen_reader_elder_repo_and_aac_profiles_map_correctly():
    profiles = {
        "screen_reader": ("P-089", ["semantic_landmarks", "accessible_names", "heading_order_reviewed", "status_announced", "focus_order_reviewed", "images_have_alt_strategy"]),
        "elder_friendly": ("P-090", ["text_resizes_without_loss", "large_touch_targets_reviewed", "plain_language", "high_contrast_option_or_compliant_default", "timeouts_avoidable", "critical_actions_confirmed"]),
        "repo_template": ("P-099", ["accessibility_statement", "keyboard_test_path", "screen_reader_test_path", "contrast_test_path", "captions_policy", "issue_template_for_accessibility"]),
        "assistive_communication": ("P-100", ["non_voice_input_available", "large_target_mode", "symbol_or_text_choice", "caregiver_override_not_silent", "emergency_message_reviewed", "offline_core_messages"]),
    }
    for profile, (roadmap, keys) in profiles.items():
        payload = {"mode": "checklist", "profile": profile, **{key: True for key in keys}}
        result = evaluate(payload)
        assert result["roadmap_id"] == roadmap
        assert result["missing"] == []
        assert result["status"] == "CHECKLIST_PASSES_MANUAL_ACCEPTANCE_STILL_REQUIRED"


def test_reading_level_plan_preserves_material_facts():
    result = evaluate({"mode": "reading_level", "audience": "beginner"})
    assert result["roadmap_id"] == "P-092"
    for required in ("dates", "numbers", "warnings", "obligations", "uncertainty", "citations"):
        assert required in result["preserve"]
    assert result["execution"]["text_transformed"] is False


def test_translation_validation_needs_people_and_critical_term_review():
    result = evaluate({"mode": "translation_validation", "language": "es", "reviewer_count": 1, "community_review": True, "critical_terms_reviewed": False})
    assert result["roadmap_id"] == "P-094"
    assert result["status"] == "VALIDATION_GAPS"
    assert result["semantics"]["translation_generated"] is False


def test_wcag_scanner_is_integration_plan_not_conformance_claim():
    result = evaluate({"mode": "wcag_scan_plan", "target_class": "component_fixture"})
    assert result["roadmap_id"] == "P-095"
    assert set(result["execution"].values()) == {False}
    assert result["semantics"]["wcag_conformance_proven"] is False


def test_contrast_black_white_and_low_contrast_cases():
    bw = evaluate({"mode": "contrast", "foreground": "#000000", "background": "#FFFFFF", "large_text": False})
    assert bw["roadmap_id"] == "P-096"
    assert bw["contrast_ratio"] == 21.0
    assert bw["wcag_2_text_threshold_checks"] == {"AA": True, "AAA": True}
    low = evaluate({"mode": "contrast", "foreground": "#777777", "background": "#FFFFFF", "large_text": False})
    assert low["wcag_2_text_threshold_checks"]["AA"] is False
    assert low["semantics"]["page_wcag_conformance_proven"] is False


def test_keyboard_audit_reports_review_without_running_browser():
    result = evaluate({"mode": "keyboard", "components": [
        {"id": "save-button", "keyboard_reachable": True, "focus_visible": True, "keyboard_operable": True},
        {"id": "custom-menu", "keyboard_reachable": True, "focus_visible": False, "keyboard_operable": True},
    ]})
    assert result["roadmap_id"] == "P-097"
    assert result["review_count"] == 1
    assert result["semantics"]["browser_test_executed"] is False


def test_caption_manifest_requires_caption_transcript_and_human_review():
    result = evaluate({"mode": "captions", "media_id": "lesson-1", "language": "en", "captions_available": True, "transcript_available": True, "human_reviewed": False})
    assert result["roadmap_id"] == "P-098"
    assert result["status"] == "CAPTION_TRANSCRIPT_GAPS"
    assert result["execution"]["caption_file_generated"] is False


def test_invalid_inputs_fail_closed():
    with pytest.raises(AccessibilityError):
        evaluate({"mode": "contrast", "foreground": "red", "background": "#FFFFFF", "large_text": False})
    with pytest.raises(AccessibilityError):
        evaluate({"mode": "translation_validation", "language": "es", "reviewer_count": -1, "community_review": True, "critical_terms_reviewed": True})
    with pytest.raises(AccessibilityError):
        evaluate({"mode": "unknown"})
