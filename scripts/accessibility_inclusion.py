#!/usr/bin/env python3
"""Reference accessibility/inclusion checks and plans.

These helpers support evidence collection and design review; they do not claim
WCAG conformance, screen-reader compatibility, translation quality or clinical
fitness for assistive communication.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class AccessibilityError(ValueError):
    pass


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise AccessibilityError(f"{name} must be a bounded identifier")
    return value


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise AccessibilityError(f"{name} must be boolean")
    return value


def checklist(data: dict[str, Any]) -> dict[str, Any]:
    profile = data.get("profile")
    profiles = {
        "voice_first": ("P-088", ["transcript_available", "text_fallback_available", "push_to_talk_or_clear_recording_state", "audio_retention_explained", "error_recovery_available"]),
        "screen_reader": ("P-089", ["semantic_landmarks", "accessible_names", "heading_order_reviewed", "status_announced", "focus_order_reviewed", "images_have_alt_strategy"]),
        "elder_friendly": ("P-090", ["text_resizes_without_loss", "large_touch_targets_reviewed", "plain_language", "high_contrast_option_or_compliant_default", "timeouts_avoidable", "critical_actions_confirmed"]),
        "repo_template": ("P-099", ["accessibility_statement", "keyboard_test_path", "screen_reader_test_path", "contrast_test_path", "captions_policy", "issue_template_for_accessibility"]),
        "assistive_communication": ("P-100", ["non_voice_input_available", "large_target_mode", "symbol_or_text_choice", "caregiver_override_not_silent", "emergency_message_reviewed", "offline_core_messages"]),
    }
    if profile not in profiles:
        raise AccessibilityError("unsupported checklist profile")
    roadmap_id, names = profiles[profile]
    values = {name: _bool(data.get(name), name) for name in names}
    missing = [name for name, value in values.items() if not value]
    return {
        "schema_version": "0.1",
        "roadmap_id": roadmap_id,
        "profile": profile,
        "checks": values,
        "missing": missing,
        "status": "REVIEW_REQUIRED" if missing else "CHECKLIST_PASSES_MANUAL_ACCEPTANCE_STILL_REQUIRED",
        "semantics": {"accessibility_certified": False, "assistive_technology_test_executed": False},
    }


def reading_level_plan(data: dict[str, Any]) -> dict[str, Any]:
    audience = data.get("audience")
    if audience not in {"beginner", "general", "technical"}:
        raise AccessibilityError("audience must be beginner, general, or technical")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-092",
        "audience": audience,
        "preserve": ["names", "dates", "numbers", "warnings", "obligations", "uncertainty", "citations"],
        "techniques": ["shorter sentences", "define jargon", "one action per step", "use examples", "offer original wording"],
        "execution": {"source_text_read": False, "text_transformed": False},
        "semantics": {"meaning_preserved_verified": False, "reading_grade_certified": False},
    }


def translation_validation(data: dict[str, Any]) -> dict[str, Any]:
    language = _id(data.get("language"), "language")
    reviewer_count = data.get("reviewer_count")
    if isinstance(reviewer_count, bool) or not isinstance(reviewer_count, int) or reviewer_count < 0:
        raise AccessibilityError("reviewer_count must be non-negative integer")
    community_review = _bool(data.get("community_review"), "community_review")
    critical_terms_reviewed = _bool(data.get("critical_terms_reviewed"), "critical_terms_reviewed")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-094",
        "language": language,
        "reviewer_count": reviewer_count,
        "community_review": community_review,
        "critical_terms_reviewed": critical_terms_reviewed,
        "status": "HUMAN_VALIDATION_PRESENT" if reviewer_count > 0 and community_review and critical_terms_reviewed else "VALIDATION_GAPS",
        "requirements": ["preserve source", "record translation version", "record reviewer role/consent outside public artifact where needed", "escalate disputed safety-critical terms"],
        "semantics": {"translation_generated": False, "translation_quality_certified": False},
    }


def _linear_channel(value: int) -> float:
    s = value / 255.0
    return s / 12.92 if s <= 0.04045 else ((s + 0.055) / 1.055) ** 2.4


def _luminance(hex_color: str) -> float:
    if not isinstance(hex_color, str) or not HEX_COLOR.fullmatch(hex_color):
        raise AccessibilityError("colors must use #RRGGBB")
    r, g, b = (int(hex_color[i:i+2], 16) for i in (1, 3, 5))
    return 0.2126 * _linear_channel(r) + 0.7152 * _linear_channel(g) + 0.0722 * _linear_channel(b)


def contrast_check(data: dict[str, Any]) -> dict[str, Any]:
    foreground = data.get("foreground")
    background = data.get("background")
    large_text = _bool(data.get("large_text"), "large_text")
    l1, l2 = _luminance(foreground), _luminance(background)
    ratio = (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)
    aa_threshold = 3.0 if large_text else 4.5
    aaa_threshold = 4.5 if large_text else 7.0
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-096",
        "foreground": foreground.upper(),
        "background": background.upper(),
        "large_text": large_text,
        "contrast_ratio": round(ratio, 3),
        "wcag_2_text_threshold_checks": {"AA": ratio >= aa_threshold, "AAA": ratio >= aaa_threshold},
        "semantics": {"page_wcag_conformance_proven": False, "non_text_contrast_evaluated": False},
    }


def wcag_scan_plan(data: dict[str, Any]) -> dict[str, Any]:
    target_class = data.get("target_class")
    if target_class not in {"static_public_url", "local_test_page", "component_fixture"}:
        raise AccessibilityError("unsupported target_class")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-095",
        "target_class": target_class,
        "recommended_automation_engine": "axe-core or equivalent reviewed accessibility engine",
        "requirements": ["pin engine/version", "retain rule IDs", "manual keyboard review", "manual screen-reader sampling", "do not equate zero automated findings with conformance"],
        "execution": {"browser_opened": False, "scanner_run": False, "network_contacted": False},
        "semantics": {"wcag_conformance_proven": False},
    }


def keyboard_audit(data: dict[str, Any]) -> dict[str, Any]:
    components = data.get("components")
    if not isinstance(components, list) or len(components) > 500:
        raise AccessibilityError("components must be a bounded list")
    findings = []
    for item in components:
        if not isinstance(item, dict):
            raise AccessibilityError("component must be an object")
        component_id = _id(item.get("id"), "component.id")
        reachable = _bool(item.get("keyboard_reachable"), "keyboard_reachable")
        visible = _bool(item.get("focus_visible"), "focus_visible")
        operable = _bool(item.get("keyboard_operable"), "keyboard_operable")
        findings.append({"id": component_id, "state": "PASS" if reachable and visible and operable else "REVIEW"})
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-097",
        "findings": findings,
        "review_count": sum(item["state"] == "REVIEW" for item in findings),
        "semantics": {"browser_test_executed": False, "aria_pattern_correctness_proven": False},
    }


def caption_manifest(data: dict[str, Any]) -> dict[str, Any]:
    media_id = _id(data.get("media_id"), "media_id")
    language = _id(data.get("language"), "language")
    has_captions = _bool(data.get("captions_available"), "captions_available")
    has_transcript = _bool(data.get("transcript_available"), "transcript_available")
    captions_reviewed = _bool(data.get("human_reviewed"), "human_reviewed")
    return {
        "schema_version": "0.1",
        "roadmap_id": "P-098",
        "media_id": media_id,
        "language": language,
        "status": "REVIEWED_CAPTION_PATH_PRESENT" if has_captions and has_transcript and captions_reviewed else "CAPTION_TRANSCRIPT_GAPS",
        "recommended_exchange_format": "WebVTT where appropriate for web text tracks",
        "checks": {"captions_available": has_captions, "transcript_available": has_transcript, "human_reviewed": captions_reviewed},
        "execution": {"audio_transcribed": False, "caption_file_generated": False},
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    mode = data.get("mode")
    if mode == "checklist":
        return checklist(data)
    if mode == "reading_level":
        return reading_level_plan(data)
    if mode == "translation_validation":
        return translation_validation(data)
    if mode == "wcag_scan_plan":
        return wcag_scan_plan(data)
    if mode == "contrast":
        return contrast_check(data)
    if mode == "keyboard":
        return keyboard_audit(data)
    if mode == "captions":
        return caption_manifest(data)
    raise AccessibilityError("unsupported mode")


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
