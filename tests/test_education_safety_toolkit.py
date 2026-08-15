import pytest

from scripts.education_safety_toolkit import EducationError, evaluate


def test_tutor_is_corpus_grounded_plan_only():
    r=evaluate({"mode":"tutor","corpus_id":"course-v1","level":"beginner"})
    assert r["roadmap_id"]=="P-109" and set(r["execution"].values())=={False}
    assert "insufficient-evidence refusal" in r["requirements"]


def test_reading_assistant_preserves_source_and_no_profile():
    r=evaluate({"mode":"reading","support":"summary"})
    assert r["roadmap_id"]=="P-110" and r["execution"]["learner_profile_stored"] is False
    assert "source access" in r["preserve"]


def test_math_and_quiz_do_not_claim_generation_or_grading():
    m=evaluate({"mode":"math","domain":"algebra"})
    q=evaluate({"mode":"quiz","objective_ids":["obj-1","obj-2"],"question_count":5})
    assert m["roadmap_id"]=="P-111" and m["execution"]["problem_solved"] is False
    assert q["roadmap_id"]=="P-112" and q["execution"]["scores_stored"] is False


def test_curriculum_and_tiers_require_review_semantics():
    c=evaluate({"mode":"curriculum","subject":"digital-literacy","unit_count":8})
    t=evaluate({"mode":"tiers","concept_id":"git-commit"})
    assert c["roadmap_id"]=="P-113" and c["execution"]["curriculum_adopted"] is False
    assert t["roadmap_id"]=="P-114" and t["semantics"]["tier_equivalence_verified"] is False


def test_digital_literacy_and_browsing_never_touch_device():
    d=evaluate({"mode":"digital_literacy","module":"backups"})
    b=evaluate({"mode":"safe_browsing","scenario":"download"})
    assert d["roadmap_id"]=="P-115" and set(d["execution"].values())=={False}
    assert b["roadmap_id"]=="P-116" and set(b["execution"].values())=={False}


def test_phishing_training_is_static_and_collects_nothing():
    r=evaluate({"mode":"phishing_training","cue_ids":["urgency","domain-mismatch"]})
    assert r["roadmap_id"]=="P-117"
    assert set(r["execution"].values())=={False}
    assert "no credential collection" in r["safe_simulation_contract"]
    assert "no message sending" in r["safe_simulation_contract"]


def test_password_hygiene_never_requests_passwords():
    r=evaluate({"mode":"password_hygiene","password_manager_explained":True,"mfa_explained":True,"reuse_risk_explained":True})
    assert r["roadmap_id"]=="P-118" and set(r["privacy"].values())=={False}


def test_executable_docs_mutation_example_is_no_execution():
    r=evaluate({"mode":"executable_docs","language":"shell","example_mutates_state":True})
    assert r["roadmap_id"]=="P-120" and r["required_sandbox"]=="NO_EXECUTION"
    assert set(r["execution"].values())=={False}


def test_invalid_modes_and_inputs_fail_closed():
    with pytest.raises(EducationError): evaluate({"mode":"math","domain":"astrology"})
    with pytest.raises(EducationError): evaluate({"mode":"quiz","objective_ids":[],"question_count":1})
    with pytest.raises(EducationError): evaluate({"mode":"phishing_training","cue_ids":["bad cue with spaces"]})
    with pytest.raises(EducationError): evaluate({"mode":"unknown"})
