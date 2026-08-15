#!/usr/bin/env python3
"""Validate a narrow SLSA Provenance v1 statement against exact expected values.

This is not a general SLSA conformance checker and does not establish a SLSA
Build level. It validates the statement semantics needed by the DAIS Universal
Evidence acceptance workflow after a separate cryptographic verifier has
verified the signed in-toto statement.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_SHA = re.compile(r"^[0-9a-f]{40,64}$")
STATEMENT_V1 = "https://in-toto.io/Statement/v1"
SLSA_PROVENANCE_V1 = "https://slsa.dev/provenance/v1"


class ProvenancePolicyError(ValueError):
    pass


def _dict(value: object, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProvenancePolicyError(f"{field} must be an object")
    return value


def _text(value: object, field: str, max_len: int = 1000) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > max_len:
        raise ProvenancePolicyError(f"{field} must be a non-empty bounded string")
    return value.strip()


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return _dict(data, str(path))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(
    statement: dict[str, Any],
    *,
    artifact_name: str,
    artifact_sha256: str,
    expected_build_type: str,
    expected_builder_id: str,
    expected_source_repository: str,
    expected_source_commit: str,
    expected_workflow_ref: str,
) -> dict[str, Any]:
    if not SHA256.fullmatch(artifact_sha256):
        raise ProvenancePolicyError("expected artifact SHA-256 must be lowercase hexadecimal")
    if not GIT_SHA.fullmatch(expected_source_commit):
        raise ProvenancePolicyError("expected source commit must be a 40-64 character lowercase hexadecimal digest")

    checks: dict[str, bool] = {}
    checks["statement_type_exact"] = statement.get("_type") == STATEMENT_V1
    checks["predicate_type_exact"] = statement.get("predicateType") == SLSA_PROVENANCE_V1

    subjects = statement.get("subject")
    checks["single_subject"] = isinstance(subjects, list) and len(subjects) == 1
    if checks["single_subject"]:
        subject = _dict(subjects[0], "subject[0]")
        checks["subject_name_exact"] = subject.get("name") == artifact_name
        digest = _dict(subject.get("digest"), "subject[0].digest")
        checks["subject_sha256_exact"] = digest.get("sha256") == artifact_sha256 and set(digest) == {"sha256"}
    else:
        checks["subject_name_exact"] = False
        checks["subject_sha256_exact"] = False

    predicate = _dict(statement.get("predicate"), "predicate")
    build_definition = _dict(predicate.get("buildDefinition"), "predicate.buildDefinition")
    run_details = _dict(predicate.get("runDetails"), "predicate.runDetails")

    checks["build_type_exact"] = build_definition.get("buildType") == expected_build_type
    external = _dict(build_definition.get("externalParameters"), "predicate.buildDefinition.externalParameters")
    expected_external = {
        "sourceRepository": expected_source_repository,
        "sourceCommit": expected_source_commit,
        "workflowRef": expected_workflow_ref,
    }
    checks["external_parameters_exact"] = external == expected_external

    dependencies = build_definition.get("resolvedDependencies")
    expected_dependency_uri = f"git+{expected_source_repository}@{expected_source_commit}"
    checks["single_resolved_dependency"] = isinstance(dependencies, list) and len(dependencies) == 1
    if checks["single_resolved_dependency"]:
        dep = _dict(dependencies[0], "predicate.buildDefinition.resolvedDependencies[0]")
        dep_digest = _dict(dep.get("digest"), "predicate.buildDefinition.resolvedDependencies[0].digest")
        checks["source_dependency_exact"] = (
            dep.get("uri") == expected_dependency_uri
            and dep_digest == {"gitCommit": expected_source_commit}
            and set(dep) == {"uri", "digest"}
        )
    else:
        checks["source_dependency_exact"] = False

    builder = _dict(run_details.get("builder"), "predicate.runDetails.builder")
    builder_id = builder.get("id")
    checks["builder_id_exact"] = builder_id == expected_builder_id

    metadata = _dict(run_details.get("metadata"), "predicate.runDetails.metadata")
    invocation_id = metadata.get("invocationId")
    checks["invocation_id_present"] = isinstance(invocation_id, str) and invocation_id.startswith("https://github.com/")

    failed = sorted(name for name, value in checks.items() if value is not True)
    verified = not failed
    return {
        "schema_version": "0.1",
        "statement_type": statement.get("_type"),
        "predicate_type": statement.get("predicateType"),
        "artifact_name": artifact_name,
        "artifact_sha256": artifact_sha256,
        "builder_id": builder_id if isinstance(builder_id, str) else None,
        "build_type": build_definition.get("buildType"),
        "source_repository": expected_source_repository,
        "source_commit": expected_source_commit,
        "workflow_ref": expected_workflow_ref,
        "checks": checks,
        "failed_checks": failed,
        "provenance_semantics_verified": verified,
        "slsa_conformance_verified": False,
        "slsa_build_level_proven": None,
        "builder_security_assessed": False,
        "cryptography_performed": False,
        "network_contact_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("statement", type=Path)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--artifact-name", required=True)
    parser.add_argument("--build-type", required=True)
    parser.add_argument("--builder-id", required=True)
    parser.add_argument("--source-repository", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--workflow-ref", required=True)
    args = parser.parse_args(argv)

    result = evaluate(
        _load(args.statement),
        artifact_name=_text(args.artifact_name, "artifact-name"),
        artifact_sha256=_sha256(args.artifact),
        expected_build_type=_text(args.build_type, "build-type"),
        expected_builder_id=_text(args.builder_id, "builder-id"),
        expected_source_repository=_text(args.source_repository, "source-repository"),
        expected_source_commit=_text(args.source_commit, "source-commit"),
        expected_workflow_ref=_text(args.workflow_ref, "workflow-ref"),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["provenance_semantics_verified"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
