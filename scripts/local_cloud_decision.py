#!/usr/bin/env python3
"""Constraint-first Local vs Cloud AI decision assistant.

This tool makes no provider, pricing, legal, compliance or performance claim. It
turns explicit user constraints into an architecture lane and a verification
checklist. Sensitive data defaults toward local-only unless the caller supplies a
separate approved-cloud policy outside this tool.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from typing import Any

VERSION = "0.1.0"
SENSITIVITY = ("public", "internal", "sensitive", "regulated")


@dataclass(frozen=True)
class Constraints:
    sensitivity: str
    offline_required: bool
    local_hardware_ready: bool
    remote_api_allowed: bool
    low_bandwidth: bool
    availability_priority: str


def decide(c: Constraints) -> dict[str, Any]:
    if c.sensitivity not in SENSITIVITY:
        raise ValueError("unknown sensitivity")
    if c.availability_priority not in {"normal", "high"}:
        raise ValueError("availability_priority must be normal or high")

    reasons: list[str] = []
    blockers: list[str] = []
    if c.offline_required:
        lane = "LOCAL_ONLY_REQUIRED"
        reasons.append("Offline operation was explicitly required.")
    elif c.sensitivity in {"sensitive", "regulated"} and not c.remote_api_allowed:
        lane = "LOCAL_ONLY_REQUIRED"
        reasons.append("The data class is sensitive/regulated and no remote API policy was approved.")
    elif not c.remote_api_allowed:
        lane = "LOCAL_PREFERRED"
        reasons.append("Remote APIs were not allowed by the supplied policy.")
    elif c.low_bandwidth:
        lane = "LOCAL_PREFERRED_WITH_OPTIONAL_CLOUD"
        reasons.append("Low/intermittent bandwidth favors local continuity when hardware can support the workload.")
    elif c.availability_priority == "high":
        lane = "HYBRID_CANDIDATE"
        reasons.append("High availability can benefit from independently verified local and remote fallback paths.")
    else:
        lane = "EVALUATE_LOCAL_AND_CLOUD"
        reasons.append("No supplied constraint forces either architecture.")

    if lane.startswith("LOCAL") and not c.local_hardware_ready:
        blockers.append("Local hardware/backend readiness is not yet verified for the intended workload.")
    if "CLOUD" in lane and not c.remote_api_allowed:
        blockers.append("Remote API use is not permitted by the supplied policy.")

    return {
        "schema_version": "0.1",
        "tool": {"name": "local_cloud_decision.py", "version": VERSION},
        "input": asdict(c),
        "recommended_lane": lane,
        "reasons": reasons,
        "blockers": blockers,
        "decision_scope": "ARCHITECTURE_PREFILTER_ONLY",
        "provider_selected": False,
        "guarantee": False,
        "required_next_checks": [
            "Classify the actual data and confirm organizational/legal policy before remote processing.",
            "Verify local model/backend capability with a pinned workload if local execution is proposed.",
            "Verify current provider terms, retention/training controls, region, security and pricing if cloud execution is proposed.",
            "Measure real latency, quality, availability and total cost using the intended workload before final selection.",
            "Design failure and offline behavior; a hybrid path must not silently send restricted data to cloud fallback.",
        ],
        "safety": {
            "network_request_performed": False,
            "data_uploaded": False,
            "provider_contacted": False,
            "model_loaded": False,
            "configuration_changed": False,
        },
    }


def offline_starter_manifest(*, runtime: str, interface: str, document_rag: bool) -> dict[str, Any]:
    if runtime not in {"ollama", "localai", "llama.cpp", "other"}:
        raise ValueError("unsupported runtime label")
    if interface not in {"cli", "web", "api"}:
        raise ValueError("interface must be cli, web, or api")
    components = [
        {
            "role": "inference_runtime",
            "selection": runtime,
            "required_boundary": "bind locally/trusted interface only until exposure review",
        },
        {
            "role": "user_interface",
            "selection": interface,
            "required_boundary": "no cloud dependency required for core offline path",
        },
    ]
    if document_rag:
        components.append({
            "role": "document_rag",
            "selection": "adopt-or-wrap-existing-local-first-project",
            "required_boundary": "documents, embeddings and chats stay local unless explicitly approved otherwise",
        })
    return {
        "schema_version": "0.1",
        "tool": {"name": "local_cloud_decision.py", "version": VERSION, "mode": "MANIFEST_ONLY"},
        "profile": "PRIVATE_OFFLINE_STARTER",
        "components": components,
        "acceptance": [
            "Core prompt/response path works after external network access is unavailable.",
            "Runtime is bound only to the intended local/trusted interface.",
            "No cloud model/provider is configured as an automatic fallback for restricted data.",
            "Model/artifact provenance and license are recorded.",
            "A small pinned local workload is verified before usefulness/performance claims.",
            "Backup/recovery for user documents and configuration is documented before relying on the system.",
        ],
        "privacy_review": [
            "Inspect update checks, telemetry, remote model catalogs and optional cloud connectors for the selected upstream products.",
            "Treat local/self-hosted as a deployment property that must be verified, not a marketing label.",
            "Do not publish document content, prompts, chats, credentials or host/network identity in evidence.",
        ],
        "mutation": {
            "software_installed": False,
            "firewall_changed": False,
            "network_exposure_changed": False,
            "model_downloaded": False,
            "service_started": False,
        },
        "status": "PLAN_ONLY_NOT_DEPLOYED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Constraint-first Local vs Cloud AI architecture assistant")
    sub = parser.add_subparsers(dest="mode", required=True)

    decision = sub.add_parser("decide")
    decision.add_argument("--sensitivity", choices=SENSITIVITY, default="internal")
    decision.add_argument("--offline-required", action="store_true")
    decision.add_argument("--local-hardware-ready", action="store_true")
    decision.add_argument("--remote-api-allowed", action="store_true")
    decision.add_argument("--low-bandwidth", action="store_true")
    decision.add_argument("--availability-priority", choices=("normal", "high"), default="normal")

    starter = sub.add_parser("offline-starter")
    starter.add_argument("--runtime", choices=("ollama", "localai", "llama.cpp", "other"), default="ollama")
    starter.add_argument("--interface", choices=("cli", "web", "api"), default="cli")
    starter.add_argument("--document-rag", action="store_true")

    args = parser.parse_args()
    if args.mode == "decide":
        result = decide(Constraints(
            sensitivity=args.sensitivity,
            offline_required=args.offline_required,
            local_hardware_ready=args.local_hardware_ready,
            remote_api_allowed=args.remote_api_allowed,
            low_bandwidth=args.low_bandwidth,
            availability_priority=args.availability_priority,
        ))
    else:
        result = offline_starter_manifest(runtime=args.runtime, interface=args.interface, document_rag=args.document_rag)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
