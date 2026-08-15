#!/usr/bin/env python3
"""Plain-language error explainer v0.1.

Maps common technical error *patterns* to cautious explanations and read-only next
checks. It does not upload logs, execute repairs, read files, or claim root cause.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any

VERSION = "0.1.0"

PATTERNS: list[dict[str, Any]] = [
    {
        "id": "command-not-found",
        "regex": re.compile(r"(?i)(command not found|is not recognized as an internal or external command|not found: [^\s]+)"),
        "plain": "The shell could not find the command you asked it to run.",
        "causes": ["The program may not be installed.", "The program may be installed but not on PATH.", "The command name may be misspelled."],
        "checks": ["Check the command spelling.", "Use the operating system's command-discovery tool to see whether the executable is available.", "Check the official installation documentation before installing anything."],
    },
    {
        "id": "permission-denied",
        "regex": re.compile(r"(?i)(permission denied|access is denied|unauthorized|operation not permitted)"),
        "plain": "The requested operation was refused by an authorization or permission boundary.",
        "causes": ["The current account may lack access.", "The file/service may intentionally be protected.", "Authentication may be missing or expired."],
        "checks": ["Confirm what resource the operation targeted.", "Inspect the documented permission requirement before elevating privileges.", "Avoid bypassing the protection until the expected access model is understood."],
    },
    {
        "id": "connection-refused",
        "regex": re.compile(r"(?i)(connection refused|actively refused it|ECONNREFUSED)"),
        "plain": "A network path reached a host/address, but the requested service did not accept the connection.",
        "causes": ["The service may not be running.", "It may be listening on a different address or port.", "A local/network policy may be rejecting the connection."],
        "checks": ["Verify the intended host and port without changing them.", "Check the service's documented health/status surface.", "Inspect listening endpoints and firewall/policy state using read-only tools."],
    },
    {
        "id": "dns-resolution",
        "regex": re.compile(r"(?i)(could not resolve host|name or service not known|temporary failure in name resolution|ENOTFOUND|getaddrinfo failed)"),
        "plain": "The system could not translate a hostname into a network address.",
        "causes": ["The hostname may be misspelled.", "DNS service may be unavailable.", "The record may not exist or may not be reachable from this network."],
        "checks": ["Verify the hostname spelling.", "Use a read-only DNS lookup.", "Check whether other known hostnames resolve before changing network settings."],
    },
    {
        "id": "disk-full",
        "regex": re.compile(r"(?i)(no space left on device|disk full|not enough space|ENOSPC)"),
        "plain": "The system reports that the relevant storage area does not have enough free capacity for the operation.",
        "causes": ["The filesystem may be full.", "A quota may have been reached.", "A temporary/cache area may be full even if another drive has space."],
        "checks": ["Measure free space on the filesystem that contains the target.", "Check quotas if the platform uses them.", "Do not delete data automatically; identify safe cleanup candidates first."],
    },
    {
        "id": "git-conflict",
        "regex": re.compile(r"(?i)(merge conflict|CONFLICT \(|you have unmerged paths|fix conflicts and then commit)"),
        "plain": "Git needs a human decision because two histories changed overlapping content in incompatible ways.",
        "causes": ["Both branches changed the same lines or nearby structure.", "A file was deleted on one side and edited on the other."],
        "checks": ["Run git status to list conflicted paths.", "Inspect each conflict before choosing content.", "Do not use destructive reset/checkout commands just to make the warning disappear."],
    },
    {
        "id": "authentication-failed",
        "regex": re.compile(r"(?i)(authentication failed|invalid credentials|credentials were not accepted|publickey|401 unauthorized|403 forbidden)"),
        "plain": "The remote service did not accept the presented authentication or authorization.",
        "causes": ["Credentials may be missing, expired, or for a different account.", "The identity may be valid but lack permission.", "The service may require a different authentication method."],
        "checks": ["Confirm the target service/account without displaying secret values.", "Check credential expiry/permission metadata where available.", "Follow the service's official authentication instructions; do not paste secrets into public logs or chats."],
    },
    {
        "id": "timeout",
        "regex": re.compile(r"(?i)(timed out|timeout|ETIMEDOUT|operation timed out)"),
        "plain": "The operation did not finish within the allowed time.",
        "causes": ["A service or network path may be slow or unavailable.", "The operation may legitimately require longer.", "A dependency may be waiting or stuck."],
        "checks": ["Identify which stage timed out.", "Check service/network health read-only before increasing timeouts.", "Retry only if the operation is known to be read-only or safely idempotent."],
    },
]

SECRET_PATTERN = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._~+/-]+=*|token[=:]\s*\S+|password[=:]\s*\S+|api[_-]?key[=:]\s*\S+)")


def explain_error(message: str) -> dict[str, Any]:
    scrubbed = SECRET_PATTERN.sub("[REDACTED_SECRET_LIKE_VALUE]", message.strip())
    matches = [item for item in PATTERNS if item["regex"].search(scrubbed)]
    if not matches:
        return {
            "schema_version": "0.1",
            "tool": {"name": "error_message_explainer.py", "version": VERSION, "mode": "NON_EXECUTING"},
            "classification": "UNKNOWN",
            "plain_language": "This error is not in the local explanation catalog.",
            "possible_causes": [],
            "safe_next_checks": ["Preserve the exact sanitized error text.", "Identify which program/version produced it.", "Consult authoritative documentation for that program before changing the system."],
            "sanitized_input": scrubbed[:4000],
            "limitations": ["No root cause has been proven.", "No repair was attempted."],
        }

    item = matches[0]
    return {
        "schema_version": "0.1",
        "tool": {"name": "error_message_explainer.py", "version": VERSION, "mode": "NON_EXECUTING"},
        "classification": item["id"],
        "plain_language": item["plain"],
        "possible_causes": item["causes"],
        "safe_next_checks": item["checks"],
        "sanitized_input": scrubbed[:4000],
        "limitations": [
            "Pattern matching suggests a category; it does not prove the root cause.",
            "Context, software version, operating system, network policy and prior actions can change interpretation.",
            "No repair was attempted.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Explain a common technical error without attempting a repair")
    parser.add_argument("message")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = explain_error(args.message)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["plain_language"])
        for check in report["safe_next_checks"]:
            print(f"- {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
