#!/usr/bin/env python3
"""Privacy- and rights-aware reference contracts for roadmap P-148..P-155.

No scheduling assignment, event registration, donation/payment processing,
contact messaging, Scripture text redistribution, theological adjudication or
external service mutation is performed by this module.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable
from urllib.parse import urlparse

ROADMAP_IDS = tuple(f"P-{n:03d}" for n in range(148, 156))
LANG_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Z]{2})?$")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


class CommunitySafetyError(ValueError):
    pass


def _text(value: str, field: str, limit: int = 160) -> str:
    if not isinstance(value, str):
        raise CommunitySafetyError(f"{field} must be text")
    value = " ".join(value.strip().split())
    if not value or len(value) > limit or any(c in value for c in "\r\n\x00"):
        raise CommunitySafetyError(f"invalid {field}")
    return value


def _id(value: str, field: str) -> str:
    value = value.strip().lower()
    if not ID_RE.fullmatch(value):
        raise CommunitySafetyError(f"invalid {field}")
    return value


def _url(value: str) -> str:
    value = _text(value, "source_url", 500)
    p = urlparse(value)
    if p.scheme != "https" or not p.netloc or p.username or p.password:
        raise CommunitySafetyError("source_url must be credential-free HTTPS")
    return value


def volunteer_schedule_plan(roles: Iterable[dict[str, Any]]) -> dict[str, Any]:
    normalized = []
    for role in roles:
        if set(role) - {"role", "slots", "skills"}:
            raise CommunitySafetyError("volunteer role contains unsupported fields")
        slots = role.get("slots")
        if not isinstance(slots, int) or slots < 1 or slots > 1000:
            raise CommunitySafetyError("slots must be 1..1000")
        normalized.append({
            "role": _text(role["role"], "role", 80),
            "slots": slots,
            "skills": sorted({_text(x, "skill", 60) for x in role.get("skills", [])}),
        })
    return {
        "roadmap_id": "P-148",
        "roles": normalized,
        "personal_data": False,
        "volunteers_assigned": False,
        "calendar_mutated": False,
        "upstream_candidates": ["Cal.diy", "CiviCRM"],
    }


def community_event_manifest(event_id: str, title: str, timezone: str, *, capacity: int | None = None) -> dict[str, Any]:
    if capacity is not None and (not isinstance(capacity, int) or capacity < 1):
        raise CommunitySafetyError("capacity must be a positive integer")
    return {
        "roadmap_id": "P-149",
        "event_id": _id(event_id, "event_id"),
        "title": _text(title, "title"),
        "timezone": _text(timezone, "timezone", 64),
        "capacity": capacity,
        "registrations_collected": False,
        "ticketing_or_payment_enabled": False,
        "upstream_candidates": ["pretix", "CiviCRM"],
    }


def donation_admin_manifest(campaign_id: str, currency: str, categories: Iterable[str]) -> dict[str, Any]:
    currency = _text(currency, "currency", 3).upper()
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise CommunitySafetyError("currency must be a three-letter code")
    return {
        "roadmap_id": "P-150",
        "campaign_id": _id(campaign_id, "campaign_id"),
        "currency": currency,
        "categories": sorted({_text(x, "category", 80) for x in categories}),
        "donor_identity_collected": False,
        "payment_credentials_collected": False,
        "payment_processed": False,
        "tax_receipt_claim": False,
        "upstream_candidate": "CiviCRM",
    }


def resource_library_manifest(resources: Iterable[dict[str, str]]) -> dict[str, Any]:
    items = []
    for item in resources:
        if set(item) != {"id", "title", "language", "source_url", "rights"}:
            raise CommunitySafetyError("resource records require id/title/language/source_url/rights only")
        lang = item["language"]
        if not LANG_RE.fullmatch(lang):
            raise CommunitySafetyError("invalid BCP-47-like language tag")
        items.append({
            "id": _id(item["id"], "resource id"),
            "title": _text(item["title"], "title"),
            "language": lang,
            "source_url": _url(item["source_url"]),
            "rights": _text(item["rights"], "rights", 120),
        })
    return {
        "roadmap_id": "P-151",
        "resources": items,
        "content_downloaded": False,
        "redistribution_authorized": False,
    }


def scripture_source_manifest(source_id: str, title: str, source_url: str, license_name: str, language: str) -> dict[str, Any]:
    if not LANG_RE.fullmatch(language):
        raise CommunitySafetyError("invalid language tag")
    return {
        "roadmap_id": "P-152",
        "source_id": _id(source_id, "source_id"),
        "title": _text(title, "title"),
        "source_url": _url(source_url),
        "license": _text(license_name, "license", 120),
        "language": language,
        "scripture_text_copied": False,
        "search_index_built": False,
        "rights_review_required": True,
        "upstream_candidates": ["CrossWire SWORD", "STEPBible"],
    }


def bible_study_plan(topic: str, source_ids: Iterable[str], language: str = "en") -> dict[str, Any]:
    if not LANG_RE.fullmatch(language):
        raise CommunitySafetyError("invalid language tag")
    sources = sorted({_id(x, "source id") for x in source_ids})
    if not sources:
        raise CommunitySafetyError("at least one licensed source is required")
    return {
        "roadmap_id": "P-153",
        "topic": _text(topic, "topic", 200),
        "source_ids": sources,
        "language": language,
        "retrieval_performed": False,
        "translation_generated": False,
        "theological_authority_claim": False,
    }


def sermon_corpus_manifest(documents: Iterable[dict[str, str]]) -> dict[str, Any]:
    records = []
    for item in documents:
        if set(item) != {"document_id", "title", "rights", "sha256"}:
            raise CommunitySafetyError("sermon records require document_id/title/rights/sha256 only")
        digest = item["sha256"].lower()
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise CommunitySafetyError("invalid sha256")
        records.append({
            "document_id": _id(item["document_id"], "document_id"),
            "title": _text(item["title"], "title"),
            "rights": _text(item["rights"], "rights", 120),
            "sha256": digest,
        })
    return {
        "roadmap_id": "P-154",
        "documents": records,
        "content_embedded": False,
        "private_material_uploaded": False,
        "index_built": False,
    }


def language_study_dataset_manifest(dataset_id: str, source_url: str, license_name: str, fields: Iterable[str]) -> dict[str, Any]:
    clean_fields = sorted({_text(x, "field", 64) for x in fields})
    if not clean_fields:
        raise CommunitySafetyError("at least one field is required")
    fingerprint = hashlib.sha256((dataset_id + "|" + "|".join(clean_fields)).encode()).hexdigest()
    return {
        "roadmap_id": "P-155",
        "dataset_id": _id(dataset_id, "dataset_id"),
        "source_url": _url(source_url),
        "license": _text(license_name, "license", 120),
        "fields": clean_fields,
        "manifest_fingerprint": fingerprint,
        "dataset_downloaded": False,
        "linguistic_interpretation_generated": False,
        "upstream_candidate": "STEPBible Data",
    }
