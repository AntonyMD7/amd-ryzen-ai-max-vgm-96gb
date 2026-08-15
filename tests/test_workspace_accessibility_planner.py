import pytest

from scripts.workspace_accessibility_planner import WorkspacePlanError, evaluate


def test_drive_move_is_proposal_only():
    result = evaluate({"mode": "drive", "action": "propose_move"})
    assert result["roadmap_id"] == "P-077"
    assert result["required_access_class"] == "METADATA_READ_PLUS_EXPLICIT_WRITE_APPROVAL"
    assert set(result["execution"].values()) == {False}


def test_docs_knowledge_requires_explicit_authorized_count():
    result = evaluate({"mode": "docs", "authorized_source_count": 3})
    assert result["roadmap_id"] == "P-078"
    assert result["required_access_class"] == "EXPLICIT_DOCUMENT_READ_ALLOWLIST"
    assert result["execution"]["content_read"] is False


def test_sheets_and_gmail_separate_read_from_mutation():
    sheet = evaluate({"mode": "sheets", "operation": "append_proposal"})
    mail = evaluate({"mode": "gmail", "operation": "send_proposal"})
    assert sheet["roadmap_id"] == "P-079"
    assert "EXPLICIT_WRITE_APPROVAL" in sheet["required_access_class"]
    assert mail["roadmap_id"] == "P-080"
    assert mail["required_access_class"] == "EXPLICIT_MUTATION_APPROVAL"
    assert mail["execution"]["message_sent"] is False


def test_calendar_proposal_never_changes_event():
    result = evaluate({"mode": "calendar", "operation": "create_proposal"})
    assert result["roadmap_id"] == "P-081"
    assert result["execution"]["calendar_event_changed"] is False


def test_plain_language_requires_risk_preservation():
    result = evaluate({"mode": "plain_language", "source_complexity": "high"})
    assert result["roadmap_id"] == "P-082"
    assert "do not omit material risk" in result["requirements"]
    assert result["semantics"]["meaning_preserved_verified"] is False


def test_forms_checklist_surfaces_accessibility_gaps():
    result = evaluate({
        "mode": "forms",
        "plain_labels": True,
        "one_idea_per_question": True,
        "required_fields_explained": False,
        "error_recovery_explained": True,
        "keyboard_path_considered": False,
        "language_declared": True,
    })
    assert result["roadmap_id"] == "P-083"
    assert set(result["missing"]) == {"required_fields_explained", "keyboard_path_considered"}


def test_browser_extension_flags_sensitive_permissions():
    result = evaluate({"mode": "browser_extension", "permissions": ["storage", "history", "tabs"]})
    assert result["roadmap_id"] == "P-084"
    assert result["status"] == "SECURITY_REVIEW_REQUIRED"
    assert set(result["broad_or_sensitive_permissions"]) == {"history", "tabs"}
    assert result["execution"]["browser_permission_granted"] is False


def test_addon_is_manifest_only():
    result = evaluate({"mode": "addon", "hosts": ["gmail", "calendar", "gmail"]})
    assert result["roadmap_id"] == "P-085"
    assert result["hosts"] == ["calendar", "gmail"]
    assert set(result["deployment"].values()) == {False}


def test_api_wrapper_requires_explicit_write_classification():
    result = evaluate({"mode": "api_wrapper", "api_id": "example-v1", "auth": "oauth2", "write_capable": True})
    assert result["roadmap_id"] == "P-086"
    assert result["required_control"] == "EXPLICIT_WRITE_APPROVAL_AND_IDEMPOTENCY"
    assert result["execution"]["api_called"] is False


def test_unknown_modes_permissions_and_hosts_fail_closed():
    with pytest.raises(WorkspacePlanError):
        evaluate({"mode": "browser_extension", "permissions": ["permission with spaces"]})
    with pytest.raises(WorkspacePlanError):
        evaluate({"mode": "addon", "hosts": ["unknown"]})
    with pytest.raises(WorkspacePlanError):
        evaluate({"mode": "send_everything"})
