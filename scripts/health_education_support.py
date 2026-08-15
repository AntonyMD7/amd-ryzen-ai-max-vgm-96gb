#!/usr/bin/env python3
"""Guardrailed public-health/medical-education reference contracts.

This module intentionally does not diagnose, prescribe, calculate clinical
scores, check medication interactions, execute emergency protocols, or accept
patient identifiers.  It produces provenance-first plans/manifests that can be
used by later applications after independent clinical, legal, privacy and
jurisdictional review.

Roadmap scope: P-134 through P-147 (IN PROGRESS reference work only).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlparse

ROADMAP_IDS = tuple(f"P-{n:03d}" for n in range(134, 148))
ALLOWED_DATA_CLASSES = {"PUBLIC", "SYNTHETIC", "LOCAL_SENSITIVE"}
FORBIDDEN_URL_KEYS = {"token", "access_token", "api_key", "apikey", "key", "password", "secret"}
RXCUI_RE = re.compile(r"^[0-9]{1,12}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+\-]{0,63}$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._\-]{1,63}$")


class HealthSafetyError(ValueError):
    """Raised when a public reference manifest violates a safety boundary."""


def _clean_label(value: str, field: str, *, max_len: int = 120) -> str:
    if not isinstance(value, str):
        raise HealthSafetyError(f"{field} must be text")
    value = " ".join(value.strip().split())
    if not value or len(value) > max_len:
        raise HealthSafetyError(f"{field} must be 1..{max_len} characters")
    if any(c in value for c in "\r\n\x00"):
        raise HealthSafetyError(f"{field} contains forbidden control characters")
    return value


def _safe_public_url(value: str, field: str = "source_url") -> str:
    value = _clean_label(value, field, max_len=500)
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise HealthSafetyError(f"{field} must be a credential-free https URL")
    query_keys = {k.lower() for k, _ in parse_qsl(parsed.query, keep_blank_values=True)}
    if query_keys & FORBIDDEN_URL_KEYS:
        raise HealthSafetyError(f"{field} must not contain credential-like query parameters")
    return value


def _source(name: str, url: str, version: str, accessed: str | None = None) -> dict[str, str]:
    version = _clean_label(version, "source version", max_len=64)
    if not VERSION_RE.fullmatch(version):
        raise HealthSafetyError("source version has unsupported characters")
    return {
        "name": _clean_label(name, "source name"),
        "url": _safe_public_url(url),
        "version": version,
        "accessed": accessed or date.today().isoformat(),
    }


def anatomy_education_manifest(topic: str, sources: Iterable[dict[str, str]]) -> dict[str, Any]:
    normalized = []
    for item in sources:
        normalized.append(_source(item["name"], item["url"], item["version"], item.get("accessed")))
    if not normalized:
        raise HealthSafetyError("at least one anatomy source is required")
    return {
        "roadmap_id": "P-134",
        "topic": _clean_label(topic, "topic"),
        "sources": normalized,
        "intended_use": "EDUCATION_ONLY",
        "clinical_decision_support": False,
        "diagnosis": False,
        "treatment_guidance": False,
        "limitations": [
            "anatomical datasets may be incomplete or non-representative",
            "source-specific licensing and asset rights require separate review",
        ],
    }


def medication_education_manifest(
    display_name: str,
    rxcui: str,
    label_source: dict[str, str],
    mechanism_source: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not RXCUI_RE.fullmatch(str(rxcui)):
        raise HealthSafetyError("rxcui must be a numeric RxNorm identifier")
    result: dict[str, Any] = {
        "roadmap_id": "P-135",
        "display_name": _clean_label(display_name, "display_name"),
        "rxcui": str(rxcui),
        "identity_authority": "NLM RxNorm",
        "label_source": _source(**label_source),
        "mechanism_source": None,
        "educational_only": True,
        "personalized_advice": False,
        "dose_recommendation": False,
        "interaction_clearance": False,
    }
    if mechanism_source:
        result["mechanism_source"] = _source(**mechanism_source)
    return result


def clinical_calculator_manifest(
    calculator_id: str,
    version: str,
    source: dict[str, str],
    inputs: list[dict[str, str]],
    reference_vectors: list[dict[str, Any]],
) -> dict[str, Any]:
    calculator_id = calculator_id.strip().lower()
    if not ID_RE.fullmatch(calculator_id):
        raise HealthSafetyError("calculator_id must be a stable lowercase identifier")
    if not inputs or not reference_vectors:
        raise HealthSafetyError("calculator manifests require inputs and independently sourced test vectors")
    allowed_keys = {"name", "unit", "type"}
    normalized_inputs = []
    for item in inputs:
        if set(item) != allowed_keys:
            raise HealthSafetyError("calculator input records may contain only name/unit/type")
        normalized_inputs.append({k: _clean_label(v, k, max_len=64) for k, v in item.items()})
    return {
        "roadmap_id": "P-136",
        "calculator_id": calculator_id,
        "version": _clean_label(version, "version", max_len=64),
        "source": _source(**source),
        "inputs": normalized_inputs,
        "reference_vector_count": len(reference_vectors),
        "reference_vectors_present": True,
        "formula_execution_enabled": False,
        "clinical_use_enabled": False,
        "required_next_gate": "independent formula implementation review plus reference-vector and clinical acceptance testing",
    }


def evidence_navigation_plan(query: str, *, database: str = "pubmed") -> dict[str, Any]:
    query = _clean_label(query, "query", max_len=300)
    if database.lower() not in {"pubmed", "pmc"}:
        raise HealthSafetyError("database must be pubmed or pmc")
    return {
        "roadmap_id": "P-137",
        "database": database.lower(),
        "query": query,
        "upstream": "NCBI Entrez E-utilities",
        "network_request_performed": False,
        "ranking_claim": False,
        "evidence_quality_claim": False,
        "required_user_notice": "retrieval results require appraisal; indexing does not establish clinical validity",
    }


def equipment_checklist(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized = []
    for item in items:
        allowed = {"item", "required", "present", "service_due"}
        if set(item) - allowed:
            raise HealthSafetyError("equipment items contain unsupported fields")
        normalized.append(
            {
                "item": _clean_label(item["item"], "item"),
                "required": bool(item.get("required", True)),
                "present": bool(item.get("present", False)),
                "service_due": item.get("service_due"),
            }
        )
    return {
        "roadmap_id": "P-138",
        "items": normalized,
        "patient_data": False,
        "inspection_performed": False,
        "certification_claim": False,
    }


def medical_inventory_snapshot(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized = []
    for item in items:
        allowed = {"item", "quantity", "unit", "expiry_month"}
        if set(item) - allowed:
            raise HealthSafetyError("inventory records contain unsupported fields")
        quantity = item.get("quantity")
        if not isinstance(quantity, int) or quantity < 0:
            raise HealthSafetyError("quantity must be a non-negative integer")
        expiry = item.get("expiry_month")
        if expiry is not None and not re.fullmatch(r"20[0-9]{2}-(0[1-9]|1[0-2])", str(expiry)):
            raise HealthSafetyError("expiry_month must be YYYY-MM")
        normalized.append(
            {
                "item": _clean_label(item["item"], "item"),
                "quantity": quantity,
                "unit": _clean_label(item.get("unit", "each"), "unit", max_len=32),
                "expiry_month": expiry,
            }
        )
    return {
        "roadmap_id": "P-139",
        "items": normalized,
        "patient_data": False,
        "procurement_action_performed": False,
    }


def remote_handover_template() -> dict[str, Any]:
    return {
        "roadmap_id": "P-140",
        "template_version": "0.1",
        "sections": [
            "operational_context",
            "open_clinical_tasks",
            "equipment_and_stock",
            "pending_follow_up",
            "escalation_and_contact_process",
            "source_and_timestamp",
        ],
        "contains_patient_data": False,
        "public_example_requires_synthetic_data": True,
        "runtime_requirement": "real patient data must remain in an approved private clinical system",
    }


def emergency_workflow_manifest(protocol_id: str, version: str, jurisdiction: str, source_url: str) -> dict[str, Any]:
    protocol_id = protocol_id.strip().lower()
    if not ID_RE.fullmatch(protocol_id):
        raise HealthSafetyError("protocol_id must be a stable lowercase identifier")
    return {
        "roadmap_id": "P-141",
        "protocol_id": protocol_id,
        "protocol_version": _clean_label(version, "protocol version", max_len=64),
        "jurisdiction": _clean_label(jurisdiction, "jurisdiction", max_len=80),
        "source_url": _safe_public_url(source_url),
        "clinical_steps_embedded": False,
        "execution_enabled": False,
        "required_next_gate": "local clinical authority approval of the exact protocol and offline failure mode",
    }


def public_health_information_manifest(title: str, source: dict[str, str], language: str = "en") -> dict[str, Any]:
    return {
        "roadmap_id": "P-142",
        "title": _clean_label(title, "title"),
        "source": _source(**source),
        "language": _clean_label(language, "language", max_len=16).lower(),
        "source_text_copied": False,
        "medical_advice": False,
    }


def health_literacy_plan(content_id: str, source_language: str, target_language: str) -> dict[str, Any]:
    if not ID_RE.fullmatch(content_id.strip().lower()):
        raise HealthSafetyError("content_id must be a stable non-sensitive identifier")
    return {
        "roadmap_id": "P-143",
        "content_id": content_id.strip().lower(),
        "source_language": _clean_label(source_language, "source_language", max_len=16).lower(),
        "target_language": _clean_label(target_language, "target_language", max_len=16).lower(),
        "preserve_numbers_units_warnings": True,
        "clinical_meaning_review_required": True,
        "content_transformed": False,
    }


def medication_list_manifest(medications: Iterable[dict[str, str]], *, data_class: str = "LOCAL_SENSITIVE") -> dict[str, Any]:
    if data_class not in ALLOWED_DATA_CLASSES:
        raise HealthSafetyError("unsupported data_class")
    normalized = []
    for med in medications:
        if set(med) != {"display_name", "rxcui"}:
            raise HealthSafetyError("medication records may contain only display_name and rxcui")
        if not RXCUI_RE.fullmatch(str(med["rxcui"])):
            raise HealthSafetyError("invalid RxCUI")
        normalized.append({"display_name": _clean_label(med["display_name"], "display_name"), "rxcui": str(med["rxcui"])})
    return {
        "roadmap_id": "P-144",
        "medications": normalized,
        "data_class": data_class,
        "patient_identifier": None,
        "cloud_upload_authorized": False,
        "clinical_reconciliation_performed": False,
    }


def medication_interaction_information_plan(rxcuis: Iterable[str]) -> dict[str, Any]:
    normalized = []
    for value in rxcuis:
        value = str(value)
        if not RXCUI_RE.fullmatch(value):
            raise HealthSafetyError("invalid RxCUI")
        normalized.append(value)
    if len(set(normalized)) < 2:
        raise HealthSafetyError("at least two distinct RxCUIs are required")
    return {
        "roadmap_id": "P-145",
        "rxcuis": sorted(set(normalized)),
        "identity_authority": "NLM RxNorm",
        "label_information_authority": "NLM DailyMed / FDA Structured Product Label",
        "interaction_check_performed": False,
        "safe_combination_claim": False,
        "unsafe_combination_claim": False,
        "required_next_gate": "current authoritative interaction information plus pharmacist/clinician review for patient-specific decisions",
    }


def offline_medical_reference_manifest(
    title: str,
    source_url: str,
    source_version: str,
    redistribution_rights: str,
    sha256: str,
) -> dict[str, Any]:
    if redistribution_rights not in {"CONFIRMED", "NOT_CONFIRMED"}:
        raise HealthSafetyError("redistribution_rights must be CONFIRMED or NOT_CONFIRMED")
    if not SHA256_RE.fullmatch(sha256):
        raise HealthSafetyError("sha256 must be lowercase hexadecimal")
    return {
        "roadmap_id": "P-146",
        "title": _clean_label(title, "title"),
        "source_url": _safe_public_url(source_url),
        "source_version": _clean_label(source_version, "source_version", max_len=64),
        "redistribution_rights": redistribution_rights,
        "sha256": sha256,
        "publishable": redistribution_rights == "CONFIRMED",
        "clinical_currency_verified": False,
        "offline_package_created": False,
    }


def emergency_preparedness_checklist() -> dict[str, Any]:
    return {
        "roadmap_id": "P-147",
        "authority": "FEMA Ready.gov for general preparedness concepts; local emergency authorities supersede",
        "categories": [
            "local_alerts_and_contacts",
            "communication_plan",
            "water_food_and_essential_supplies",
            "medications_and_health_needs",
            "documents_and_accessibility_needs",
            "power_and_charging",
            "evacuation_and_shelter_information",
        ],
        "location_specific_instructions_embedded": False,
        "emergency_service_contact_inferred": False,
        "medical_treatment_guidance": False,
    }
