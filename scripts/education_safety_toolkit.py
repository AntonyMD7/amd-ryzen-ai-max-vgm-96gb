#!/usr/bin/env python3
"""Content-light education/digital-literacy planning primitives.

No student data, browsing history, credentials, messages or executable lesson
content are collected. Outputs are reviewable manifests/checklists only.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any


class EducationError(ValueError):
    pass


SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/+:-]{0,127}$")


def _id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not SAFE.fullmatch(value):
        raise EducationError(f"{name} must be a bounded identifier")
    return value


def _bool(value: Any, name: str) -> bool:
    if not isinstance(value, bool):
        raise EducationError(f"{name} must be boolean")
    return value


def tutor_plan(data: dict[str, Any]) -> dict[str, Any]:
    corpus_id = _id(data.get("corpus_id"), "corpus_id")
    level = data.get("level")
    if level not in {"beginner", "intermediate", "advanced"}:
        raise EducationError("level must be beginner/intermediate/advanced")
    return {
        "schema_version":"0.1","roadmap_id":"P-109","corpus_id":corpus_id,"level":level,
        "requirements":["authorized corpus", "citations", "state uncertainty", "insufficient-evidence refusal", "separate assessment from grading authority", "learner privacy"],
        "execution":{"learner_data_read":False,"model_called":False,"grade_recorded":False},
        "semantics":{"answer_accuracy_certified":False}
    }


def reading_plan(data: dict[str, Any]) -> dict[str, Any]:
    support = data.get("support")
    if support not in {"define_terms", "chunk_text", "questions", "summary", "read_aloud_plan"}:
        raise EducationError("unsupported reading support")
    return {
        "schema_version":"0.1","roadmap_id":"P-110","support":support,
        "preserve":["source access", "names", "dates", "numbers", "citations", "warnings", "uncertainty"],
        "requirements":["user-controlled difficulty", "do not replace source", "avoid hidden comprehension scoring"],
        "execution":{"source_text_read":False,"speech_generated":False,"learner_profile_stored":False}
    }


def math_explanation(data: dict[str, Any]) -> dict[str, Any]:
    domain = data.get("domain")
    if domain not in {"arithmetic", "algebra", "geometry", "statistics", "calculus"}:
        raise EducationError("unsupported domain")
    return {
        "schema_version":"0.1","roadmap_id":"P-111","domain":domain,
        "requirements":["show steps", "name assumptions", "offer verification", "separate exact arithmetic from heuristic explanation", "do not fabricate theorem/source"],
        "execution":{"problem_solved":False,"calculator_called":False},
        "semantics":{"mathematical_correctness_certified":False}
    }


def quiz_builder(data: dict[str, Any]) -> dict[str, Any]:
    objectives = data.get("objective_ids")
    if not isinstance(objectives, list) or not objectives or len(objectives) > 100:
        raise EducationError("objective_ids must be a bounded non-empty list")
    ids = [_id(x,"objective_id") for x in objectives]
    count = data.get("question_count")
    if isinstance(count,bool) or not isinstance(count,int) or count < 1 or count > 100:
        raise EducationError("question_count must be 1..100")
    return {
        "schema_version":"0.1","roadmap_id":"P-112","objective_ids":ids,"question_count":count,
        "requirements":["map every item to objective", "review answer key", "avoid sensitive learner profiling", "include rationale", "support accessible formats"],
        "execution":{"questions_generated":False,"assessment_published":False,"scores_stored":False}
    }


def curriculum_plan(data: dict[str, Any]) -> dict[str, Any]:
    subject = _id(data.get("subject"),"subject")
    unit_count = data.get("unit_count")
    if isinstance(unit_count,bool) or not isinstance(unit_count,int) or not 1 <= unit_count <= 100:
        raise EducationError("unit_count must be 1..100")
    return {
        "schema_version":"0.1","roadmap_id":"P-113","subject":subject,"unit_count":unit_count,
        "requirements":["learning objectives", "prerequisites", "assessment alignment", "source provenance", "accessibility", "local context review", "teacher/human review"],
        "execution":{"curriculum_generated":False,"curriculum_adopted":False}
    }


def explanation_tiers(data: dict[str, Any]) -> dict[str, Any]:
    concept_id = _id(data.get("concept_id"),"concept_id")
    return {
        "schema_version":"0.1","roadmap_id":"P-114","concept_id":concept_id,
        "tiers":{
            "beginner":["plain language","one concept at a time","safe example"],
            "intermediate":["mechanism","tradeoffs","alternatives","common failure modes"],
            "expert":["assumptions","formal terms","evidence/provenance","edge cases","reproducibility"]},
        "semantics":{"explanation_generated":False,"tier_equivalence_verified":False}
    }


def digital_literacy(data: dict[str, Any]) -> dict[str, Any]:
    module = data.get("module")
    modules = {"files","browser","email","accounts","updates","backups","privacy","ai_basics"}
    if module not in modules:
        raise EducationError("unsupported digital literacy module")
    return {
        "schema_version":"0.1","roadmap_id":"P-115","module":module,
        "requirements":["learning-by-doing", "safe sandbox or screenshots", "plain language", "recovery steps", "no shame framing", "accessible alternatives"],
        "execution":{"device_changed":False,"account_accessed":False}
    }


def safe_browsing(data: dict[str, Any]) -> dict[str, Any]:
    scenario = data.get("scenario")
    if scenario not in {"url", "download", "permission_prompt", "login_page", "public_wifi", "browser_update"}:
        raise EducationError("unsupported safe browsing scenario")
    return {
        "schema_version":"0.1","roadmap_id":"P-116","scenario":scenario,
        "teach":["verify source", "notice domain/context", "avoid unnecessary permissions", "keep software updated", "use recovery/reporting path"],
        "execution":{"url_opened":False,"download_started":False,"credential_requested":False}
    }


def phishing_training(data: dict[str, Any]) -> dict[str, Any]:
    cues = data.get("cue_ids")
    if not isinstance(cues,list) or len(cues)>50:
        raise EducationError("cue_ids must be a bounded list")
    cues = [_id(x,"cue_id") for x in cues]
    return {
        "schema_version":"0.1","roadmap_id":"P-117","cue_ids":cues,
        "safe_simulation_contract":["local/static examples only", "no credential collection", "no message sending", "no deceptive external domains", "debrief immediately", "reporting practice"],
        "execution":{"email_sent":False,"credential_collected":False,"external_domain_registered":False,"tracking_pixel_used":False}
    }


def password_hygiene(data: dict[str, Any]) -> dict[str, Any]:
    supports_manager = _bool(data.get("password_manager_explained"),"password_manager_explained")
    supports_mfa = _bool(data.get("mfa_explained"),"mfa_explained")
    reuse = _bool(data.get("reuse_risk_explained"),"reuse_risk_explained")
    return {
        "schema_version":"0.1","roadmap_id":"P-118",
        "checks":{"password_manager_explained":supports_manager,"mfa_explained":supports_mfa,"reuse_risk_explained":reuse},
        "status":"EDUCATION_GAPS" if not all((supports_manager,supports_mfa,reuse)) else "CHECKLIST_PASSES",
        "privacy":{"password_value_requested":False,"password_hash_requested":False,"account_identifier_requested":False}
    }


def executable_docs(data: dict[str, Any]) -> dict[str, Any]:
    language = data.get("language")
    if language not in {"python", "shell", "javascript", "none"}:
        raise EducationError("unsupported language")
    mutating = _bool(data.get("example_mutates_state"),"example_mutates_state")
    return {
        "schema_version":"0.1","roadmap_id":"P-120","language":language,"example_mutates_state":mutating,
        "required_sandbox":"NO_EXECUTION" if mutating else "EPHEMERAL_NO_SECRETS_NO_NETWORK_BY_DEFAULT",
        "requirements":["pinned dependencies", "deterministic fixture", "expected output", "timeout", "resource cap", "no secrets", "cleanup", "copy-paste risk warning"],
        "execution":{"example_executed":False,"filesystem_changed":False,"network_used":False}
    }


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    fn={
        "tutor":tutor_plan,"reading":reading_plan,"math":math_explanation,"quiz":quiz_builder,
        "curriculum":curriculum_plan,"tiers":explanation_tiers,"digital_literacy":digital_literacy,
        "safe_browsing":safe_browsing,"phishing_training":phishing_training,"password_hygiene":password_hygiene,
        "executable_docs":executable_docs,
    }.get(data.get("mode"))
    if fn is None:
        raise EducationError("unsupported mode")
    return fn(data)


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("request"); a=p.parse_args()
    with open(a.request,encoding="utf-8") as h: data=json.load(h)
    print(json.dumps(evaluate(data),indent=2,sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
