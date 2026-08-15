import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_trust_policy import TrustPolicyError, evaluate, validate_profile  # noqa: E402


def load(name):
    return json.loads((ROOT / "examples" / name).read_text(encoding="utf-8"))


def profile():
    return load("evidence-trust-profile-synthetic-v0.1.json")


def observation():
    return load("evidence-trust-observation-synthetic-v0.1.json")


def test_matching_policy_satisfies_only_cryptographic_policy():
    result = evaluate(profile(), observation())
    assert result["policy_status"] == "POLICY_SATISFIED"
    assert result["cryptographic_policy_satisfied"] is True
    assert result["artifact_goodness_proven"] is False
    assert result["semantic_truth_proven"] is False
    assert result["slsa_level_proven"] is None
    assert result["verifier_observation_trusted_by_this_module"] is False
    assert result["network_contact_performed"] is False
    assert result["cryptography_performed"] is False
    assert result["artifact_execution_performed"] is False


def test_digest_mismatch_rejects():
    obs = observation()
    obs["artifact_sha256"] = "2" * 64
    result = evaluate(profile(), obs)
    assert result["policy_status"] == "POLICY_REJECTED"
    assert "artifact_digest_exact" in result["failed_checks"]


def test_exact_signer_identity_required():
    obs = observation()
    obs["certificate_identity"] = "other@example.invalid"
    result = evaluate(profile(), obs)
    assert "certificate_identity_exact" in result["failed_checks"]


def test_exact_oidc_issuer_required():
    obs = observation()
    obs["certificate_oidc_issuer"] = "https://other-issuer.example.invalid"
    result = evaluate(profile(), obs)
    assert "certificate_oidc_issuer_exact" in result["failed_checks"]


def test_required_transparency_fails_closed():
    obs = observation()
    obs["transparency_verified"] = False
    result = evaluate(profile(), obs)
    assert "transparency_requirement" in result["failed_checks"]


def test_required_timestamp_must_use_accepted_source():
    obs = observation()
    obs["timestamp_source"] = "NONE"
    result = evaluate(profile(), obs)
    assert "timestamp_requirement" in result["failed_checks"]


def test_builder_identity_and_provenance_both_required():
    obs = observation()
    obs["builder_id"] = "https://example.invalid/builders/other"
    result = evaluate(profile(), obs)
    assert "builder_identity_requirement" in result["failed_checks"]

    obs = observation()
    obs["provenance_verified"] = False
    result = evaluate(profile(), obs)
    assert "builder_identity_requirement" in result["failed_checks"]


def test_wildcard_signer_policy_is_rejected():
    p = profile()
    p["signer"]["exact_identity"] = "*@example.invalid"
    with pytest.raises(TrustPolicyError, match="exact"):
        validate_profile(p)


def test_policy_may_not_infer_goodness_or_truth():
    p = profile()
    p["claims"]["artifact_goodness_inferred"] = True
    with pytest.raises(TrustPolicyError, match="must not infer"):
        validate_profile(p)

    p = profile()
    p["claims"]["semantic_truth_inferred"] = True
    with pytest.raises(TrustPolicyError, match="must not infer"):
        validate_profile(p)


def test_evaluation_does_not_mutate_inputs():
    p = profile()
    obs = observation()
    p_before = copy.deepcopy(p)
    obs_before = copy.deepcopy(obs)
    evaluate(p, obs)
    assert p == p_before
    assert obs == obs_before
