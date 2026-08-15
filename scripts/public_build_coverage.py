#!/usr/bin/env python3
"""Truthful source/reference coverage verifier for the DAIS 227-project portfolio.

The verifier proves only that each canonical opportunity ID is mapped to a
public proving-ground evidence tranche. It deliberately does NOT prove roadmap
completion, usability, release, acceptance, security, accessibility, licensing
or production readiness.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

EXPECTED_IDS = tuple(f"P-{i:03d}" for i in range(1, 228))
FOUNDATION_IDS = tuple(f"F-{i:02d}" for i in range(1, 7))


@dataclass(frozen=True)
class CoverageTranche:
    name: str
    ids: tuple[str, ...]
    evidence_paths: tuple[str, ...]


def ids(*parts: int | tuple[int, int]) -> tuple[str, ...]:
    values: list[str] = []
    for part in parts:
        if isinstance(part, int):
            values.append(f"P-{part:03d}")
        else:
            start, end = part
            values.extend(f"P-{i:03d}" for i in range(start, end + 1))
    return tuple(values)


TRANCHES = (
    CoverageTranche("beginner-tech-rescue", ids(1, 17, 18), ("scripts/beginner_tech_rescue.py", "docs/BEGINNER-TECH-RESCUE.md")),
    CoverageTranche("system-doctor", ids(2, 16), ("scripts/system_doctor.py", "docs/SYSTEM-DOCTOR-AND-ACCESSIBLE-AI.md")),
    CoverageTranche("system-support", ids((3, 10)), ("scripts/system_support_planner.py", "docs/SYSTEM-SUPPORT-PLANNER.md")),
    CoverageTranche("hardware-upgrade", ids((11, 15)), ("scripts/hardware_upgrade_advisor.py", "docs/HARDWARE-UPGRADE-BENCHMARK-ADVISOR.md")),
    CoverageTranche("install-config", ids(19, 20), ("scripts/install_config_planner.py", "docs/INSTALLATION-CONFIGURATION-PLANNER.md")),
    CoverageTranche("accelerator-readiness", ids((21, 24)), ("scripts/accelerator_readiness.py", "scripts/cuda_readiness.py")),
    CoverageTranche("vgm-proving-ground", ids(25), ("README.md", "docs/VERIFIED_SEQUENCE.md")),
    CoverageTranche("local-ai-ecosystem", ids((26, 38)), ("scripts/model_memory_estimator.py", "scripts/local_ai_setup_planner.py", "docs/LOCAL-CLOUD-OFFLINE-DECISION.md")),
    CoverageTranche("repository-quality", ids((39, 50)), ("scripts/repo_doctor.py", "scripts/repo_quality_integration_plan.py", "scripts/evidence_validate.py")),
    CoverageTranche("community-release-governance", ids((51, 63)), ("scripts/release_governance.py", "scripts/contributor_safety_tools.py", "scripts/community_maintenance_analysis.py")),
    CoverageTranche("model-dataset-ecosystem", ids((64, 76)), ("scripts/model_ecosystem_planner.py", "scripts/dataset_stewardship.py")),
    CoverageTranche("workspace-accessibility", ids((77, 86)), ("scripts/workspace_accessibility_planner.py", "docs/WORKSPACE-ACCESSIBILITY-PLANNER.md")),
    CoverageTranche("accessibility-inclusion", ids((87, 100)), ("scripts/accessibility_inclusion.py", "docs/ACCESSIBILITY-INCLUSION.md")),
    CoverageTranche("offline-low-bandwidth", ids((101, 108)), ("scripts/offline_access_planner.py", "docs/OFFLINE-LOW-BANDWIDTH.md")),
    CoverageTranche("education-digital-literacy", ids((109, 118), 120), ("scripts/education_safety_toolkit.py", "docs/EDUCATION-DIGITAL-LITERACY.md")),
    CoverageTranche("learning-git-external", ids(119), ("docs/DAIS-PUBLIC-BUILD-STATUS.md",)),
    CoverageTranche("cyber-privacy-trust", ids((121, 133)), ("scripts/cyber_privacy_trust.py", "docs/CYBERSECURITY-PRIVACY-TRUST.md")),
    CoverageTranche("health-medicine-emergency", ids((134, 147)), ("scripts/health_education_support.py", "docs/HEALTH-MEDICINE-EMERGENCY.md")),
    CoverageTranche("community-ministry-nonprofit", ids((148, 155)), ("scripts/community_ministry_nonprofit.py", "docs/COMMUNITY-MINISTRY-NONPROFIT.md")),
    CoverageTranche("agriculture-business-finance", ids((156, 172)), ("scripts/agriculture_business_finance.py", "docs/AGRICULTURE-BUSINESS-FINANCE.md")),
    CoverageTranche("travel-civic-public-info", ids((173, 182)), ("scripts/travel_civic_public_info.py", "docs/TRAVEL-CIVIC-PUBLIC-INFORMATION.md")),
    CoverageTranche("science-research-environment", ids((183, 194)), ("scripts/science_research_environment.py", "docs/SCIENCE-RESEARCH-ENVIRONMENT.md")),
    CoverageTranche("agent-memory-governance", ids((195, 210)), ("scripts/agent_memory_governance.py", "docs/AI-AGENT-MEMORY-GOVERNANCE.md")),
    CoverageTranche("infrastructure-fleet-evidence", ids((211, 227)), ("scripts/public_infrastructure_reference.py", "docs/INFRASTRUCTURE-FLEET-EVIDENCE.md")),
)

FOUNDATION_EVIDENCE = {
    "F-01": ("scripts/safefix_contract.py", "docs/PUBLIC-BUILD-FOUNDATIONS.md"),
    "F-02": ("scripts/system_doctor.py", "docs/SYSTEM-DOCTOR-AND-ACCESSIBLE-AI.md"),
    "F-03": ("scripts/local_ai_readiness.py", "docs/LOCAL-AI-MODEL-FIT.md"),
    "F-04": ("schemas/hardware-compatibility-report-v0.1.schema.json", "docs/COMPATIBILITY.md"),
    "F-05": ("schemas/universal-evidence-v0.1.schema.json", "scripts/evidence_interoperability.py"),
    "F-06": ("scripts/accessible_report.py", "docs/ACCESSIBILITY-INCLUSION.md"),
}


def flattened_ids(tranches: Iterable[CoverageTranche] = TRANCHES) -> list[str]:
    return [project_id for tranche in tranches for project_id in tranche.ids]


def audit(root: Path = Path(".")) -> dict[str, object]:
    actual = flattened_ids()
    duplicates = sorted({x for x in actual if actual.count(x) > 1})
    missing = sorted(set(EXPECTED_IDS) - set(actual))
    unexpected = sorted(set(actual) - set(EXPECTED_IDS))
    missing_paths: list[str] = []
    for tranche in TRANCHES:
        for rel in tranche.evidence_paths:
            if not (root / rel).is_file():
                missing_paths.append(f"{tranche.name}:{rel}")
    for foundation_id, paths in FOUNDATION_EVIDENCE.items():
        for rel in paths:
            if not (root / rel).is_file():
                missing_paths.append(f"{foundation_id}:{rel}")

    complete = not duplicates and not missing and not unexpected and not missing_paths
    return {
        "schema_version": "0.1",
        "claim": "PUBLIC_SOURCE_REFERENCE_COVERAGE_ONLY",
        "expected_opportunities": len(EXPECTED_IDS),
        "mapped_opportunities": len(set(actual) & set(EXPECTED_IDS)),
        "expected_foundations": len(FOUNDATION_IDS),
        "mapped_foundations": len(FOUNDATION_EVIDENCE),
        "duplicates": duplicates,
        "missing_ids": missing,
        "unexpected_ids": unexpected,
        "missing_evidence_paths": sorted(missing_paths),
        "coverage_gate": "PASS" if complete else "FAIL",
        "roadmap_complete_count": 0,
        "roadmap_completion_proven": False,
        "release_proven": False,
        "real_world_acceptance_proven": False,
    }


def main() -> int:
    import json
    report = audit()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["coverage_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
